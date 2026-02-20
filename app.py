import streamlit as st
from openai import OpenAI
import datetime
import requests

# --- ΕΡΕΥΝΗΤΙΚΟ ΠΕΡΙΒΑΛΛΟΝ IRONBRICK ---
# Υλοποίηση: [Το Ονοματεπώνυμό Σου]

st.set_page_config(page_title="ironbrick Research IDE", layout="wide")

# Custom CSS
st.markdown("<style>header {visibility: hidden;} .stExpander { border: 2px solid #00a0dc; border-radius: 8px; }</style>", unsafe_allow_html=True)

# Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("Connection Error.")

# --- RESEARCH LOGIC ---
MY_CODING_LOGIC = (
    "Analyze the student's prompt and categorize it: "
    "L1: Simple natural language, L2: Parameters/Values, L3: Logic/Loops, "
    "L4: Technical Terminology (Huskylens, RGB, etc), L5: Debugging. "
    "Return only the label (e.g., L1)."
)

# Αρχικοποίηση Session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_output" not in st.session_state:
    st.session_state.last_output = ""

# Layout
tab_ide, tab_logs = st.tabs(["💻 IDE", "📊 Data Access"])

with tab_ide:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Κουμπί Καθαρισμού Συνομιλίας
        if st.button("🗑️ Καθαρισμός Ιστορικού"):
            st.session_state.chat_history = []
            st.session_state.last_output = ""
            st.rerun()

        with st.form("input_form"):
            student_id = st.text_input("Student Code:", "S01")
            # Αλλαγή Task names
            mode = st.radio("Τύπος Ενέργειας:", ["Νέα Συνομιλία", "Διορθωση εντολής"], horizontal=True)
            user_input = st.text_area("Περιγράψτε την αποστολή στο Maqueen:", height=150)
            btn = st.form_submit_button("Εκτέλεση")

    with col2:
        if btn and user_input:
            # Αν είναι Νέα Συνομιλία, καθαρίζουμε το ιστορικό πριν το νέο prompt
            if mode == "Νέα Συνομιλία":
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner('Ανάλυση...'):
                # 1. Κατάταξη L1-L5
                analysis = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
                )
                current_level = analysis.choices[0].message.content.strip()

                # 2. Παραγωγή Κώδικα (Maqueen & Huskylens focus)
                maqueen_sys = (
                    "You are a Maqueen Robot expert. Generate ONLY clean code for micro:bit Maqueen. "
                    "Support libraries: Maqueen, Huskylens, NeoPixel. "
                    "Return ONLY the code, no markdown, no comments, no greetings."
                )
                messages = [{"role": "system", "content": maqueen_sys}] + st.session_state.chat_history
                code_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
                final_code = code_res.choices[0].message.content.strip()
                
                st.session_state.last_output = final_code
                st.markdown(f"**Επίπεδο: {current_level}**")
                st.code(final_code, language='python')

                # 3. Logging
                log_entry = {
                    "data": [{
                        "Timestamp": str(datetime.datetime.now()),
                        "Student_ID": student_id,
                        "Action": mode,
                        "Coding_Level": current_level,
                        "Prompt": user_input,
                        "Code": final_code.replace('"', "'")
                    }]
                }
                requests.post(DB_URL, json=log_entry)

    # Επεξήγηση
    if st.session_state.last_output:
        with st.expander("💡 Επεξήγηση Κώδικα"):
            exp_sys = "Είσαι καθηγητής ρομποτικής. Εξήγησε τον κώδικα Maqueen ΜΟΝΟ στα Ελληνικά με απλά λόγια."
            explanation = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": exp_sys}, {"role": "user", "content": st.session_state.last_output}]
            )
            st.write(explanation.choices[0].message.content)
