import streamlit as st
from openai import OpenAI
import datetime
import requests
import re

# --- ΡΥΘΜΙΣΕΙΣ ΕΡΕΥΝΑΣ ---
st.set_page_config(page_title="ironbrick IDE | Plus V2 Official", layout="wide")

st.markdown("<style>header {visibility: hidden;} .stExpander { border: 2px solid #00a0dc; border-radius: 8px; }</style>", unsafe_allow_html=True)

try:
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Configuration Error: {e}")

MY_CODING_LOGIC = (
    "Categorize student prompt: L1: Natural Language, L2: Parameters, L3: Logic/Loops, "
    "L4: Tech Terms (Huskylens/RGB), L5: Debugging. Return only level label."
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
            
            with st.spinner('Παραγωγή Επίσημου Κώδικα V2 PLUS...'):
                try:
                    # 1. Κατάταξη
                    analysis = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
                    )
                    current_level = analysis.choices[0].message.content.strip()

                    # 2. ΑΥΣΤΗΡΟ ΠΡΩΤΟΚΟΛΛΟ MAQUEEN PLUS V2
                    # Εδώ ορίζουμε τις επίσημες εντολές ως κανόνες
                    official_v2_sys = (
                        "You are a dedicated compiler for Maqueen Plus V2. "
                        "MANDATORY: Use ONLY the following syntax patterns. Do NOT invent methods.\n\n"
                        "1. Motors: maqueenPlusV2.control_motor(maqueenPlusV2.MyEnumMotor.LEFT_MOTOR, maqueenPlusV2.MyEnumDir.FORWARD, speed)\n"
                        "2. RGB: maqueenPlusV2.set_rgb_light(maqueenPlusV2.MyEnumRgbLight.R_RGB, maqueenPlusV2.MyEnumColor.RED)\n"
                        "3. Ultrasonic: maqueenPlusV2.read_ultrasonic(Pin.P13, Pin.P14)\n"
                        "4. Line Sensors: maqueenPlusV2.read_line_sensor(maqueenPlusV2.MyEnumLineSensor.L1)\n"
                        "Always start with: from microbit import * \nimport maqueenPlusV2\n\n"
                        "Strict Rule: NO markdown (```), NO chat, NO comments. ONLY THE CODE."
                    )
                    
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": official_v2_sys}] + st.session_state.chat_history
                    )
                    
                    raw_code = code_res.choices[0].message.content.strip()
                    clean_code = re.sub(r'```[a-z]*', '', raw_code).replace('```', '').strip()
                    
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
                    st.error(f"Connection Error: {e}")

    if st.session_state.last_output:
        with st.expander("💡 Επεξήγηση"):
            exp_sys = "Είσαι καθηγητής. Εξήγησε τον κώδικα Maqueen Plus V2 στα Ελληνικά σύντομα."
            explanation = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": exp_sys}, {"role": "user", "content": st.session_state.last_output}]
            )
            st.write(explanation.choices[0].message.content)
