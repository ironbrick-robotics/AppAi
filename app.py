import streamlit as st
from openai import OpenAI
import datetime
import requests
import re
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="AppIDE", layout="wide")
st.title("AppIDE: LLM-Based Robotics Tutor")

# Ανάγνωση από αρχεία txt
def load_research_file(filename, default_text):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return default_text

# Σύνδεση με API/GROQ 
try:
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Config Error: {e}")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tabs
tab_ide, tab_config, tab_pre, tab_post, tab_exersices = st.tabs(["AppIDE", "Help", "Pre Test", "Post Test", "Exersices"])

with tab_pre:
    st.subheader("Αρχική Αξιολόγηση")
    pre_test_url = "https://forms.gle/wHkXG48y6xwWJV929"
    components.iframe(pre_test_url, height=800, scrolling=True)

with tab_post:
    st.subheader("Τελική Αξιολόγηση")
    post_test_url = "https://forms.gle/V5AW1eTAFRHEiaBs5"
    components.iframe(post_test_url, height=800, scrolling=True)

with tab_exersices:
    st.subheader("Ασκήσεις")
    st.text_area("excersices.txt", load_research_file("excersices.txt", "No excersices found."), height=1200, disabled=True)

with tab_config:    
    col_r, col_k, col_b = st.columns(3)
    with col_r:
        st.subheader("Rubric (L1-L5)")
        st.text_area("rubric.txt", load_research_file("rubric.txt", "No rubric found."), height=500, disabled=True)
    with col_k:
        st.subheader("Knowledge Base")
        st.text_area("knowledge.txt", load_research_file("knowledge.txt", "No docs found."), height=200, disabled=True)
    with col_b:
        st.subheader("Model Behavior")
        st.text_area("behavior.txt", load_research_file("behavior.txt", "No behavior found."), height=200, disabled=True)

with tab_ide:
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("input_form"):
            student_id = st.text_input("ID Μαθητή:", "---")
            mode = st.radio("Ενέργεια:", ["Νέα_Εντολή", "Διόρθωση"], horizontal=True)
            user_input = st.text_area("Κείμενο:", height=150)
            btn = st.form_submit_button("Εκτέλεση & Αποθήκευση")

    with col2:
        if btn and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            my_rubric = load_research_file("rubric.txt", "Categorize L1 to L5.")
            my_knowledge = load_research_file("knowledge.txt", "Use MicroPython v2.")
            my_behavior = load_research_file("behavior.txt", "Be a professional teacher.")
            
            with st.spinner('Αναμονή...'):
                try:
                    # Level L1-L5
                    class_sys = f"You are an educational researcher. Classify the prompt into one level using ONLY this rubric:\n{my_rubric}\nReturn ONLY the label (e.g., L3)."
                    class_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": class_sys}, {"role": "user", "content": user_input}]
                    )
                    auto_level = class_res.choices[0].message.content.strip()

                    # Δημιουργία κώδικα
                    v2_sys = f"{my_behavior}\nReference Docs: {my_knowledge}\nSTRICT RULE: Only raw code, no markdown, no comments."
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": v2_sys}] + st.session_state.chat_history
                    )
                    clean_code = re.sub(r'```[a-z]*', '', code_res.choices[0].message.content.strip()).replace('```', '').strip()

                    st.markdown(f"Κώδικας")
                    st.code(clean_code, language='python')
                    
                    # Επεξήγηση & Βοήθεια
                    with st.expander("Βοήθεια", expanded=True):
                        # Δυναμικό system prompt ανάλογα με την ενέργεια
                        if mode == "Διόρθωση":
                            help_sys = f"{my_behavior}\nΕίσαι καθηγητής ρομποτικής. Ο μαθητής ζήτησε διόρθωση. Εξήγησε αναλυτικά ΠΟΥ ήταν το λάθος στον προηγούμενο κώδικα (π.χ. κεφαλαία γράμματα, εσοχές, λάθος εντολή) και ΓΙΑΤΙ η νέα έκδοση είναι σωστή. Μίλα απλά στα Ελληνικά για παιδιά."
                        else:
                            help_sys = f"{my_behavior}\nΕίσαι καθηγητής ρομποτικής. Εξήγησε σύντομα στα Ελληνικά τι κάνει ο παραπάνω κώδικας και δώσε μια συμβουλή για το επόμενο βήμα. Μίλα απλά για παιδιά."
                        
                        help_res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": help_sys}, {"role": "user", "content": f"Prompt μαθητή: {user_input}\nΤελικός Κώδικας: {clean_code}"}]
                        )
                        st.write(help_res.choices[0].message.content)
                   
                    # Αποθήκευση στο Google Sheet
                    if DB_URL:
                        requests.post(DB_URL, json={"data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": student_id,
                            "Action": mode,
                            "Coding_Level": auto_level,
                            "Prompt": user_input,
                            "Code": clean_code.replace('"', "'")
                        }]})
                except Exception as e:
                    st.error(f"Error: {e}")

















