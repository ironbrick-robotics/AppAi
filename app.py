import streamlit as st
from openai import OpenAI
import datetime
import requests
import streamlit.components.v1 as components

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.0 | API Integrated", page_icon="🎓", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    .pub-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    iframe { border-radius: 10px; border: 1px solid #ccc; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets.")

# 3. Tabs
tab_info, tab_app, tab_data = st.tabs(["📖 Ταυτότητα", "🚀 App (MakeCode API)", "📂 Αρχεία"])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης (Ph.D. Candidate)")

with tab_app:
    st.header("🔬 AI Robotics Research Interface v8.0", anchor=False)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα:", ["MicroPython", "Arduino C"])
    with col_set2:
        action_type = st.radio("Ενέργεια:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Επεξεργασία μέσω API...'):
                try:
                    # System Prompt εστιασμένο μόνο σε καθαρό κώδικα
                    sys_prompt = "Είσαι ειδικός στο Micro:bit Maqueen. Δώσε ΜΟΝΟ τον κώδικα Python (MicroPython). Μην βάζεις XML ή κείμενο."

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    py_code = response.choices[0].message.content.replace("```python", "").replace("```", "").strip()
                    st.session_state.messages.append({"role": "assistant", "content": py_code})

                    # --- ΕΜΦΑΝΙΣΗ ΚΩΔΙΚΑ ---
                    st.markdown("#### 🐍 MicroPython Code")
                    st.code(py_code, language='python')
                    
                    # --- MAKECODE API RENDERING (IFRAME) ---
                    st.markdown("#### 🧩 Visual Blocks (MakeCode API)")
                    # Δημιουργία URL για το MakeCode Share/Embed
                    # Χρησιμοποιούμε το επίσημο portal για να δείξουμε τα blocks
                    makecode_url = "https://makecode.microbit.org/---embed?python=" + requests.utils.quote(py_code)
                    
                    components.iframe(makecode_url, height=500)
                    
                    # --- LOGGING ---
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": str(u_id),
                            "Action": str(action_type),
                            "Prompt": str(prompt),
                            "Answer": str(py_code)
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast("✅ Επιτυχής Καταγραφή!")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
