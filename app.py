import streamlit as st
from openai import OpenAI
import datetime
import requests
import re

# --- ΡΥΘΜΙΣΕΙΣ ΕΡΕΥΝΑΣ ---
st.set_page_config(page_title="ironbrick IDE | MicroPython v2 Official", layout="wide")

try:
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Config Error: {e}")

# --- ΕΠΙΣΗΜΟ DOCUMENTATION REFERENCE (v2-docs) ---
MICROBIT_V2_DOCS = """
Reference: https://microbit-micropython.readthedocs.io/en/v2-docs/
Core Principles:
1. Imports: Always 'from microbit import *'. For Maqueen: 'import maqueenPlusV2'.
2. Time: Use 'sleep(ms)' for delays (Official MicroPython v2).
3. Display: Use 'display.show(Image.HAPPY)' or 'display.scroll("text")'.
4. Sound: Use 'speaker.on()' and 'audio.play(Sound.GIGGLE)' or 'music.play(music.PYTHON)'.
5. Sensors: 
   - Logo: 'logo.is_touched()'
   - Sound: 'microphone.sound_level()'
6. Maqueen Plus V2 Specific (Wrapper Support):
   - maqueenPlusV2.control_motor(motor, direction, speed)
   - maqueenPlusV2.read_ultrasonic(P13, P14)
"""

MY_CODING_LOGIC = "Categorize: L1: Natural, L2: Params, L3: Logic, L4: Tech, L5: Debug. Return label only."

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
            user_input = st.text_area("Περιγράψτε την αποστολή (v2-docs compliant):", height=150)
            btn = st.form_submit_button("Εκτέλεση")

    with col2:
        if btn and user_input:
            if mode == "Νέα Εντολή":
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner('Σύνταξη βάσει MicroPython v2 Docs...'):
                try:
                    # 1. Κατάταξη
                    analysis = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
                    )
                    current_level = analysis.choices[0].message.content.strip()

                    # 2. Παραγωγή Κώδικα (Strict v2 Docs)
                    v2_sys_prompt = (
                        f"You are a MicroPython v2 expert for micro:bit and Maqueen Plus V2.\n"
                        f"STRICT REFERENCE: {MICROBIT_V2_DOCS}\n"
                        "DIRECTIONS:\n"
                        "- Use 'sleep()' for pauses as per official v2-docs.\n"
                        "- Use 'maqueenPlusV2' library for all robot movements.\n"
                        "- If the user mentions sound or logo, use V2-specific features.\n"
                        "- OUTPUT ONLY RAW CODE. No markdown, no text."
                    )
                    
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": v2_sys_prompt}] + st.session_state.chat_history
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
                    st.error(f"Error: {e}")

    if st.session_state.last_output:
        with st.expander("💡 Επεξήγηση"):
            exp_sys = "Είσαι καθηγητής. Εξήγησε τον κώδικα στα Ελληνικά με βάση τις δυνατότητες του micro:bit V2."
            explanation = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": exp_sys}, {"role": "user", "content": st.session_state.last_output}]
            )
            st.write(explanation.choices[0].message.content)
