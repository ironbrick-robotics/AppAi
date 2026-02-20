import streamlit as st
from openai import OpenAI
import datetime
import requests
import re

# --- ΡΥΘΜΙΣΕΙΣ ΕΡΕΥΝΑΣ ---
st.set_page_config(page_title="ironbrick IDE | V2 PLUS Recovery", layout="wide")

st.markdown("<style>header {visibility: hidden;} .stExpander { border: 2px solid #00a0dc; border-radius: 8px; }</style>", unsafe_allow_html=True)

try:
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Config Error: {e}")

MY_CODING_LOGIC = (
    "Categorize: L1: Natural, L2: Params, L3: Logic, L4: Tech, L5: Debug. Return label only."
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
            user_input = st.text_area("Περιγράψτε την αποστολή:", height=150)
            btn = st.form_submit_button("Εκτέλεση")

    with col2:
        if btn and user_input:
            if mode == "Νέα Εντολή":
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner('Σύνταξη επίσημου κώδικα...'):
                try:
                    # 1. Ερευνητική Κατάταξη
                    analysis = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
                    )
                    current_level = analysis.choices[0].message.content.strip()

                    # 2. ΑΥΣΤΗΡΟ ΠΡΩΤΟΚΟΛΛΟ MAQUEEN PLUS V2
                    # Προσθήκη "Gold Standard" παραδειγμάτων για να μην παρεκκλίνει το AI
                    official_v2_sys = (
                        "You are a code generator for micro:bit Maqueen Plus V2. "
                        "CRITICAL: You must use the exact library name 'maqueenPlusV2'.\n"
                        "MANDATORY HEADER:\n"
                        "from microbit import *\n"
                        "import maqueenPlusV2\n\n"
                        "COMMAND TEMPLATES:\n"
                        "- Forward: maqueenPlusV2.control_motor(maqueenPlusV2.MyEnumMotor.ALL_MOTOR, maqueenPlusV2.MyEnumDir.FORWARD, 100)\n"
                        "- Stop: maqueenPlusV2.control_motor(maqueenPlusV2.MyEnumMotor.ALL_MOTOR, maqueenPlusV2.MyEnumDir.FORWARD, 0)\n"
                        "- RGB: maqueenPlusV2.set_rgb_light(maqueenPlusV2.MyEnumRgbLight.R_RGB, maqueenPlusV2.MyEnumColor.RED)\n\n"
                        "STRICT RULES: No markdown. No comments. No explanations. Only executable code."
                    )
                    
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": official_v2_sys}] + st.session_state.chat_history
                    )
                    
                    raw_code = code_res.choices[0].message.content.strip()
                    # Καθαρισμός από Markdown και κείμενο
                    clean_code = re.sub(r'```[a-z]*', '', raw_code).replace('```', '').strip()
                    # Αφαίρεση τυχόν κειμένου πριν το import
                    if "from" in clean_code:
                        clean_code = clean_code[clean_code.find("from"):]

                    st.session_state.last_output = clean_code
                    st.markdown(f"**Research Level: {current_level}**")
                    st.code(clean_code, language='python')

                    # 3. Logging
                    if DB_URL:
                        requests.post(DB_URL, json={"data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": student_id,
                            "Action": mode,
                            "Coding_Level": current_level,
                            "Prompt": user_input,
                            "Code": clean_code.replace('"', "'")
                        }]})
                
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.last_output:
        with st.expander("💡 Επεξήγηση"):
            exp_sys = "Είσαι καθηγητής. Εξήγησε τον κώδικα Maqueen Plus V2 στα Ελληνικά σύντομα."
            explanation = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": exp_sys}, {"role": "user", "content": st.session_state.last_output}]
            )
            st.write(explanation.choices[0].message.content)
