import streamlit as st
from openai import OpenAI
import datetime
import requests
import streamlit.components.v1 as components

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.5 | Ph.D. Official", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ ΤΗΝ ΤΑΥΤΟΤΗΤΑ ΤΟΥ SITE ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    .pub-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .action-btn {
        background-color: #00a0dc; color: white !important; padding: 15px 25px;
        border-radius: 8px; text-align: center; display: inline-block;
        text-decoration: none; font-weight: bold; font-size: 18px;
        margin: 10px 0; border: none; transition: 0.3s;
    }
    .action-btn:hover { background-color: #007bb5; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets (GROQ_API_KEY & GSHEET_URL).")

# 3. Δομή Tabs
tab_info, tab_app, tab_data = st.tabs(["📖 Ταυτότητα", "🚀 Official IDE Bridge", "📂 Αρχεία"])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης (Ph.D. Candidate)")

with tab_app:
    st.header("🔬 Official MakeCode Research Interface", anchor=False)
    
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
            with st.spinner('⏳ Παραγωγή επίσημου κώδικα...'):
                try:
                    # System Prompt για καθαρό κώδικα συμβατό με MakeCode Python
                    sys_prompt = "Είσαι ειδικός Maqueen. Δώσε ΜΟΝΟ τον κώδικα Python. Χρησιμοποίησε τη βιβλιοθήκη 'maqueen'. Χωρίς XML ή κείμενο."
                    
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    py_code = response.choices[0].message.content.replace("```python", "").replace("```", "").strip()
                    st.session_state.messages.append({"role": "assistant", "content": py_code})

                    # --- ΠΡΟΒΟΛΗ ΚΩΔΙΚΑ ---
                    st.markdown("#### 🐍 Generated Code")
                    st.code(py_code, language='python')
                    
                    # --- THE OFFICIAL SOLUTION (Link Injection) ---
                    st.markdown("#### 🧩 Official MakeCode Visualizer")
                    
                    # Δημιουργία URL που ανοίγει τον κώδικα απευθείας στον Editor (όπως στην εικόνα 6)
                    encoded_code = requests.utils.quote(py_code)
                    makecode_url = f"https://makecode.microbit.org/#pub:_python:{encoded_code}"
                    
                    st.markdown(f"""
                        <div style="background:#f0f9ff; padding:20px; border-radius:10px; border:1px solid #bae6fd;">
                            <p>🎯 Ο κώδικας είναι έτοιμος! Για να δείτε τα <b>Blocks</b> και τον <b>Simulator</b>:</p>
                            <a href="{makecode_url}" target="_blank" class="action-btn">
                                🚀 ΑΝΟΙΓΜΑ ΣΤΟ OFFICIAL MAKECODE
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # --- SAFE LOGGING (Fix για Screenshot 2 & 3) ---
                    # Μετατρέπουμε τα πάντα σε String για να αποφύγουμε το Dict error
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
                    st.toast("✅ Καταγράφηκε επιτυχώς!")

                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
