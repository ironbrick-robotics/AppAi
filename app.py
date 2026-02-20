import streamlit as st
from openai import OpenAI
import datetime
import requests

# --- ΕΡΕΥΝΗΤΙΚΟ ΠΕΡΙΒΑΛΛΟΝ IRONBRICK ---
# Υλοποίηση: [Το Ονοματεπώνυμό Σου]
# Σκοπός: Μελέτη μετάβασης από Blocks σε Text-based Code

st.set_page_config(page_title="ironbrick Research IDE", layout="wide")

# Custom CSS για το interface της έρευνας
st.markdown("""
    <style>
    header {visibility: hidden;}
    .stExpander { border: 2px solid #00a0dc; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# Σύνδεση με τα API (Secrets)
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("Connection Error: Check API Configuration.")

# Ορισμός του δικού σου Coding Scheme για την ανάλυση
MY_CODING_LOGIC = (
    "Analyze the student's prompt and categorize it into the following levels: "
    "L1: Simple natural language, L2: Parameters/Values, L3: Logic/Loops, "
    "L4: Technical Terminology, L5: Debugging/Iteration. "
    "Return only the label (e.g., L3)."
)

# Κύριο Interface
tab_ide, tab_logs = st.tabs(["💻 IDE", "📊 Data Access"])

with tab_ide:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.form("input_form"):
            student_id = st.text_input("Student Code:", "S01")
            mode = st.selectbox("Task Type:", ["New Mission", "Correction"])
            user_input = st.text_area("Περιγράψτε την αποστολή:", height=150)
            btn = st.form_submit_button("Generate Code")

    with col2:
        if btn and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # 1. Αυτόματη Κωδικοποίηση (Research Metric)
            analysis = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": MY_CODING_LOGIC}, {"role": "user", "content": user_input}]
            )
            current_level = analysis.choices[0].message.content.strip()

            # 2. Παραγωγή Κώδικα Maqueen
            maqueen_prompt = "Expert Maqueen coder. Clean code only, no explanations, no markdown blocks."
            messages = [{"role": "system", "content": maqueen_prompt}] + st.session_state.chat_history
            code_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            final_code = code_res.choices[0].message.content.strip()
            
            st.session_state.last_output = final_code
            st.code(final_code, language='python')

            # 3. Αυτόματο Logging στο Google Sheet
            log_data = {
                "data": [{
                    "Timestamp": str(datetime.datetime.now()),
                    "Student_ID": student_id,
                    "Action": mode,
                    "Coding_Level": current_level,
                    "Prompt": user_input,
                    "Code": final_code
                }]
            }
            requests.post(DB_URL, json=log_data)
            st.toast(f"Logged as {current_level}")

    # Παιδαγωγική Ανατροφοδότηση
    if "last_output" in st.session_state:
        with st.expander("💡 Επεξήγηση Κώδικα για τον Μαθητή"):
            pedagogical_prompt = "Είσαι καθηγητής ρομποτικής. Εξήγησε τον κώδικα στα Ελληνικά με απλά λόγια."
            explanation = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": pedagogical_prompt}, {"role": "user", "content": st.session_state.last_output}]
            )
            st.write(explanation.choices[0].message.content)
