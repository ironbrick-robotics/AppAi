import streamlit as st
from openai import OpenAI
import datetime
import requests
import re
import os

# Ονομασία Εφαρμογής - 
st.set_page_config(page_title="AppIDE", layout="wide")

# Συνάρτηση ανάγνωσης από αρχεία txt
def load_research_file(filename, default_text):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return default_text

# Σύνδεση με API - GROQ 
try:
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Config Error: {e}")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tabs
tab_ide, tab_config = st.tabs(["AppIDE", "Help"])

with tab_config:    
    col_r, col_k, col_b = st.columns(3)
    with col_r:
        st.subheader("Rubric (L1-L5)")
        st.text_area("rubric.txt", load_research_file("rubric.txt", "No rubric found."), height=200, disabled=True)
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
                    # ΒΗΜΑ 1: ΑΥΤΟΜΑΤΗ ΚΑΤΑΤΑΞΗ 
                    class_sys = f"You are an educational researcher. Classify the prompt into one level using ONLY this rubric:\n{my_rubric}\nReturn ONLY the label (e.g., L3)."
                    class_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": class_sys}, {"role": "user", "content": user_input}]
                    )
                    auto_level = class_res.choices[0].message.content.strip()

                    # ΒΗΜΑ 2: ΠΑΡΑΓΩΓΗ ΚΩΔΙΚΑ 
                    v2_sys = f"{my_behavior}\nReference Docs: {my_knowledge}\nSTRICT RULE: Only raw code, no markdown, no comments."
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": v2_sys}] + st.session_state.chat_history
                    )
                    clean_code = re.sub(r'```[a-z]*', '', code_res.choices[0].message.content.strip()).replace('```', '').strip()

                    st.markdown(f"**Research Level: {auto_level}**")
                    st.code(clean_code, language='python')
                    
                    # ΒΗΜΑ 4: ΠΑΙΔΑΓΩΓΙΚΗ ΒΟΗΘΕΙΑ (Scaffolding Mode)
                    with st.expander("💡 Επεξήγηση & Βοήθεια", expanded=True):
                        help_sys = "Είσαι καθηγητής ρομποτικής. Εξήγησε σύντομα στα Ελληνικά τι κάνει ο παραπάνω κώδικας και δώσε μια συμβουλή για το επόμενο βήμα."
                        help_res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": help_sys}, {"role": "user", "content": f"Κώδικας: {clean_code}"}]
                        )
                        st.write(help_res.choices[0].message.content)
                    
                    # ΒΗΜΑ 3: LOGGING ΣΤΟ GOOGLE SHEET
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



