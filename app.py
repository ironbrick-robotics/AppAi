import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import datetime
import requests
import re
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="AppIDE & Admin Portal", layout="wide")

# ==========================================
# ΑΣΦΑΛΗΣ ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
# ==========================================
@st.cache_resource
def get_gspread_client():
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_dict = dict(st.secrets["connections"]["gsheets"])
        elif "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        else:
            return None
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        return None

@st.cache_resource
def get_products_sheet():
    client = get_gspread_client()
    if client:
        return client.open("DB_ROBOTICS").worksheet("db_products")
    return None

# ==========================================
# 1. ΣΥΣΤΗΜΑ LOGIN (ΑΣΦΑΛΕΙΑΣ)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

def check_google_sheet_user(username, password):
    """Ελέγχει τα στοιχεία σύνδεσης από το Google Sheet DB_ROBOTICS -> tab DB_user"""
    try:
        client = get_gspread_client()
        if client:
            sheet = client.open("DB_ROBOTICS").worksheet("DB_user")
            records = sheet.get_all_records()
            
            for row in records:
                u = str(row.get("username", row.get("Username", ""))).strip()
                p = str(row.get("password", row.get("Password", ""))).strip()
                r = str(row.get("role", row.get("Role", "admin"))).strip()
                if u == username and p == password:
                    return r
    except Exception as e:
        pass
        
    # Fallback διαχειριστής
    if username == "admin" and password == "admin2026!":
        return "admin"
        
    return None

# Φόρμα Σύνδεσης
if not st.session_state.logged_in:
    st.title("🔐 Είσοδος στην Εφαρμογή")
    with st.form("login_form"):
        input_user = st.text_input("Username")
        input_pass = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Είσοδος")
        
        if login_btn:
            if input_user == "argykoyr" and input_pass == "ai_agent":
                st.session_state.logged_in = True
                st.session_state.user_role = "tutor"
                st.rerun()
            else:
                role = check_google_sheet_user(input_user, input_pass)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.rerun()
                else:
                    st.error("Λάθος Username ή Password!")
    st.stop()

# Πλαϊνό μενού αποσύνδεσης
if st.sidebar.button("Αποσύνδεση"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()


# ==========================================
# 2. ΠΕΡΙΒΑΛΛΟΝ ΔΙΑΧΕΙΡΙΣΤΗ (ADMIN / DB_ROBOTICS -> db_products)
# ==========================================
if st.session_state.user_role == "admin":
    st.title("🛠️ Admin Portal: Διαχείριση Εξοπλισμού")
    st.write("Διαχείριση προϊόντων στην καρτέλα **db_products** του Google Sheet **DB_ROBOTICS**.")

    # --- ΚΟΥΜΠΙ ΑΝΑΝΕΩΣΗΣ ΔΕΔΟΜΕΝΩΝ ---
    col_ref1, col_ref2 = st.columns([3, 1])
    with col_ref2:
        if st.button("🔄 Ανανέωση Δεδομένων"):
            st.cache_resource.clear()
            st.rerun()

    # Ενότητα: Εξοπλισμός
    st.header("📦 Εξοπλισμός")
    
    # 1. Προβολή τρεχόντων προϊόντων
    try:
        sheet = get_products_sheet()
        if sheet:
            records = sheet.get_all_records()
            if records:
                df_products = pd.DataFrame(records)
                st.dataframe(df_products, use_container_width=True)
            else:
                st.info("Η καρτέλα db_products είναι προς το παρόν άδεια.")
        else:
            st.warning("Δεν κατέστη δυνατή η σύνδεση με το Google Sheet. Ελέγξτε τα Secrets.")
    except Exception as e:
        st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

    st.markdown("---")

    # 2. Επιλογή ενέργειας (Εισαγωγή ή Επεξεργασία)
    action = st.radio(
        "Επιλέξτε ενέργεια διαχείρισης:", 
        ["Επιλέξτε...", "➕ Εισαγωγή Νέου Προιόντος", "✏️ Επεξεργασία Υπάρχοντος Προιόντος"],
        horizontal=True
    )

    if action == "➕ Εισαγωγή Νέου Προιόντος":
        st.subheader("➕ Φόρμα Εισαγωγής Προιόντος")
        with st.form("insert_form"):
            p_id = st.text_input("Product ID")
            p_company = st.text_input("Εταιρεία (Company)")
            p_name = st.text_input("Όνομα Προιόντος (Name)")
            p_qty = st.number_input("Ποσότητα (Quantity)", min_value=0, step=1)
            p_year = st.number_input("Έτος (Year)", min_value=2000, max_value=2100, value=2026, step=1)
            
            insert_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_btn:
                if p_id:
                    try:
                        sheet = get_products_sheet()
                        if sheet:
                            sheet.append_row([p_id, p_company, p_name, p_qty, p_year])
                            st.success("Το προϊόν προστέθηκε επιτυχώς!")
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.error("Σφάλμα σύνδεσης με τη βάση.")
                    except Exception as e:
                        st.error(f"Σφάλμα εισαγωγής: {e}")
                else:
                    st.warning("Το Product ID είναι υποχρεωτικό.")

    elif action == "✏️ Επεξεργασία Υπάρχοντος Προιόντος":
        st.subheader("✏️ Φόρμα Επεξεργασίας / Διόρθωσης Προιόντος")
        with st.form("edit_form"):
            edit_id = st.text_input("Product ID προς διόρθωση (βάσει αυτού γίνεται η αναζήτηση)")
            edit_company = st.text_input("Νέα Εταιρεία")
            edit_name = st.text_input("Νέο Όνομα Προιόντος")
            edit_qty = st.number_input("Νέα Ποσότητα", min_value=0, step=1)
            edit_year = st.number_input("Νέο Έτος", min_value=2000, max_value=2100, value=2026, step=1)
            
            edit_btn = st.form_submit_button("Οριστική Ενημέρωση")
            
            if edit_btn:
                if edit_id:
                    try:
                        sheet = get_products_sheet()
                        if sheet:
                            cell = sheet.find(edit_id)
                            if cell:
                                row_num = cell.row
                                sheet.update_cell(row_num, 2, edit_company)
                                sheet.update_cell(row_num, 3, edit_name)
                                sheet.update_cell(row_num, 4, edit_qty)
                                sheet.update_cell(row_num, 5, edit_year)
                                st.success(f"Το προϊόν με ID '{edit_id}' ενημερώθηκε επιτυχώς!")
                                st.cache_resource.clear()
                                st.rerun()
                            else:
                                st.error(f"Δεν βρέθηκε προϊόν με ID: {edit_id}")
                        else:
                            st.error("Σφάλμα σύνδεσης με τη βάση.")
                    except Exception as e:
                        st.error(f"Σφάλμα ενημέρωσης: {e}")
                else:
                    st.warning("Συμπληρώστε το Product ID που θέλετε να διορθώσετε.")


# ==========================================
# 3. ΠΕΡΙΒΑΛΛΟΝ TUTOR (AI_AGENT - ΚΛΕΙΔΩΜΕΝΟ)
# ==========================================
elif st.session_state.user_role == "tutor":
    st.title("AppIDE: LLM-Based Robotics Tutor")

    def load_research_file(filename, default_text):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        return default_text

    try:
        if "GROQ_API_KEY" in st.secrets:
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
        DB_URL = st.secrets.get("GSHEET_URL", "")
    except Exception as e:
        st.error(f"Config Error: {e}")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

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
                        class_sys = f"You are an educational researcher. Classify the prompt into one level using ONLY this rubric:\n{my_rubric}\nReturn ONLY the label (e.g., L3)."
                        class_res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": class_sys}, {"role": "user", "content": user_input}]
                        )
                        auto_level = class_res.choices[0].message.content.strip()

                        v2_sys = f"{my_behavior}\nReference Docs: {my_knowledge}\nSTRICT RULE: Output ONLY MicroPython code. No explanations, no introductory text, no markdown code blocks, no comments. Start directly with 'from microbit import *'."
                        code_res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": v2_sys}] + st.session_state.chat_history
                        )
                        raw_output = code_res.choices[0].message.content.strip()
                        clean_code = re.sub(r'```(?:python|micropython|)?', '', raw_output, flags=re.IGNORECASE).replace('```', '').strip()

                        st.markdown(f"Κώδικας")
                        st.code(clean_code, language='python')
                        
                        with st.expander("Βοήθεια", expanded=True):
                            if mode == "Διόρθωση":
                                help_sys = f"{my_behavior}\nΕίσαι καθηγητής ρομποτικής. Ο μαθητής ζήτησε διόρθωση. Εξήγησε αναλυτικά ΠΟΥ ήταν το λάθος στον προηγούμενο κώδικα και ΓΙΑΤΙ η νέα έκδοση είναι σωστή."
                            else:
                                help_sys = f"{my_behavior}\nΕίσαι καθηγητής ρομποτικής. Εξήγησε σύντομα στα Ελληνικά τι κάνει ο παραπάνω κώδικας και δώσε μια συμβουλή."
                            
                            help_res = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "system", "content": help_sys}, {"role": "user", "content": f"Prompt μαθητής: {user_input}\nΤελικός Κώδικας: {clean_code}"}]
                            )
                            st.write(help_res.choices[0].message.content)
                        
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
