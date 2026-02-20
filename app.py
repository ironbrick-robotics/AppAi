import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.9 | Research Edition", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ CLEAN RESEARCH UI ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stExpander { border: 2px solid #00a0dc; border-radius: 10px; background-color: #f0f9ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Σφάλμα σύνδεσης. Ελέγξτε τα Secrets.")

# 3. Tabs
tab_info, tab_app, tab_data = st.tabs(["📖 Ταυτότητα", "🚀 App (AI Tutor)", "📂 Δεδομένα"])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Μελέτη της αλληλεπίδρασης Μαθητή-ΤΝ στον Προγραμματισμό Ρομποτικών Συστημάτων")

with tab_app:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_py" not in st.session_state:
        st.session_state.last_py = ""

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            lang_choice = st.selectbox("Γλώσσα:", ["MicroPython", "Arduino C"])
            action_type = st.radio("Ενέργεια:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)
            prompt = st.text_area("Περιγράψτε τι θέλετε να κάνει το ρομπότ:", height=150)
            submit = st.form_submit_button("🚀 Παραγωγή Κώδικα")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Επεξεργασία...'):
                try:
                    # Αυστηρό prompt για παραγωγή μόνο κώδικα
                    sys_prompt = "Είσαι ειδικός Maqueen. Δώσε ΜΟΝΟ τον κώδικα Python ή C. Μην συμπεριλάβεις κανένα άλλο κείμενο."
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    st.session_state.last_py = response.choices[0].message.content.replace("```python", "").replace("```cpp", "").replace("```", "").strip()
                    st.session_state.messages.append({"role": "assistant", "content": st.session_state.last_py})

                    st.markdown("#### 🐍 Παραγόμενος Κώδικας")
                    st.code(st.session_state.last_py, language='python' if lang_choice=="MicroPython" else 'cpp')
                    
                    # LOGGING ΓΙΑ ΤΟ ΑΡΘΡΟ
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": str(u_id),
                            "Action": str(action_type),
                            "Language": str(lang_choice),
                            "Prompt": str(prompt),
                            "Answer": str(st.session_state.last_py).replace('"', "'")
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast("✅ Καταγράφηκε!")
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

    # --- ΕΠΕΞΗΓΗΣΗ (Ανοίγει μόνο αν ζητηθεί) ---
    if st.session_state.last_py:
        st.write("---")
        with st.expander("💡 Χρειάζεσαι βοήθεια για να καταλάβεις τον κώδικα;"):
            with st.spinner('📚 Προετοιμασία επεξήγησης...'):
                explain_msg = [
                    {"role": "system", "content": "Είσαι καθηγητής. Εξήγησε τον κώδικα ΜΟΝΟ στα Ελληνικά, απλά και παραστατικά. Μην χρησιμοποιείς αγγλικά ή άλλες γλώσσες στην επεξήγηση."},
                    {"role": "user", "content": f"Εξήγησε αυτόν τον κώδικα:\n{st.session_state.last_py}"}
                ]
                exp_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=explain_msg)
                st.write(exp_res.choices[0].message.content)

with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
