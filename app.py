import streamlit as st
from openai import OpenAI
import datetime
import requests
import re
import os

# --- ΕΡΕΥΝΗΤΙΚΟ ΠΕΡΙΒΑΛΛΟΝ iron2 ---
st.set_page_config(page_title="ironbrick IDE | iron2 Official", layout="wide")

# Συνάρτηση για ανάγνωση των ερευνητικών αρχείων
def load_research_file(filename, default_text):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return default_text

# Σύνδεση με API
try:
    if "GROQ_API_KEY" in st.secrets:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    DB_URL = st.secrets.get("GSHEET_URL", "")
except Exception as e:
    st.error(f"Config Error: {e}")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tabs: IDE και Ρυθμίσεις Έρευνας
tab_ide, tab_config = st.tabs(["💻 IDE", "⚙️ Research Config"])

with tab_config:
    st.header("Research Control Center (iron2)")
    st.info("Τα παρακάτω δεδομένα φορτώνονται από τα .txt αρχεία στο GitHub σου.")
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
        if st.button("🗑️ Νέα Συνομιλία"):
            st.session_state.chat_history = []
            st.rerun()

        with st.form("input_form"):
            student_id = st.text_input("ID Μαθητή:", "S01")
            mode = st.radio("Ενέργεια:", ["Νέα Εντολή", "Διόρθωση/Debug"], horizontal=True)
            user_input = st.text_area("Περιγράψτε την αποστολή:", height=150)
            btn = st.form_submit_button("Εκτέλεση & Καταγραφή")

    with col2:
        if btn and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Φόρτωση δυναμικών οδηγιών από τα αρχεία σου
            my_rubric = load_research_file("rubric.txt", "Categorize L1 to L5.")
            my_knowledge = load_research_file("knowledge.txt", "Use MicroPython v2.")
            my_behavior = load_research_file("behavior.txt", "Be a professional teacher.")
            
            with st.spinner('Ανάλυση βάσει ερευνητικού πρωτοκόλλου...'):
                try:
                    # ΒΗΜΑ 1: ΑΥΤΟΜΑΤΗ ΚΑΤΑΤΑΞΗ (Research Mapping)
                    class_sys = f"You are an educational researcher. Classify the prompt into one level using ONLY this rubric:\n{my_rubric}\nReturn ONLY the label (e.g., L3)."
                    class_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": class_sys}, {"role": "user", "content": user_input}]
                    )
                    auto_level = class_res.choices[0].message.content.strip()

                    # ΒΗΜΑ 2: ΠΑΡΑΓΩΓΗ ΚΩΔΙΚΑ (Pedagogical Output)
                    v2_sys = f"{my_behavior}\nReference Docs: {my_knowledge}\nSTRICT RULE: Only raw code, no markdown, no comments."
                    code_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": v2_sys}] + st.session_state.chat_history
                    )
                    clean_code = re.sub(r'```[a-z]*', '', code_res.choices[0].message.content.strip()).replace('```', '').strip()

                    st.markdown(f"**Research Level: {auto_level}**")
                    st.code(clean_code, language='python')

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
