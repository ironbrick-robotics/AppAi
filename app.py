import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.6 | PhD Master", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ ΤΗΝ ΠΛΗΡΗ ΕΠΑΝΑΦΟΡΑ ΤΟΥ SITE ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    .pub-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .official-btn {
        background-color: #00a0dc; color: white !important; padding: 25px;
        border-radius: 15px; text-align: center; display: block;
        text-decoration: none; font-weight: bold; font-size: 22px;
        margin-top: 20px; border: 3px solid #007bb5;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets (GROQ_API_KEY & GSHEET_URL).")

# 3. Tabs (Ταυτότητα, Πρόοδος, Δημοσιεύσεις, App, Αρχεία)
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (Stable)", "📂 Αρχεία"
])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης (Ph.D. Candidate)")

with tab_app:
    st.header("🔬 Official MakeCode Research Bridge", anchor=False)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Researcher_1")
            action_type = st.radio("Τύπος:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Δημιουργία")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Παραγωγή επίσημου κώδικα...'):
                try:
                    # System Prompt για καθαρό MicroPython
                    sys_prompt = "Είσαι ειδικός Maqueen. Δώσε ΜΟΝΟ τον κώδικα Python. Χωρίς XML, χωρίς σχόλια."
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    py_code = response.choices[0].message.content.replace("```python", "").replace("```", "").strip()
                    st.session_state.messages.append({"role": "assistant", "content": py_code})

                    st.markdown("#### 🐍 Generated Python Code")
                    st.code(py_code, language='python')
                    
                    # --- Η ΛΥΣΗ ΓΙΑ ΤΟ ΣΦΑΛΜΑ ΔΙΚΤΥΟΥ (URL Protocol) ---
                    # Χρήση του 'Magic Link' που ανοίγει τον κώδικα απευθείας στον Browser
                    magic_link = f"https://makecode.microbit.org/#pub:_python:{requests.utils.quote(py_code)}"
                    
                    st.markdown(f"""
                        <div style="padding:20px; border:1px solid #ddd; border-radius:10px; background:#fff;">
                        <p>✅ Ο κώδικας δημιουργήθηκε! Για να αποφύγετε σφάλματα δικτύου:</p>
                        <a href="{magic_link}" target="_blank" class="official-btn">
                            🚀 ΑΝΟΙΓΜΑ ΣΤΟ OFFICIAL MAKECODE
                        </a>
                        <p style='margin-top:10px; font-size:12px; color:gray;'>
                            *Το κουμπί ανοίγει τον αυθεντικό editor σε νέα καρτέλα για 100% σταθερότητα.
                        </p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # --- ΣΤΑΘΕΡΟ LOGGING (Fix για 'dict' error) ---
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": str(u_id),
                            "Action": str(action_type),
                            "Prompt": str(prompt),
                            "Answer": str(py_code).replace('"', "'")
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast("✅ Επιτυχής Καταγραφή!")

                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

with tab_data:
    st.header("Βάση Δεδομένων", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
