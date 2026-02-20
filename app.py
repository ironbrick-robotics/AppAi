import streamlit as st
from openai import OpenAI
import datetime
import requests
import re

# --- ΡΥΘΜΙΣΕΙΣ ΕΡΕΥΝΑΣ ---
st.set_page_config(page_title="ironbrick IDE | Plus V2", layout="wide")

# CSS για καθαρό interface
st.markdown("<style>header {visibility: hidden;} .stExpander { border: 2px solid #00a0dc; border-radius: 8px; }</style>", unsafe_allow_html=True)

# Σύνδεση με Groq - Διόρθωση στο Client Initialization
try:
    # Σιγουρευόμαστε ότι το API KEY υπάρχει
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1", 
            api_key=st.secrets["GROQ_API_KEY"]
        )
    else:
        st.error("Το GROQ_API_KEY λείπει από τα Secrets!")
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Σφάλμα Ρύθμισης: {e}")

# --- RESEARCH LOGIC (ΚΑΤΑΤΑΞΗ) ---
MY_CODING_LOGIC = (
    "Analyze the student's prompt and categorize it into ONE level only: "
    "L1: Simple natural language, L2: Parameters/Values, L3: Logic/Loops, "
    "L4: Technical Terminology, L5: Debugging. "
    "Return only the label (e.g., L3)."
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_output" not in st.session_state:
    st.session_state.last_output = ""

tab_ide, tab_logs = st.tabs(["💻 IDE", "📊 Data Access"])

with tab_ide:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🗑️ Νέα Συνομιλία (Reset)"):
            st.session_state.chat_history = []
            st.session_state.last_output = ""
            st.rerun()

        with st.form("input_form"):
            student_id = st.text_input("Κωδικός Μαθητή:", "S01")
            mode = st.radio("Ενέργεια:", ["Νέα Εντολή", "Διορθωση εντολής"], horizontal=True)
            user_input = st.text_area("Περιγράψτε την αποστολή (Maqueen Plus V2):", height=150)
            btn = st.form_submit_button("Παραγωγή Κώδικα")

    with col2:
        if btn and user_input:
            if mode == "Νέα Εντολή":
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner('Σύνδεση με τον AI Researcher...'):
                try:
                    # 1. Ερευνητική Κατάταξη
                    analysis = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
                    )
                    current_level = analysis.choices[0].message.content.strip()

                    # 2. Παραγωγή Κώδικα V2 PLUS
                    plus_v2_sys = (
                        "You are an expert MicroPython programmer for Maqueen Plus V2. "
                        "Rule 1: Use ONLY 'import maqueenPlusV2' and 'from microbit import *'. "
                        "Rule 2: Use EXACT syntax: maqueenPlusV2.control_motor(maqueenPlusV2.MyEnumMotor.ALL_MOTOR, maqueenPlusV2.MyEnumDir.FORWARD, 100). "
                        "Rule 3: NO markdown, NO comments, NO explanations. Pure code only."
                    )
                    
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": plus_v2_sys}] + st.session_state.chat_history
                    )
                    
                    raw_code = code_res.choices[0].message.content.strip()
                    clean_code = re.sub(r'```[a-z]*', '', raw_code).replace('```', '').strip()
                    
                    st.session_state.last_output = clean_code
                    st.markdown(f"**Επίπεδο Μάθησης: {current_level}**")
                    st.code(clean_code, language='python')

                    # 3. Αποθήκευση Δεδομένων
                    if DB_URL:
                        log_entry = {
                            "data": [{
                                "Timestamp": str(datetime.datetime.now()),
                                "Student_ID": student_id,
                                "Action": mode,
                                "Coding_Level": current_level,
                                "Prompt": user_input,
                                "Code": clean_code.replace('"', "'")
                            }]
                        }
                        requests.post(DB_URL, json=log_entry)
                
                except Exception as e:
                    st.error(f"Σφάλμα Σύνδεσης: {e}. Βεβαιωθείτε ότι το API Key είναι σωστό.")

    if st.session_state.last_output:
        with st.expander("💡 Πώς λειτουργεί ο κώδικας;"):
            try:
                exp_sys = "Είσαι καθηγητής. Εξήγησε τον κώδικα Maqueen Plus V2 στα Ελληνικά σύντομα."
                explanation = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": exp_sys}, {"role": "user", "content": st.session_state.last_output}]
                )
                st.write(explanation.choices[0].message.content)
            except:
                st.write("Η επεξήγηση δεν είναι διαθέσιμη λόγω σφάλματος σύνδεσης.")
