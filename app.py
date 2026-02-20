import streamlit as st
from openai import OpenAI
import datetime
import requests

# --- ΕΡΕΥΝΗΤΙΚΟ ΠΕΡΙΒΑΛΛΟΝ IRONBRICK ---
st.set_page_config(page_title="ironbrick Research IDE | Plus V2", layout="wide")

st.markdown("<style>header {visibility: hidden;} .stExpander { border: 2px solid #00a0dc; border-radius: 8px; }</style>", unsafe_allow_html=True)

try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("Connection Error: Check API Secrets.")

# --- RESEARCH LOGIC (ΚΑΤΑΤΑΞΗ) ---
MY_CODING_LOGIC = (
    "Analyze the student's prompt and categorize it: "
    "L1: Simple natural language, L2: Parameters/Values, L3: Logic/Loops, "
    "L4: Technical Terminology (Huskylens, RGB, etc), L5: Debugging. "
    "Return only the label (e.g., L1)."
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_output" not in st.session_state:
    st.session_state.last_output = ""

tab_ide, tab_logs = st.tabs(["💻 IDE", "📊 Data Access"])

with tab_ide:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🗑️ Καθαρισμός Ιστορικού"):
            st.session_state.chat_history = []
            st.session_state.last_output = ""
            st.rerun()

        with st.form("input_form"):
            student_id = st.text_input("Student Code:", "S01")
            # Εστίαση μόνο σε MicroPython για την ώρα για μέγιστη συμβατότητα
            lang_choice = "MicroPython (Maqueen Plus V2)"
            mode = st.radio("Τύπος Ενέργειας:", ["Νέα Συνομιλία", "Διορθωση εντολής"], horizontal=True)
            user_input = st.text_area("Περιγράψτε την αποστολή (Maqueen Plus V2):", height=150)
            btn = st.form_submit_button("Εκτέλεση")

    with col2:
        if btn and user_input:
            if mode == "Νέα Συνομιλία":
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner('Επεξεργασία κώδικα V2 PLUS...'):
                # 1. Κατάταξη
                analysis = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
                )
                current_level = analysis.choices[0].message.content.strip()

                # 2. ΠΑΡΑΓΩΓΗ ΚΩΔΙΚΑ ΜΕ ΒΑΣΗ ΤΟ ΠΡΟΤΥΠΟ PLUS V2
                plus_v2_sys = (
                    "You are an expert in micro:bit Maqueen Plus V2. "
                    "You MUST use the 'maqueenPlusV2' library syntax. "
                    "EXAMPLE SYNTAX TO FOLLOW:\n"
                    "maqueenPlusV2.control_motor(maqueenPlusV2.MyEnumMotor.ALL_MOTOR, maqueenPlusV2.MyEnumDir.FORWARD, 100)\n"
                    "maqueenPlusV2.set_rgb_light(maqueenPlusV2.MyEnumRgbLight.R_RGB, maqueenPlusV2.MyEnumColor.RED)\n"
                    "Include: 'import maqueenPlusV2' and 'from microbit import *' at the top. "
                    "Generate ONLY functional MicroPython code. No comments, no markdown blocks."
                )
                
                messages = [{"role": "system", "content": plus_v2_sys}] + st.session_state.chat_history
                code_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
                final_code = code_res.choices[0].message.content.strip().replace("```python", "").replace("```", "")
                
                st.session_state.last_output = final_code
                st.markdown(f"**Ερευνητική Κατάταξη: {current_level}**")
                st.code(final_code, language='python')

                # 3. Logging
                try:
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime
