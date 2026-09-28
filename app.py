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
# ΚΕΝΤΡΙΚΗ ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS (CONNECTIONS.GSHEETS)
# ==========================================
@st.cache_resource
def get_gspread_client():
    creds_dict = {
        "type": st.secrets["connections"]["gsheets"]["type"],
        "project_id": st.secrets["connections"]["gsheets"]["project_id"],
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key": st.secrets["connections"]["gsheets"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["connections"]["gsheets"]["client_email"],
        "client_id": st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
        "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"]
    }
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_resource
def get_products_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_products")

@st.cache_resource
def get_company_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("DB_Company")


# ==========================================
# 1. ΣΥΣΤΗΜΑ LOGIN (ΑΣΦΑΛΕΙΑΣ) & PAGE STATE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

if "admin_subpage" not in st.session_state:
    st.session_state.admin_subpage = "menu"

def check_google_sheet_user(username, password):
    """Ελέγχει τα στοιχεία σύνδεσης από το Google Sheet DB_ROBOTICS -> tab DB_user"""
    try:
        client = get_gspread_client()
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
                st.session_state.admin_subpage = "menu"
                st.rerun()
            else:
                role = check_google_sheet_user(input_user, input_pass)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.session_state.admin_subpage = "menu"
                    st.rerun()
                else:
                    st.error("Λάθος Username ή Password!")
    st.stop()

# Πλαϊνό μενού αποσύνδεσης
if st.sidebar.button("Αποσύνδεση"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.admin_subpage = "menu"
    st.rerun()


# ==========================================
# 2. ΠΕΡΙΒΑΛΛΟΝ ΔΙΑΧΕΙΡΙΣΤΗ (ADMIN / DB_ROBOTICS)
# ==========================================
if st.session_state.user_role == "admin":
    
    # Κεντρικός τίτλος ενότητας
    st.title("🛠️ Admin Portal: Διαχείριση Συστήματος")
    st.write("Διαχείριση δεδομένων στο Google Sheet **DB_ROBOTICS**.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Α: ΚΕΝΤΡΙΚΟ ΜΕΝΟΥ ΔΙΑΧΕΙΡΙΣΤΗ
    # ------------------------------------------
    if st.session_state.admin_subpage == "menu":
        st.subheader("🏢 ΕΤΑΙΡΙΑ ΠΡΟΙΟΝΤΟΣ")
        st.write("Διαχείριση εταιριών (tab DB_Company):")

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            if st.button("➕ Εισαγωγή Εταιρίας", use_container_width=True):
                st.session_state.admin_subpage = "insert_company"
                st.rerun()
        with col_c2:
            if st.button("✏️ Επεξεργασία Εταιρίας", use_container_width=True):
                st.session_state.admin_subpage = "edit_company"
                st.rerun()
        with col_c3:
            if st.button("📋 Λίστα Εταιριών", use_container_width=True):
                st.session_state.admin_subpage = "list_company"
                st.rerun()

        st.markdown("---")
        st.subheader("📦 Εισαγωγή - Επεξεργασία Προιόντος")
        st.write("Επιλέξτε μια από τις παρακάτω ενέργειες:")

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            if st.button("➕ Εισαγωγή Προιόντος", use_container_width=True):
                st.session_state.admin_subpage = "insert"
                st.rerun()
        with col_m2:
            if st.button("✏️ Επεξεργασία Προιόντος", use_container_width=True):
                st.session_state.admin_subpage = "edit"
                st.rerun()
        with col_m3:
            if st.button("📋 Λίστα εξοπλισμού", use_container_width=True):
                st.session_state.admin_subpage = "list"
                st.rerun()

    # ------------------------------------------
    # ΣΕΛΙΔΑ Β: ΛΙΣΤΑ ΕΞΟΠΛΙΣΜΟΥ (ΠΡΟΒΟΛΗ)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list":
        if st.button("⬅️ Επιστροφή στο Μενού"):
            st.session_state.admin_subpage = "menu"
            st.rerun()

        col_ref1, col_ref2 = st.columns([3, 1])
        with col_ref2:
            if st.button("🔄 Ανανέωση Δεδομένων", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

        st.subheader("📋 Εισαγωγή - Επεξεργασία Προιόντος: Λίστα Εξοπλισμού")
        
        try:
            sheet = get_products_sheet()
            records = sheet.get_all_records()
            if records:
                df_products = pd.DataFrame(records)
                st.dataframe(df_products, use_container_width=True)
            else:
                st.info("Η καρτέλα db_products είναι προς το παρόν άδεια.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Γ: ΕΙΣΑΓΩΓΗ ΝΕΟΥ ΠΡΟΪΟΝΤΟΣ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "insert":
        if st.button("⬅️ Επιστροφή στο Μενού"):
            st.session_state.admin_subpage = "menu"
            st.rerun()

        st.subheader("➕ Εισαγωγή - Επεξεργασία Προιόντος: Φόρμα Εισαγωγής Νέου Προιόντος")
        
        # Υπολογισμός αυτόματου Product ID
        try:
            p_sheet = get_products_sheet()
            p_records = p_sheet.get_all_records()
            if p_records:
                p_ids = []
                for r in p_records:
                    val = r.get("product_id", r.get("Product ID", r.get("id", len(p_ids) + 1)))
                    try:
                        p_ids.append(int(val))
                    except:
                        pass
                next_p_id = max(p_ids) + 1 if p_ids else len(p_records) + 1
            else:
                next_p_id = 1
        except:
            next_p_id = 1

        st.info(f"Αυτόματο Product ID που θα αποθηκευτεί: **{next_p_id}**")

        # Φόρτωση εταιριών για το dropdown
        company_list = []
        try:
            c_sheet = get_company_sheet()
            c_records = c_sheet.get_all_records()
            for r in c_records:
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_name and c_name not in company_list:
                    company_list.append(c_name)
        except Exception as e:
            pass

        with st.form("insert_form"):
            if company_list:
                selected_company = st.selectbox("Εταιρεία (product_company)", options=company_list)
            else:
                selected_company = st.text_input("Εταιρεία (product_company) - (Δεν βρέθηκαν εταιρίες στο DB_Company)")
            
            p_name = st.text_input("Όνομα Προιόντος (product_name)")
            p_qty = st.number_input("Ποσότητα (Quantity)", min_value=0, step=1)
            p_year = st.number_input("Έτος (Year)", min_value=2000, max_value=2100, value=2026, step=1)
            
            insert_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_btn:
                if p_name.strip() and selected_company:
                    try:
                        p_sheet = get_products_sheet()
                        # Αποθήκευση με τα πεδία: product_id, product_company, product_name, quantity, year (ή ανάλογα με τις στήλες σου)
                        p_sheet.append_row([next_p_id, selected_company, p_name.strip(), p_qty, p_year])
                        st.success("Το προϊόν αποθηκεύτηκε κανονικά! Πατήστε «🔄 Ανανέωση Δεδομένων» στη λίστα εξοπλισμού για να το δείτε.")
                    except Exception as e:
                        st.error(f"Σφάλμα εισαγωγής: {e}")
                else:
                    st.warning("Το όνομα προϊόντος και η εταιρεία είναι υποχρεωτικά.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Δ: ΕΠΕΞΕΡΓΑΣΙΑ ΥΠΑΡΧΟΝΤΟΣ ΠΡΟΪΟΝΤΟΣ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "edit":
        if st.button("⬅️ Επιστροφή στο Μενού"):
            st.session_state.admin_subpage = "menu"
            st.rerun()

        st.subheader("✏️ Εισαγωγή - Επεξεργασία Προιόντος: Φόρμα Επεξεργασίας / Διόρθωσης Προιόντος")
        
        with st.form("edit_form"):
            edit_id = st.text_input("Product ID προς διόρθωση (βάσει αυτού γίνεται η αναζήτηση)")
            edit_company = st.text_input("Νέα Εταιρεία (product_company)")
            edit_name = st.text_input("Νέο Όνομα Προιόντος (product_name)")
            edit_qty = st.number_input("Νέα Ποσότητα", min_value=0, step=1)
            edit_year = st.number_input("Νέο Έτος", min_value=2000, max_value=2100, value=2026, step=1)
            
            edit_btn = st.form_submit_button("Οριστική Ενημέρωση")
            
            if edit_btn:
                if edit_id.strip():
                    try:
                        sheet = get_products_sheet()
                        cell = sheet.find(edit_id.strip())
                        if cell:
                            row_num = cell.row
                            sheet.update_cell(row_num, 2, edit_company.strip())
                            sheet.update_cell(row_num, 3, edit_name.strip())
                            sheet.update_cell(row_num, 4, edit_qty)
                            sheet.update_cell(row_num, 5, edit_year)
                            st.success(f"Το προϊόν με ID '{edit_id}' ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» για να το δείτε.")
                        else:
                            st.error(f"Δεν βρέθηκε προϊόν με ID: {edit_id}")
                    except Exception as e:
                        st.error(f"Σφάλμα ενημέρωσης: {e}")
                else:
                    st.warning("Συμπληρώστε το Product ID που θέλετε να διορθώσετε.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ε: ΛΙΣΤΑ ΕΤΑΙΡΙΩΝ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list_company":
        if st.button("⬅️ Επιστροφή στο Μενού"):
            st.session_state.admin_subpage = "menu"
            st.rerun()

        col_ref1, col_ref2 = st.columns([3, 1])
        with col_ref2:
            if st.button("🔄 Ανανέωση Δεδομένων", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

        st.subheader("📋 ΕΤΑΙΡΙΑ ΠΡΟΙΟΝΤΟΣ: Λίστα Εταιριών")
        
        try:
            c_sheet = get_company_sheet()
            records = c_sheet.get_all_records()
            if records:
                df_company = pd.DataFrame(records)
                if df_company.shape[1] >= 2:
                    df_company = df_company.iloc[:, :2]
                    df_company.columns = ["ID", "ΕΠΩΝΥΜΙΑ"]
                st.dataframe(df_company, use_container_width=True, hide_index=True)
            else:
                st.info("Η καρτέλα DB_Company είναι προς το παρόν άδεια.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων εταιριών: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ ΣΤ: ΕΙΣΑΓΩΓΗ ΝΕΑΣ ΕΤΑΙΡΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "insert_company":
        if st.button("⬅️ Επιστροφή στο Μενού"):
            st.session_state.admin_subpage = "menu"
            st.rerun()

        st.subheader("➕ ΕΤΑΙΡΙΑ ΠΡΟΙΟΝΤΟΣ: Φόρμα Εισαγωγής Νέας Εταιρίας")
        
        try:
            c_sheet = get_company_sheet()
            records = c_sheet.get_all_records()
            if records:
                ids = []
                for r in records:
                    val = r.get("company_id", r.get("Company ID", len(ids) + 1))
                    try:
                        ids.append(int(val))
                    except:
                        pass
                next_id = max(ids) + 1 if ids else len(records) + 1
            else:
                next_id = 1
        except:
            next_id = 1

        st.info(f"Αυτόματο company_id που θα αποθηκευτεί: **{next_id}**")

        with st.form("insert_company_form"):
            company_name = st.text_input("Όνομα Εταιρίας (company_name)")
            insert_c_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_c_btn:
                if company_name.strip():
                    try:
                        c_sheet = get_company_sheet()
                        c_sheet.append_row([next_id, company_name.strip()])
                        st.success("Η εταιρία αποθηκεύτηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στη λίστα εταιριών για να την δείτε.")
                    except Exception as e:
                        st.error(f"Σφάλμα αποθήκευσης: {e}")
                else:
                    st.warning("Το όνομα της εταιρίας είναι υποχρεωτικό.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ζ: ΕΠΕΞΕΡΓΑΣΙΑ ΕΤΑΙΡΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "edit_company":
        if st.button("⬅️ Επιστροφή στο Μενού"):
            st.session_state.admin_subpage = "menu"
            st.rerun()

        st.subheader("✏️ ΕΤΑΙΡΙΑ ΠΡΟΙΟΝΤΟΣ: Φόρμα Επεξεργασίας / Διόρθωσης Εταιρίας")
        
        company_options = {}
        try:
            c_sheet = get_company_sheet()
            records = c_sheet.get_all_records()
            for r in records:
                c_id = str(r.get("company_id", r.get("Company ID", ""))).strip()
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_id:
                    company_options[f"ID: {c_id} - {c_name}"] = c_id
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης εταιριών: {e}")

        if not company_options:
            st.warning("Δεν βρέθηκαν καταχωρημένες εταιρίες στο tab DB_Company.")
        else:
            with st.form("edit_company_form"):
                selected_option = st.selectbox("Επιλέξτε Εταιρία προς Τροποποίηση", options=list(company_options.keys()))
                new_c_name = st.text_input("Νέο Όνομα Εταιρίας (company_name)")
                
                edit_c_btn = st.form_submit_button("Οριστική Ενημέρωση")
                
                if edit_c_btn:
                    selected_id = company_options[selected_option]
                    if selected_id and new_c_name.strip():
                        try:
                            c_sheet = get_company_sheet()
                            cell = c_sheet.find(selected_id)
                            if cell:
                                row_num = cell.row
                                c_sheet.update_cell(row_num, 2, new_c_name.strip())
                                st.success(f"Η εταιρία με ID '{selected_id}' ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» για να το δείτε.")
                            else:
                                st.error(f"Δεν βρέθηκε η εταιρία στο Google Sheet.")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης: {e}")
                    else:
                        st.warning("Συμπληρώστε το νέο όνομα της εταιρίας.")


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
