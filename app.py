import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v9.6 | Research IDE", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ CLEAN INTERFACE ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stExpander { border: 1px solid #00a0dc; border-radius: 10px; background-color: #f0f9ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets (GROQ_API_KEY & GSHEET_URL).")

# 3. Δομή Tabs
tab_app, tab_info, tab_data = st.tabs(["🚀 Εργαστήριο", "📖 Ταυτότητα", "📂 Αρχεία"])

with tab_app:
    # Αρχικοποίηση Ιστορικού (Context)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_code" not in st.session_state:
        st.session_state.last_code = ""

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            lang_choice = st.selectbox("Γλώσσα:", ["MicroPython", "Arduino C"])
            action_type = st.radio("Τύπος Ενέργειας:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση")

    with col_out:
        if submit and prompt:
            # Προσθήκη στο ιστορικό για μνήμη
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner('⏳ Επεξεργασία...'):
                try:
                    # Αυστηρό System Prompt για αποφυγή γλωσσικών λαθών
                    sys_prompt = (
                        f"Είσαι ειδικός Maqueen. Δώσε ΜΟΝΟ τον καθαρό κώδικα {lang_choice}. "
                        "Μην χρησιμοποιείς Markdown blocks (```), μην δίνεις χαιρετισμούς ή σχόλια. "
                        "Απάντα ΜΟΝΟ με τις εντολές προγραμματισμού."
                    )
                    
                    # Σύνθεση μηνυμάτων με το ιστορικό
                    api_messages = [{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=api_messages
                    )
                    
                    # Καθαρισμός κώδικα
                    clean_code = response.choices[0].message.content.replace("```python", "").replace("```cpp", "").replace("```", "").strip()
                    st.session_state.last_code = clean_code
                    st.session_state.messages.append({"role": "assistant", "content": clean_code})

                    st.markdown(f"#### ⚙️ Κώδικας {lang_choice}")
                    st.code(clean_code, language='python' if lang_choice=="MicroPython" else 'cpp')
                    
                    # LOGGING ΣΤΟ GOOGLE SHEET
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": str(u_id),
                            "Action": str(action_type),
                            "Language": str(lang_choice),
                            "Prompt": str(prompt),
                            "Answer": str(clean_code).replace('"', "'")
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast("✅ Καταγράφηκε!")
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

    # --- ΕΠΕΞΗΓΗΣΗ ΚΩΔΙΚΑ (Αυστηρά Ελληνικά) ---
    if st.session_state.last_code:
        st.write("---")
        with st.expander("💡 Επεξήγηση Λειτουργίας (Καθηγητής)"):
            with st.spinner('📚 Ανάλυση...'):
                explain_msg = [
                    {"role": "system", "content": "Είσαι καθηγητής ρομποτικής. Εξήγησε τον κώδικα ΜΟΝΟ στα Ελληνικά. "
                                                 "Απαγορεύεται αυστηρά η χρήση οποιασδήποτε άλλης γλώσσας. "
                                                 "Μίλα απλά και παραστατικά στον μαθητή."},
                    {"role": "user", "content": f"Εξήγησε αυτόν τον κώδικα:\n{st.session_state.last_code}"}
                ]
                exp_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=explain_msg)
                st.write(exp_res.choices[0].message.content)

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Μελέτη αλληλεπίδρασης Μαθητή-ΤΝ στον προγραμματισμό Maqueen.")

with tab_data:
    st.link_button("📊 Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
