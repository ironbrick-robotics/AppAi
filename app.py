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
# ΚΕΝΤΡΙΚΗ ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS (ΜΕ CACHING ΓΙΑ ΤΑΧΥΤΗΤΑ)
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

@st.cache_data(ttl=60)
def get_products_records():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_products").get_all_records()

@st.cache_data(ttl=60)
def get_company_records():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("DB_Company").get_all_records()

@st.cache_data(ttl=60)
def get_broken_records():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_broken").get_all_records()

@st.cache_data(ttl=60)
def get_loans_records():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_loans").get_all_records()

@st.cache_data(ttl=60)
def get_robots_records():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_robots").get_all_records()

def get_products_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_products")

def get_company_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("DB_Company")

def get_broken_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_broken")

def get_loans_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_loans")

def get_robots_sheet():
    client = get_gspread_client()
    return client.open("DB_ROBOTICS").worksheet("db_robots")


# ==========================================
# 1. ΣΥΣΤΗΜΑ LOGIN (ΑΣΦΑΛΕΙΑΣ) & PAGE STATE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

if "admin_subpage" not in st.session_state:
    st.session_state.admin_subpage = "menu"

def check_google_sheet_user(username, password):
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
        
    if username == "admin" and password == "admin2026!":
        return "admin"
    return None

if not st.session_state.logged_in:
    st.title("🔐 Είσοδος στην Εφαρμογή")
    with st.form("login_form"):
        input_user = st.text_input("Username")
        input_pass = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Είσοδος")
        
        if login_btn:
            if input_user == "argykoyr" and input_pass == "ai_mentor":
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


# ==========================================
# SIDEBAR: ΠΑΝΤΑ ΔΙΑΘΕΣΙΜΑ ΚΟΥΜΠΙΑ ΨΗΛΑ
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Γενικός Έλεγχος")
    
    if st.button("🔄 Ανανέωση Δεδομένων", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Η μνήμη ανανεώθηκε!")
        st.rerun()

    if st.session_state.user_role == "admin" and st.session_state.admin_subpage != "menu":
        if st.button("🏠 Επιστροφή στο Μενού", use_container_width=True):
            st.session_state.admin_subpage = "menu"
            st.rerun()

    st.markdown("---")
    
    if st.button("🚪 Αποσύνδεση", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.admin_subpage = "menu"
        st.rerun()


# ==========================================
# 2. ΠΕΡΙΒΑΛΛΟΝ ΔΙΑΧΕΙΡΙΣΤΗ (ADMIN / DB_ROBOTICS)
# ==========================================
if st.session_state.user_role == "admin":
    
    st.title("Διαχείριση εξοπλισμού Ρομποτικής")

    if st.session_state.admin_subpage == "menu":
        st.subheader("🏢 Εταιρεία Προϊόντος")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("➕ Εισαγωγή Κατηγορίας", use_container_width=True):
                st.session_state.admin_subpage = "insert_company"
                st.rerun()
        with col_c2:
            if st.button("✏️ Επεξεργασία Κατηγορίας", use_container_width=True):
                st.session_state.admin_subpage = "edit_company"
                st.rerun()

        st.markdown("---")
        st.subheader("📦 Εισαγωγή - Επεξεργασία Προϊόντος")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("➕ Εισαγωγή Προϊόντος", use_container_width=True):
                st.session_state.admin_subpage = "insert"
                st.rerun()
            if st.button("🤝 Δανεισμός Εξοπλισμού", use_container_width=True):
                st.session_state.admin_subpage = "loans"
                st.rerun()
        with col_m2:
            if st.button("✏️ Επεξεργασία Προϊόντος", use_container_width=True):
                st.session_state.admin_subpage = "edit"
                st.rerun()
            if st.button("⚠️ Κατεστραμμένα", use_container_width=True):
                st.session_state.admin_subpage = "broken"
                st.rerun()

        st.markdown("---")
        st.subheader("🤖 Ρομπότ")

        col_rob1, col_rob2 = st.columns(2)
        with col_rob1:
            if st.button("🤖 Κατασκευή Ρομπότ", use_container_width=True):
                st.session_state.admin_subpage = "robot_build"
                st.rerun()
        with col_rob2:
            if st.button("✏️ Επεξεργασία Ρομπότ", use_container_width=True):
                st.session_state.admin_subpage = "robot_edit"
                st.rerun()

        st.markdown("---")
        st.subheader("📊 Αναφορές")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("📋 Λίστα εξοπλισμού", use_container_width=True):
                st.session_state.admin_subpage = "list"
                st.rerun()
            if st.button("📋 Λίστα ενεργών δανεισμών", use_container_width=True):
                st.session_state.admin_subpage = "active_loans_list"
                st.rerun()
        with col_r2:
            if st.button("📋 Λίστα Κατηγοριών", use_container_width=True):
                st.session_state.admin_subpage = "list_company"
                st.rerun()
            if st.button("📋 Λίστα κατεστραμμένων", use_container_width=True):
                st.session_state.admin_subpage = "broken_list"
                st.rerun()
            if st.button("🤖 Λίστα ρομπότ", use_container_width=True):
                st.session_state.admin_subpage = "robot_list"
                st.rerun()

    # ------------------------------------------
    # ΣΕΛΙΔΑ Β: ΛΙΣΤΑ ΕΞΟΠΛΙΣΜΟΥ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list":
        st.subheader("📋 Λίστα Εξοπλισμού")
        
        try:
            p_records = get_products_records()
            b_records = get_broken_records()
            l_records = get_loans_records()
            r_records = get_robots_records()
            
            broken_map = {}
            for br in b_records:
                b_id = str(br.get("broken_id", br.get("ID", ""))).strip()
                b_qty = 0
                try:
                    b_qty = int(br.get("broken_quantity", br.get("Quantity", 0)))
                except:
                    pass
                if b_id:
                    broken_map[b_id] = broken_map.get(b_id, 0) + b_qty

            loan_map = {}
            for lr in l_records:
                status = str(lr.get("status", lr.get("Status", ""))).strip()
                if status == "Ενεργός Δανεισμός":
                    p_name_loan = str(lr.get("product_name", lr.get("Product Name", ""))).strip()
                    l_qty = 0
                    try:
                        l_qty = int(lr.get("quantity_borrowed", lr.get("Quantity", 0)))
                    except:
                        pass
                    if p_name_loan:
                        loan_map[p_name_loan] = loan_map.get(p_name_loan, 0) + l_qty

            robot_usage_map = {}
            for rr in r_records:
                status_r = str(rr.get("status", rr.get("Status", "Ενεργό"))).strip()
                if status_r != "Διαλυμένο":
                    board = str(rr.get("board", "")).strip()
                    s1 = str(rr.get("sensor1", "")).strip()
                    try: s1_qty = int(rr.get("sensor1_qty", 1))
                    except: s1_qty = 1

                    s2 = str(rr.get("sensor2", "")).strip()
                    try: s2_qty = int(rr.get("sensor2_qty", 1))
                    except: s2_qty = 1

                    batt = str(rr.get("battery", "")).strip()
                    try: motors_qty = int(rr.get("motors_qty", 0))
                    except: motors_qty = 0
                    motors_name = str(rr.get("motors", "")).strip()

                    try: wheels_qty = int(rr.get("wheels_qty", 0))
                    except: wheels_qty = 0
                    wheels_name = str(rr.get("wheels", "")).strip()

                    extra_str = str(rr.get("extra_parts", "")).strip()

                    if board: robot_usage_map[board] = robot_usage_map.get(board, 0) + 1
                    if s1: robot_usage_map[s1] = robot_usage_map.get(s1, 0) + s1_qty
                    if s2: robot_usage_map[s2] = robot_usage_map.get(s2, 0) + s2_qty
                    if batt: robot_usage_map[batt] = robot_usage_map.get(batt, 0) + 1
                    if motors_name and motors_qty > 0: robot_usage_map[motors_name] = robot_usage_map.get(motors_name, 0) + motors_qty
                    if wheels_name and wheels_qty > 0: robot_usage_map[wheels_name] = robot_usage_map.get(wheels_name, 0) + wheels_qty

                    if extra_str:
                        for part in extra_str.split(","):
                            if ":" in part:
                                p_part_name, p_part_qty_str = part.split(":", 1)
                                p_part_name = p_part_name.strip()
                                try: p_part_qty = int(p_part_qty_str.strip())
                                except: p_part_qty = 0
                                if p_part_name:
                                    robot_usage_map[p_part_name] = robot_usage_map.get(p_part_name, 0) + p_part_qty

            if p_records:
                table_data = []
                for pr in p_records:
                    p_id = str(pr.get("product_id", pr.get("Product ID", pr.get("id", "")))).strip()
                    p_comp = str(pr.get("product_company", pr.get("Company", ""))).strip()
                    p_sub = str(pr.get("product_subcategory", pr.get("Subcategory", ""))).strip()
                    p_name = str(pr.get("product_name", pr.get("Name", ""))).strip()
                    
                    p_qty = 0
                    try: p_qty = int(pr.get("product_quantity", pr.get("Quantity", 0)))
                    except: pass
                    
                    broken_qty = broken_map.get(p_id, 0)
                    borrowed_qty = loan_map.get(p_name, 0)
                    used_qty = robot_usage_map.get(p_name, 0)
                    
                    functional_qty = max(0, p_qty - broken_qty - borrowed_qty - used_qty)
                    
                    table_data.append({
                        "ΚΩΔΙΚΟΣ": p_id,
                        "ΚΑΤΗΓΟΡΙΑ": p_comp,
                        "ΥΠΟΚΑΤΗΓΟΡΙΑ": p_sub,
                        "ΟΝΟΜΑ ΠΡΟΪΟΝΤΟΣ": p_name,
                        "ΣΥΝΟΛΙΚΑ ΤΕΜΑΧΙΑ": p_qty,
                        "ΑΧΡΗΣΙΜΟΠΟΙΗΤΑ": functional_qty,
                        "ΧΡΗΣΙΜΟΠΟΙΟΥΝΤΑΙ": used_qty,
                        "ΧΑΛΑΣΜΕΝΑ": broken_qty,
                        "ΔΑΝΕΙΣΜΕΝΑ": borrowed_qty
                    })

                df_products = pd.DataFrame(table_data)

                def highlight_empty(row):
                    try:
                        if int(row["ΣΥΝΟΛΙΚΑ ΤΕΜΑΧΙΑ"]) == 0:
                            return ['background-color: rgba(255, 99, 71, 0.25)'] * len(row)
                    except:
                        pass
                    return [''] * len(row)

                styled_df = df_products.style.apply(highlight_empty, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.info("Η καρτέλα db_products είναι προς το παρόν άδεια.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Γ: ΕΙΣΑΓΩΓΗ ΝΕΟΥ ΠΡΟΪΟΝΤΟΣ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "insert":
        st.subheader("➕ Φόρμα Εισαγωγής Νέου Προϊόντος")
        
        try:
            p_records = get_products_records()
            if p_records:
                p_ids = []
                for r in p_records:
                    val = r.get("product_id", r.get("Product ID", r.get("id", len(p_ids) + 1)))
                    try: p_ids.append(int(val))
                    except: pass
                next_p_id = max(p_ids) + 1 if p_ids else len(p_records) + 1
            else:
                next_p_id = 1
        except:
            next_p_id = 1

        st.info(f"Αυτόματο Product ID που θα αποθηκευτεί: **{next_p_id}**")

        company_list = []
        try:
            c_records = get_company_records()
            for r in c_records:
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_name and c_name not in company_list:
                    company_list.append(c_name)
            company_list = sorted(company_list)
        except Exception as e:
            pass

        with st.form("insert_form"):
            if company_list:
                selected_company = st.selectbox("Κατηγορία (product_company)", options=company_list)
            else:
                selected_company = st.text_input("Κατηγορία (product_company)")
            
            subcategories = sorted(["Kit", "Part"])
            selected_subcategory = st.selectbox("Υποκατηγορία (product_subcategory)", options=subcategories)
            
            p_name = st.text_input("Όνομα Προϊόντος (product_name)")
            p_qty = st.number_input("Τεμάχια (product_quantity)", min_value=0, step=1)
            
            insert_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_btn:
                if p_name.strip() and selected_company:
                    try:
                        p_sheet = get_products_sheet()
                        p_sheet.append_row([next_p_id, selected_company, selected_subcategory, p_name.strip(), p_qty])
                        st.success("Το προϊόν αποθηκεύτηκε! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                    except Exception as e:
                        st.error(f"Σφάλμα εισαγωγής: {e}")
                else:
                    st.warning("Το όνομα προϊόντος και η κατηγορία είναι υποχρεωτικά.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Δ: ΕΠΕΞΕΡΓΑΣΙΑ ΥΠΑΡΧΟΝΤΟΣ ΠΡΟΪΟΝΤΟΣ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "edit":
        st.subheader("✏️ Φόρμα Επεξεργασίας Προϊόντος")
        
        company_options = []
        product_records = []
        try:
            c_records = get_company_records()
            for r in c_records:
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_name and c_name not in company_options:
                    company_options.append(c_name)
            company_options = sorted(company_options)
            product_records = get_products_records()
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

        if not company_options or not product_records:
            st.warning("Δεν βρέθηκαν καταχωρημένες κατηγορίες ή προϊόντα.")
        else:
            selected_edit_company = st.selectbox("Επιλέξτε Κατηγορία", options=company_options)
            
            filtered_products = []
            for idx, r in enumerate(product_records):
                comp = str(r.get("product_company", r.get("Company", ""))).strip()
                if comp == selected_edit_company:
                    p_id = str(r.get("product_id", r.get("Product ID", r.get("id", "")))).strip()
                    p_name = str(r.get("product_name", r.get("Name", ""))).strip()
                    filtered_products.append({"row_index": idx + 2, "id": p_id, "name": p_name, "data": r})

            filtered_products = sorted(filtered_products, key=lambda x: x["name"])
            product_display_options = {f"ID: {p['id']} - {p['name']}": p for p in filtered_products}

            if not product_display_options:
                st.info(f"Δεν υπάρχουν προϊόντα για την κατηγορία '{selected_edit_company}'.")
            else:
                selected_prod_label = st.selectbox("Επιλέξτε Προϊόν", options=list(product_display_options.keys()))
                chosen_product = product_display_options[selected_prod_label]
                
                curr_data = chosen_product["data"]
                curr_subcat = str(curr_data.get("product_subcategory", curr_data.get("Subcategory", "Kit"))).strip()
                if curr_subcat not in ["Kit", "Part"]: curr_subcat = "Kit"
                curr_name = str(curr_data.get("product_name", curr_data.get("Name", ""))).strip()
                try: curr_qty = int(curr_data.get("product_quantity", curr_data.get("Quantity", 0)))
                except: curr_qty = 0

                with st.form("edit_form"):
                    edit_subcategory = st.selectbox("Νέα Υποκατηγορία (product_subcategory)", options=["Kit", "Part"], index=["Kit", "Part"].index(curr_subcat))
                    edit_name = st.text_input("Νέο Όνομα Προϊόντος (product_name)", value=curr_name)
                    edit_qty = st.number_input("Νέα Τεμάχια (product_quantity)", min_value=0, value=curr_qty, step=1)
                    
                    edit_btn = st.form_submit_button("Οριστική Ενημέρωση")
                    
                    if edit_btn:
                        if edit_name.strip():
                            try:
                                sheet = get_products_sheet()
                                row_to_update = chosen_product["row_index"]
                                sheet.update_cell(row_to_update, 2, selected_edit_company)
                                sheet.update_cell(row_to_update, 3, edit_subcategory)
                                sheet.update_cell(row_to_update, 4, edit_name.strip())
                                sheet.update_cell(row_to_update, 5, edit_qty)
                                st.success("Το προϊόν ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                            except Exception as e:
                                st.error(f"Σφάλμα ενημέρωσης: {e}")
                        else:
                            st.warning("Το όνομα προϊόντος είναι υποχρεωτικό.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ε: ΔΙΑΧΕΙΡΙΣΗ ΚΑΤΕΣΤΡΑΜΜΕΝΩΝ (db_broken)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "broken":
        st.subheader("⚠️ Διαχείριση Κατεστραμμένων Προϊόντων")
        
        tab_broken_add, tab_broken_edit = st.tabs(["➕ Νέα Καταχώριση Κατεστραμμένων", "✏️ Τροποποίηση / Διόρθωση Κατεστραμμένων"])

        company_options = []
        product_records = []
        try:
            c_records = get_company_records()
            for r in c_records:
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_name and c_name not in company_options:
                    company_options.append(c_name)
            company_options = sorted(company_options)
            product_records = get_products_records()
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

        with tab_broken_add:
            if not company_options or not product_records:
                st.warning("Δεν βρέθηκαν καταχωρημένες κατηγορίες ή προϊόντα.")
            else:
                selected_b_company = st.selectbox("Επιλέξτε Κατηγορία", options=company_options, key="b_comp")
                
                filtered_products = []
                for r in product_records:
                    comp = str(r.get("product_company", r.get("Company", ""))).strip()
                    if comp == selected_b_company:
                        p_id = str(r.get("product_id", r.get("Product ID", r.get("id", "")))).strip()
                        p_sub = str(r.get("product_subcategory", r.get("Subcategory", ""))).strip()
                        p_name = str(r.get("product_name", r.get("Name", ""))).strip()
                        try: p_qty = int(r.get("product_quantity", r.get("Quantity", 0)))
                        except: p_qty = 0
                        filtered_products.append({"id": p_id, "subcategory": p_sub, "name": p_name, "quantity": p_qty})

                filtered_products = sorted(filtered_products, key=lambda x: x["name"])
                product_display_options = {f"[{p['subcategory']}] {p['name']} (ID: {p['id']} - Διαθέσιμα: {p['quantity']})": p for p in filtered_products}

                if not product_display_options:
                    st.info(f"Δεν υπάρχουν προϊόντα για την κατηγορία '{selected_b_company}'.")
                else:
                    selected_b_prod_label = st.selectbox("Επιλέξτε Προϊόν", options=list(product_display_options.keys()), key="b_prod")
                    chosen_b_prod = product_display_options[selected_b_prod_label]

                    with st.form("broken_form"):
                        broken_qty = st.number_input("Κατεστραμμένα Τεμάχια", min_value=0, max_value=chosen_b_prod["quantity"], step=1)
                        submit_broken = st.form_submit_button("Καταχώριση Κατεστραμμένων")
                        
                        if submit_broken:
                            if broken_qty > 0:
                                try:
                                    operation_result = chosen_b_prod["quantity"] - broken_qty
                                    b_sheet = get_broken_sheet()
                                    b_sheet.append_row([
                                        chosen_b_prod["id"],
                                        selected_b_company,
                                        chosen_b_prod["subcategory"],
                                        chosen_b_prod["name"],
                                        broken_qty,
                                        operation_result
                                    ])
                                    st.success(f"Καταγράφηκαν {broken_qty} κατεστραμμένα τεμάχια. Υπόλοιπο λειτουργικά: {operation_result}.")
                                except Exception as e:
                                    st.error(f"Σφάλμα αποθήκευσης: {e}")
                            else:
                                st.warning("Παρακαλώ εισάγετε αριθμό μεγαλύτερο του 0.")

        with tab_broken_edit:
            try:
                b_records = get_broken_records()
            except Exception as e:
                b_records = []

            if not b_records:
                st.info("Δεν υπάρχουν καταχωρημένα κατεστραμμένα προϊόντα προς τροποποίηση.")
            else:
                broken_options = []
                for idx, br in enumerate(b_records):
                    br_id = str(br.get("broken_id", br.get("ID", ""))).strip()
                    br_comp = str(br.get("broken_company", br.get("Company", ""))).strip()
                    br_name = str(br.get("broken_name", br.get("Name", ""))).strip()
                    br_qty = br.get("broken_quantity", br.get("Quantity", 0))
                    broken_options.append({
                        "label": f"[{br_comp}] {br_name} (ID: {br_id} - Κατεστραμμένα: {br_qty})",
                        "row_index": idx + 2,
                        "data": br
                    })

                broken_options = sorted(broken_options, key=lambda x: x["label"])
                broken_options_dict = {item["label"]: item for item in broken_options}

                selected_br_label = st.selectbox("Επιλέξτε Καταχώριση Κατεστραμμένων προς Διόρθωση", options=list(broken_options_dict.keys()))
                chosen_br_item = broken_options_dict[selected_br_label]
                br_data = chosen_br_item["data"]

                try: curr_br_qty = int(br_data.get("broken_quantity", br_data.get("Quantity", 0)))
                except: curr_br_qty = 0

                with st.form("broken_edit_form"):
                    new_broken_qty = st.number_input("Διορθωμένα Κατεστραμμένα Τεμάχια", min_value=0, value=curr_br_qty, step=1)
                    edit_broken_submit = st.form_submit_button("Οριστική Ενημέρωση Κατεστραμμένων")

                    if edit_broken_submit:
                        try:
                            row_to_up = chosen_br_item["row_index"]
                            b_sheet = get_broken_sheet()
                            b_sheet.update_cell(row_to_up, 5, new_broken_qty)
                            st.success(f"Η εγγραφή ενημερώθηκε σε {new_broken_qty} τεμάχια!")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Θ: ΔΑΝΕΙΣΜΟΣ ΕΞΟΠΛΙΣΜΟΥ (db_loans)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "loans":
        st.subheader("🤝 Δανεισμός & Επιστροφή Εξοπλισμού")

        tab_borrow, tab_return, tab_edit_loan = st.tabs(["📝 Καταγραφή Νέου Δανεισμού", "↩️ Επιστροφή / Ενεργοί Δανεισμοί", "✏️ Τροποποίηση Δανεισμού"])

        with tab_borrow:
            try:
                product_records = get_products_records()
            except Exception as e:
                product_records = []

            if not product_records:
                st.warning("Δεν βρέθηκαν διαθέσιμα προϊόντα.")
            else:
                formatted_products = []
                for r in product_records:
                    p_comp = str(r.get("product_company", r.get("Company", ""))).strip()
                    p_name = str(r.get("product_name", r.get("Name", ""))).strip()
                    p_id = str(r.get("product_id", r.get("Product ID", r.get("id", "")))).strip()
                    label = f"[{p_comp}] {p_name} (ID: {p_id})"
                    formatted_products.append({"label": label, "data": r})

                formatted_products = sorted(formatted_products, key=lambda x: x["label"])
                prod_options = {item["label"]: item["data"] for item in formatted_products}

                selected_prod_label = st.selectbox("Επιλέξτε Προϊόν για Δανεισμό", options=list(prod_options.keys()), key="l_prod")
                chosen_p = prod_options[selected_prod_label]
                
                borrower_name = st.text_input("Όνομα Δανειζόμενου (Μέλους Ομάδας)", key="l_borrower")
                quantity_borrowed = st.number_input("Ποσότητα Δανεισμού", min_value=1, step=1, key="l_qty")
                
                loan_submit = st.button("Καταχώριση Δανεισμού", type="primary", use_container_width=True, key="l_sub")

                if loan_submit:
                    if borrower_name.strip() and quantity_borrowed > 0:
                        try:
                            l_sheet = get_loans_sheet()
                            l_records = get_loans_records()
                            next_loan_id = len(l_records) + 1 if l_records else 1
                            
                            prod_name_val = str(chosen_p.get("product_name", chosen_p.get("Name", ""))).strip()
                            loan_date_val = str(datetime.date.today())
                            status_val = "Ενεργός Δανεισμός"
                            return_date_val = "-"

                            l_sheet.append_row([
                                next_loan_id,
                                prod_name_val,
                                borrower_name.strip(),
                                loan_date_val,
                                quantity_borrowed,
                                status_val,
                                return_date_val
                            ])
                            st.success("Ο δανεισμός καταγράφηκε επιτυχώς!")
                        except Exception as e:
                            st.error(f"Σφάλμα καταγραφής: {e}")
                    else:
                        st.warning("Συμπληρώστε το όνομα του δανειζόμενου και έγκυρη ποσότητα.")

        with tab_return:
            st.write("Ενεργοί Δανεισμοί που εκκρεμούν προς επιστροφή:")
            try:
                l_records = get_loans_records()
                active_loans = []
                for idx, r in enumerate(l_records):
                    status = str(r.get("status", r.get("Status", ""))).strip()
                    if status == "Ενεργός Δανεισμός":
                        p_name = str(r.get("product_name", r.get("Product Name", ""))).strip()
                        borrower = str(r.get("borrower_name", r.get("Borrower", ""))).strip()
                        l_id = str(r.get("loan_id", r.get("ID", ""))).strip()
                        active_loans.append({
                            "label": f"Δανεισμός ID: {l_id} | Προϊόν: {p_name} | Δανειζόμενος: {borrower}",
                            "row_index": idx + 2,
                            "data": r
                        })

                active_loans = sorted(active_loans, key=lambda x: x["label"])
                active_options = {item["label"]: item for item in active_loans}

                if not active_options:
                    st.info("Δεν υπάρχουν ενεργοί δανεισμοί αυτή τη στιγμή.")
                else:
                    selected_active_label = st.selectbox("Επιλέξτε Δανεισμό προς Επιστροφή", options=list(active_options.keys()), key="ret_sel")
                    chosen_loan = active_options[selected_active_label]
                    
                    return_submit = st.button("Καταχώριση Επιστροφής", type="primary", use_container_width=True, key="ret_sub")

                    if return_submit:
                        try:
                            l_sheet = get_loans_sheet()
                            row_to_up = chosen_loan["row_index"]
                            today_str = str(datetime.date.today())
                            l_sheet.update_cell(row_to_up, 6, "Επιστράφηκε")
                            l_sheet.update_cell(row_to_up, 7, today_str)
                            st.success("Η επιστροφή καταχωρήθηκε!")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης: {e}")
            except Exception as e:
                st.error(f"Σφάλμα φόρτωσης δανείων: {e}")

        with tab_edit_loan:
            st.write("Διόρθωση στοιχείων ενεργού δανεισμού:")
            try:
                l_records = get_loans_records()
                product_records = get_products_records()
            except Exception as e:
                l_records = []
                product_records = []

            active_loans_edit = []
            for idx, r in enumerate(l_records):
                status = str(r.get("status", r.get("Status", ""))).strip()
                if status == "Ενεργός Δανεισμός":
                    p_name = str(r.get("product_name", r.get("Product Name", ""))).strip()
                    borrower = str(r.get("borrower_name", r.get("Borrower", ""))).strip()
                    l_id = str(r.get("loan_id", r.get("ID", ""))).strip()
                    active_loans_edit.append({
                        "label": f"Δανεισμός ID: {l_id} | Προϊόν: {p_name} | Δανειζόμενος: {borrower}",
                        "row_index": idx + 2,
                        "data": r
                    })

            if not active_loans_edit:
                st.info("Δεν υπάρχουν ενεργοί δανεισμοί προς τροποποίηση.")
            else:
                active_loans_edit = sorted(active_loans_edit, key=lambda x: x["label"])
                edit_loan_options = {item["label"]: item for item in active_loans_edit}

                selected_edit_loan_label = st.selectbox("Επιλέξτε Δανεισμό προς Τροποποίηση", options=list(edit_loan_options.keys()), key="edit_loan_sel")
                chosen_edit_loan = edit_loan_options[selected_edit_loan_label]
                loan_row_data = chosen_edit_loan["data"]
                loan_row_idx = chosen_edit_loan["row_index"]

                formatted_products_edit = []
                for p in product_records:
                    p_comp = str(p.get("product_company", p.get("Company", ""))).strip()
                    p_name = str(p.get("product_name", p.get("Name", ""))).strip()
                    label = f"[{p_comp}] {p_name}"
                    formatted_products_edit.append({"label": label, "name": p_name})

                formatted_products_edit = sorted(formatted_products_edit, key=lambda x: x["label"])
                
                # Δημιουργία λίστας labels και αντιστοίχιση με τα ονόματα των προϊόντων
                product_labels_sorted = [item["label"] for item in formatted_products_edit]
                product_names_sorted = [item["name"] for item in formatted_products_edit]

                curr_prod = str(loan_row_data.get("product_name", loan_row_data.get("Product Name", ""))).strip()
                curr_borrower = str(loan_row_data.get("borrower_name", loan_row_data.get("Borrower", "")))
                try: curr_lqty = int(loan_row_data.get("quantity_borrowed", loan_row_data.get("Quantity", 1)))
                except: curr_lqty = 1

                # Βρίσκουμε το σωστό label με βάση το curr_prod
                default_label_idx = 0
                for i, name_val in enumerate(product_names_sorted):
                    if name_val == curr_prod:
                        default_label_idx = i
                        break

                selected_edit_label = st.selectbox("Διόρθωση Είδους Προϊόντος", options=product_labels_sorted, index=default_label_idx, key=f"edit_plabel_{loan_row_idx}")
                edit_prod_name = product_names_sorted[product_labels_sorted.index(selected_edit_label)]

                edit_borrower_name = st.text_input("Διόρθωση Ονόματος Δανειζόμενου", value=curr_borrower, key=f"edit_bname_{loan_row_idx}")
                edit_loan_qty = st.number_input("Διόρθωση Ποσότητας Δανεισμού", min_value=1, value=curr_lqty, step=1, key=f"edit_lqty_{loan_row_idx}")

                update_loan_btn = st.button("Οριστική Ενημέρωση Δανεισμού", type="primary", use_container_width=True, key=f"edit_lsub_{loan_row_idx}")

                if update_loan_btn:
                    try:
                        l_sheet = get_loans_sheet()
                        l_sheet.update_cell(loan_row_idx, 2, edit_prod_name)
                        l_sheet.update_cell(loan_row_idx, 3, edit_borrower_name.strip())
                        l_sheet.update_cell(loan_row_idx, 5, edit_loan_qty)
                        st.success("Ο δανεισμός ενημερώθηκε επιτυχώς!")
                    except Exception as e:
                        st.error(f"Σφάλμα ενημέρωσης: {e}")
                        
    # ------------------------------------------
    # ΣΕΛΙΔΑ J: ΚΑΤΑΣΚΕΥΗ ΡΟΜΠΟΤ (db_robots με robot_type στη στήλη B)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "robot_build":
        st.subheader("🤖 Κατασκευή Νέου Ρομπότ")

        try:
            product_records = get_products_records()
        except Exception as e:
            product_records = []

        if not product_records:
            st.warning("Δεν βρέθηκαν προϊόντα στην αποθήκη.")
        else:
            formatted_products = []
            for r in product_records:
                p_comp = str(r.get("product_company", r.get("Company", ""))).strip()
                p_name = str(r.get("product_name", r.get("Name", ""))).strip()
                label = f"[{p_comp}] {p_name}"
                formatted_products.append({"label": label, "name": p_name})

            formatted_products = sorted(formatted_products, key=lambda x: x["label"])
            product_names_sorted = [item["name"] for item in formatted_products]
            product_labels_sorted = [""] + [item["label"] for item in formatted_products]

            robot_type = st.text_input("Είδος Ρομπότ", key="b_rtype")
            operator_name = st.text_input("Όνομα Χειριστή", key="b_op")
            robot_name = st.text_input("Όνομα Ρομπότ (π.χ. KAGE)", key="b_rname")

            board_label = st.selectbox("Πλακέτα", options=product_labels_sorted, key="b_board")
            board = product_names_sorted[product_labels_sorted.index(board_label) - 1] if board_label else ""
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                s1_label = st.selectbox("Τύπος Αισθητήρων (Είδος 1)", options=product_labels_sorted, key="b_s1")
                sensor1 = product_names_sorted[product_labels_sorted.index(s1_label) - 1] if s1_label else ""
            with col_s2:
                sensor1_qty = st.number_input("Ποσότητα Είδους 1", min_value=0, step=1, value=1, key="b_s1_q")
            with col_s3:
                s2_label = st.selectbox("Τύπος Αισθητήρων (Είδος 2)", options=product_labels_sorted, key="b_s2")
                sensor2 = product_names_sorted[product_labels_sorted.index(s2_label) - 1] if s2_label else ""
            with col_s4:
                sensor2_qty = st.number_input("Ποσότητα Είδους 2", min_value=0, step=1, key="b_s2_q")

            batt_label = st.selectbox("Μπαταρία", options=product_labels_sorted, key="b_batt")
            battery = product_names_sorted[product_labels_sorted.index(batt_label) - 1] if batt_label else ""
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                mot_label = st.selectbox("Κινητήρες", options=product_labels_sorted, key="b_mot")
                motors = product_names_sorted[product_labels_sorted.index(mot_label) - 1] if mot_label else ""
            with col_m2:
                motors_qty = st.number_input("Ποσότητα Κινητήρων", min_value=0, step=1, key="b_mot_q")

            col_w1, col_w2 = st.columns(2)
            with col_w1:
                wh_label = st.selectbox("Ρόδες", options=product_labels_sorted, key="b_wh")
                wheels = product_names_sorted[product_labels_sorted.index(wh_label) - 1] if wh_label else ""
            with col_w2:
                wheels_qty = st.number_input("Ποσότητα Ρόδων", min_value=0, step=1, key="b_wh_q")

            chassis = st.text_input("Σασί (Πλαίσιο - Ελεύθερο κείμενο)", key="b_ch")

            st.markdown("---")
            st.subheader("🔌 Open Source / Extra Υλικά (Καλώδια, Αντάπτορες, Drivers, Πυκνωτές, Αντιστάσεις, Buttons κ.λπ.)")
            
            selected_extra_labels = st.multiselect("Επιλέξτε επιπλέον υλικά από την αποθήκη:", options=product_labels_sorted[1:], key="build_extras_multi")
            
            extra_qtys = {}
            if selected_extra_labels:
                st.markdown("**Ορίστε τεμάχια για καθένα από τα επιλεγμένα extra υλικά:**")
                cols_ex = st.columns(2)
                for idx, ex_label in enumerate(selected_extra_labels):
                    ex_name = product_names_sorted[product_labels_sorted.index(ex_label) - 1]
                    with cols_ex[idx % 2]:
                        extra_qtys[ex_name] = st.number_input(f"Τεμάχια για «{ex_label}»", min_value=1, step=1, value=1, key=f"build_ex_qty_{ex_name}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            build_submit = st.button("Οριστική Κατασκευή Ρομπότ", type="primary", use_container_width=True)

            if build_submit:
                if robot_type.strip() and operator_name.strip() and robot_name.strip():
                    try:
                        r_sheet = get_robots_sheet()
                        r_records = get_robots_records()
                        next_robot_id = len(r_records) + 1 if r_records else 1

                        extra_parts_str = ", ".join([f"{ex}:{extra_qtys[ex]}" for ex in extra_qtys])

                        # Σειρά στηλών: robot_id, robot_type, operator_name, robot_name, board, sensor1, sensor1_qty, sensor2, sensor2_qty, battery, motors, motors_qty, wheels, wheels_qty, chassis, extra_parts, status
                        r_sheet.append_row([
                            next_robot_id,
                            robot_type.strip(),
                            operator_name.strip(),
                            robot_name.strip(),
                            board,
                            sensor1,
                            sensor1_qty,
                            sensor2,
                            sensor2_qty,
                            battery,
                            motors,
                            motors_qty,
                            wheels,
                            wheels_qty,
                            chassis.strip(),
                            extra_parts_str,
                            "Ενεργό"
                        ])
                        st.success(f"Το ρομπότ '{robot_name}' κατασκευάστηκε επιτυχώς!")
                    except Exception as e:
                        st.error(f"Σφάλμα αποθήκευσης: {e}")
                else:
                    st.warning("Συμπληρώστε το είδος, το όνομα χειριστή και το όνομα του ρομπότ.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ K: ΕΠΕΞΕΡΓΑΣΙΑ / ΑΛΛΑΓΗ ΕΞΑΡΤΗΜΑΤΩΝ ΡΟΜΠΟΤ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "robot_edit":
        st.subheader("✏️ Επεξεργασία & Αλλαγή Εξαρτημάτων Ρομπότ")

        try:
            r_records = get_robots_records()
            product_records = get_products_records()
        except Exception as e:
            r_records, product_records = [], []

        if not r_records:
            st.info("Δεν βρέθηκαν καταχωρημένα ρομπότ.")
        else:
            active_robots = []
            for idx, r in enumerate(r_records):
                status = str(r.get("status", r.get("Status", "Ενεργό"))).strip()
                if status != "Διαλυμένο":
                    active_robots.append({"row_index": idx + 2, "data": r})

            if not active_robots:
                st.info("Δεν υπάρχουν ενεργά ρομπότ προς επεξεργασία.")
            else:
                robot_options = {f"ID: {r['data'].get('robot_id', r['data'].get('ID',''))} | Ρομπότ: {r['data'].get('robot_name', r['data'].get('Robot Name',''))} (Χειριστής: {r['data'].get('operator_name', r['data'].get('Operator',''))})": r for r in active_robots}

                selected_robot_label = st.selectbox("Επιλέξτε Ρομπότ προς Τροποποίηση", options=list(robot_options.keys()))
                chosen_robot = robot_options[selected_robot_label]
                r_data = chosen_robot["data"]
                r_idx = chosen_robot["row_index"]

                formatted_products = []
                for p in product_records:
                    p_comp = str(p.get("product_company", p.get("Company", ""))).strip()
                    p_name = str(p.get("product_name", p.get("Name", ""))).strip()
                    label = f"[{p_comp}] {p_name}"
                    formatted_products.append({"label": label, "name": p_name})

                formatted_products = sorted(formatted_products, key=lambda x: x["label"])
                product_names_sorted = [item["name"] for item in formatted_products]
                product_labels_sorted = [""] + [item["label"] for item in formatted_products]

                def get_index(val):
                    if val in product_names_sorted:
                        return product_names_sorted.index(val) + 1
                    return 0

                existing_extras = {}
                curr_extra_str = str(r_data.get("extra_parts", "")).strip()
                if curr_extra_str:
                    for part in curr_extra_str.split(","):
                        if ":" in part:
                            pn, pq = part.split(":", 1)
                            try: existing_extras[pn.strip()] = int(pq.strip())
                            except: existing_extras[pn.strip()] = 1

                curr_rtype = str(r_data.get("robot_type", r_data.get("Robot Type", ""))).strip()
                edit_robot_type = st.text_input("Διόρθωση Είδους Ρομπότ", value=curr_rtype, key=f"ed_rtype_{r_idx}")
                edit_operator = st.text_input("Νέο Όνομα Χειριστή", value=str(r_data.get("operator_name", r_data.get("Operator", ""))), key=f"ed_op_{r_idx}")
                edit_robot_name = st.text_input("Νέο Όνομα Ρομπότ", value=str(r_data.get("robot_name", r_data.get("Robot Name", ""))), key=f"ed_rn_{r_idx}")

                curr_board = str(r_data.get("board", ""))
                edit_board_label = st.selectbox("Πλακέτα", options=product_labels_sorted, index=get_index(curr_board), key=f"ed_bd_{r_idx}")
                edit_board = product_names_sorted[product_labels_sorted.index(edit_board_label) - 1] if edit_board_label else ""

                curr_s1 = str(r_data.get("sensor1", ""))
                try: curr_s1_qty = int(r_data.get("sensor1_qty", 1))
                except: curr_s1_qty = 1

                curr_s2 = str(r_data.get("sensor2", ""))
                try: curr_s2_qty = int(r_data.get("sensor2_qty", 1))
                except: curr_s2_qty = 1

                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    edit_s1_label = st.selectbox("Τύπος Αισθητήρων (Είδος 1)", options=product_labels_sorted, index=get_index(curr_s1), key=f"ed_s1_{r_idx}")
                    edit_sensor1 = product_names_sorted[product_labels_sorted.index(edit_s1_label) - 1] if edit_s1_label else ""
                with col_s2:
                    edit_sensor1_qty = st.number_input("Ποσότητα Είδους 1", min_value=0, value=curr_s1_qty, step=1, key=f"ed_s1q_{r_idx}")
                with col_s3:
                    edit_s2_label = st.selectbox("Τύπος Αισθητήρων (Είδος 2)", options=product_labels_sorted, index=get_index(curr_s2), key=f"ed_s2_{r_idx}")
                    edit_sensor2 = product_names_sorted[product_labels_sorted.index(edit_s2_label) - 1] if edit_s2_label else ""
                with col_s4:
                    edit_sensor2_qty = st.number_input("Ποσότητα Είδους 2", min_value=0, value=curr_s2_qty, step=1, key=f"ed_s2q_{r_idx}")

                curr_batt = str(r_data.get("battery", ""))
                edit_batt_label = st.selectbox("Μπαταρία", options=product_labels_sorted, index=get_index(curr_batt), key=f"ed_bt_{r_idx}")
                edit_battery = product_names_sorted[product_labels_sorted.index(edit_batt_label) - 1] if edit_batt_label else ""

                curr_motors = str(r_data.get("motors", ""))
                try: curr_mqty = int(r_data.get("motors_qty", 0))
                except: curr_mqty = 0

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    edit_mot_label = st.selectbox("Κινητήρες", options=product_labels_sorted, index=get_index(curr_motors), key=f"ed_mot_{r_idx}")
                    edit_motors = product_names_sorted[product_labels_sorted.index(edit_mot_label) - 1] if edit_mot_label else ""
                with col_m2:
                    edit_motors_qty = st.number_input("Ποσότητα Κινητήρων", min_value=0, value=curr_mqty, step=1, key=f"ed_motq_{r_idx}")

                curr_wheels = str(r_data.get("wheels", ""))
                try: curr_wqty = int(r_data.get("wheels_qty", 0))
                except: curr_wqty = 0

                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    edit_wh_label = st.selectbox("Ρόδες", options=product_labels_sorted, index=get_index(curr_wheels), key=f"ed_wh_{r_idx}")
                    edit_wheels = product_names_sorted[product_labels_sorted.index(edit_wh_label) - 1] if edit_wh_label else ""
                with col_w2:
                    edit_wheels_qty = st.number_input("Ποσότητα Ρόδων", min_value=0, value=curr_wqty, step=1, key=f"ed_whq_{r_idx}")

                curr_chassis = str(r_data.get("chassis", ""))
                edit_chassis = st.text_input("Σασί (Πλαίσιο - Ελεύθερο κείμενο)", value=curr_chassis, key=f"ed_ch_{r_idx}")

                st.markdown("---")
                st.subheader("🔌 Open Source / Extra Υλικά (Επεξεργασία)")
                
                default_selected_labels = []
                for k in existing_extras.keys():
                    match_item = next((item for item in formatted_products if item["name"] == k), None)
                    if match_item:
                        default_selected_labels.append(match_item["label"])

                edit_selected_labels = st.multiselect("Επιλέξτε επιπλέον υλικά από την αποθήκη:", options=product_labels_sorted[1:], default=default_selected_labels, key=f"edit_extras_multi_{r_idx}")
                
                edit_extra_qtys = {}
                if edit_selected_labels:
                    st.markdown("**Ορίστε τεμάχια για καθένα από τα επιλεγμένα extra υλικά:**")
                    cols_ed_ex = st.columns(2)
                    for idx, ex_label in enumerate(edit_selected_labels):
                        ex_name = product_names_sorted[product_labels_sorted.index(ex_label) - 1]
                        default_val = existing_extras.get(ex_name, 1)
                        with cols_ed_ex[idx % 2]:
                            edit_extra_qtys[ex_name] = st.number_input(f"Τεμάχια για «{ex_label}»", min_value=1, step=1, value=default_val, key=f"edit_ex_qty_{r_idx}_{ex_name}")

                st.markdown("<br>", unsafe_allow_html=True)
                edit_submit = st.button("Οριστική Ενημέρωση Ρομπότ", type="primary", use_container_width=True)

                if edit_submit:
                    try:
                        r_sheet = get_robots_sheet()
                        row_idx = chosen_robot["row_index"]

                        edit_extra_parts_str = ", ".join([f"{ex}:{edit_extra_qtys[ex]}" for ex in edit_extra_qtys])

                        r_sheet.update_cell(row_idx, 2, edit_robot_type.strip())
                        r_sheet.update_cell(row_idx, 3, edit_operator.strip())
                        r_sheet.update_cell(row_idx, 4, edit_robot_name.strip())
                        r_sheet.update_cell(row_idx, 5, edit_board)
                        r_sheet.update_cell(row_idx, 6, edit_sensor1)
                        r_sheet.update_cell(row_idx, 7, edit_sensor1_qty)
                        r_sheet.update_cell(row_idx, 8, edit_sensor2)
                        r_sheet.update_cell(row_idx, 9, edit_sensor2_qty)
                        r_sheet.update_cell(row_idx, 10, edit_battery)
                        r_sheet.update_cell(row_idx, 11, edit_motors)
                        r_sheet.update_cell(row_idx, 12, edit_motors_qty)
                        r_sheet.update_cell(row_idx, 13, edit_wheels)
                        r_sheet.update_cell(row_idx, 14, edit_wheels_qty)
                        r_sheet.update_cell(row_idx, 15, edit_chassis.strip())
                        r_sheet.update_cell(row_idx, 16, edit_extra_parts_str)

                        st.success("Το ρομπότ ενημερώθηκε επιτυχώς!")
                    except Exception as e:
                        st.error(f"Σφάλμα ενημέρωσης: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ L: ΛΙΣΤΑ ΡΟΜΠΟΤ (Εμφάνιση Είδος Ρομπότ)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "robot_list":
        st.subheader("📋 Λίστα Κατασκευασμένων Ρομπότ")

        try:
            r_records = get_robots_records()
            robot_list_data = []
            for r in r_records:
                r_id = str(r.get("robot_id", r.get("ID", ""))).strip()
                r_type = str(r.get("robot_type", r.get("Robot Type", ""))).strip()
                op_name = str(r.get("operator_name", r.get("Operator", ""))).strip()
                r_name = str(r.get("robot_name", r.get("Robot Name", ""))).strip()
                board = str(r.get("board", r.get("Board", ""))).strip()
                
                s1 = str(r.get("sensor1", "")).strip()
                try: s1_q = int(r.get("sensor1_qty", 1))
                except: s1_q = 1

                s2 = str(r.get("sensor2", "")).strip()
                try: s2_q = int(r.get("sensor2_qty", 0))
                except: s2_q = 0

                s_types = f"{s1} (x{s1_q})"
                if s2: s_types += f", {s2} (x{s2_q})"

                batt = str(r.get("battery", r.get("Battery", ""))).strip()
                motors = f"{r.get('motors', '')} ({r.get('motors_qty', 0)})".strip()
                wheels = f"{r.get('wheels', '')} ({r.get('wheels_qty', 0)})".strip()
                chassis = str(r.get("chassis", r.get("Chassis", ""))).strip()
                extras = str(r.get("extra_parts", "")).strip()
                status = str(r.get("status", r.get("Status", "Ενεργό"))).strip()

                robot_list_data.append({
                    "ID": r_id,
                    "ΕΙΔΟΣ ΡΟΜΠΟΤ": r_type,
                    "ΧΕΙΡΙΣΤΗΣ": op_name,
                    "ΟΝΟΜΑ ΡΟΜΠΟΤ": r_name,
                    "ΠΛΑΚΕΤΑ": board,
                    "ΑΙΣΘΗΤΗΡΕΣ": s_types,
                    "ΜΠΑΤΑΡΙΑ": batt,
                    "ΚΙΝΗΤΗΡΕΣ": motors,
                    "ΡΟΔΕΣ": wheels,
                    "ΣΑΣΙ": chassis,
                    "EXTRA ΥΛΙΚΑ": extras,
                    "ΚΑΤΑΣΤΑΣΗ": status
                })

            if robot_list_data:
                df_robots = pd.DataFrame(robot_list_data)
                st.dataframe(df_robots, use_container_width=True, hide_index=True)
            else:
                st.info("Δεν βρέθηκαν καταχωρημένα ρομπότ.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ι: ΛΙΣΤΑ ΕΝΕΡΓΩΝ ΔΑΝΕΙΣΜΩΝ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "active_loans_list":
        st.subheader("📋 Λίστα Ενεργών Δανεισμών")
        
        try:
            l_records = get_loans_records()
            active_list_data = []
            for r in l_records:
                status = str(r.get("status", r.get("Status", ""))).strip()
                if status == "Ενεργός Δανεισμός":
                    l_id = str(r.get("loan_id", r.get("ID", ""))).strip()
                    p_name = str(r.get("product_name", r.get("Product Name", ""))).strip()
                    borrower = str(r.get("borrower_name", r.get("Borrower", ""))).strip()
                    l_date = str(r.get("loan_date", r.get("Date", ""))).strip()
                    try: l_qty = int(r.get("quantity_borrowed", r.get("Quantity", 0)))
                    except: l_qty = 0
                    
                    active_list_data.append({
                        "ID ΔΑΝΕΙΣΜΟΥ": l_id,
                        "ΟΝΟΜΑ ΠΡΟΪΟΝΤΟΣ": p_name,
                        "ΔΑΝΕΙΖΟΜΕΝΟΣ": borrower,
                        "ΗΜΕΡΟΜΗΝΙΑ ΔΑΝΕΙΣΜΟΥ": l_date,
                        "ΤΕΜΑΧΙΑ": l_qty,
                        "ΚΑΤΑΣΤΑΣΗ": status
                    })

            if active_list_data:
                df_active_loans = pd.DataFrame(active_list_data)
                st.dataframe(df_active_loans, use_container_width=True, hide_index=True)
            else:
                st.info("Δεν βρέθηκαν ενεργοί δανεισμοί αυτή τη στιγμή.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Κ: ΛΙΣΤΑ ΚΑΤΕΣΤΡΑΜΜΕΝΩΝ (db_broken)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "broken_list":
        st.subheader("📋 Λίστα Κατεστραμμένων Προϊόντων")
        
        try:
            b_records = get_broken_records()
            broken_list_data = []
            for r in b_records:
                b_id = str(r.get("broken_id", r.get("ID", ""))).strip()
                b_comp = str(r.get("broken_company", r.get("Company", ""))).strip()
                b_sub = str(r.get("broken_subcategory", r.get("Subcategory", ""))).strip()
                b_name = str(r.get("broken_name", r.get("Name", ""))).strip()
                try: b_qty = int(r.get("broken_quantity", r.get("Quantity", 0)))
                except: b_qty = 0
                try: op_val = int(r.get("operation", r.get("Operation", 0)))
                except: op_val = 0
                
                broken_list_data.append({
                    "ΚΩΔΙΚΟΣ": b_id,
                    "ΚΑΤΗΓΟΡΙΑ": b_comp,
                    "ΥΠΟΚΑΤΗΓΟΡΙΑ": b_sub,
                    "ΟΝΟΜΑ ΠΡΟΪΟΝΤΟΣ": b_name,
                    "ΚΑΤΕΣΤΡΑΜΜΕΝΑ ΤΕΜΑΧΙΑ": b_qty,
                    "ΥΠΟΛΟΙΠΟ ΛΕΙΤΟΥΡΓΙΚΩΝ": op_val
                })

            if broken_list_data:
                df_broken = pd.DataFrame(broken_list_data)
                st.dataframe(df_broken, use_container_width=True, hide_index=True)
            else:
                st.info("Η καρτέλα db_broken είναι προς το παρόν άδεια.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ ΣΤ: ΛΙΣΤΑ ΚΑΤΗΓΟΡΙΩΝ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list_company":
        st.subheader("📋 Λίστα Κατηγοριών")
        
        try:
            records = get_company_records()
            if records:
                df_company = pd.DataFrame(records)
                if df_company.shape[1] >= 2:
                    df_company = df_company.iloc[:, :2]
                    df_company.columns = ["ID", "ΕΠΩΝΥΜΙΑ"]
                st.dataframe(df_company, use_container_width=True, hide_index=True)
            else:
                st.info("Η καρτέλα DB_Company είναι προς το παρόν άδεια.")
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ζ: ΕΙΣΑΓΩΓΗ ΝΕΑΣ ΚΑΤΗΓΟΡΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "insert_company":
        st.subheader("➕ Φόρμα Εισαγωγής Νέας Κατηγορίας")
        
        try:
            records = get_company_records()
            if records:
                ids = []
                for r in records:
                    val = r.get("company_id", r.get("Company ID", len(ids) + 1))
                    try: ids.append(int(val))
                    except: pass
                next_id = max(ids) + 1 if ids else len(records) + 1
            else:
                next_id = 1
        except:
            next_id = 1

        st.info(f"Αυτόματο company_id που θα αποθηκευτεί: **{next_id}**")

        with st.form("insert_company_form"):
            company_name = st.text_input("Όνομα Κατηγορίας")
            insert_c_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_c_btn:
                if company_name.strip():
                    try:
                        c_sheet = get_company_sheet()
                        c_sheet.append_row([next_id, company_name.strip()])
                        st.success("Η κατηγορία αποθηκεύτηκε επιτυχώς!")
                    except Exception as e:
                        st.error(f"Σφάλμα αποθήκευσης: {e}")
                else:
                    st.warning("Το όνομα της κατηγορίας είναι υποχρεωτικό.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Η: ΕΠΕΞΕΡΓΑΣΙΑ ΚΑΤΗΓΟΡΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "edit_company":
        st.subheader("✏️ Φόρμα Επεξεργασίας Κατηγορίας")
        
        company_options = {}
        try:
            records = get_company_records()
            for r in records:
                c_id = str(r.get("company_id", r.get("Company ID", ""))).strip()
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_id:
                    company_options[f"ID: {c_id} - {c_name}"] = c_id
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης: {e}")

        if not company_options:
            st.warning("Δεν βρέθηκαν καταχωρημένες κατηγορίες στο tab DB_Company.")
        else:
            with st.form("edit_company_form"):
                selected_option = st.selectbox("Επιλέξτε Κατηγορία προς Τροποποίηση", options=list(company_options.keys()))
                new_c_name = st.text_input("Νέο Όνομα Κατηγορίας")
                
                edit_c_btn = st.form_submit_button("Οριστική Ενημέρωση")
                
                if edit_c_btn:
                    selected_id = company_options[selected_option]
                    if selected_id and new_c_name.strip():
                        try:
                            c_sheet = get_company_sheet()
                            cell = c_sheet.find(selected_id)
                            if cell:
                                c_sheet.update_cell(cell.row, 2, new_c_name.strip())
                                st.success("Η κατηγορία ενημερώθηκε επιτυχώς!")
                            else:
                                st.error("Δεν βρέθηκε η κατηγορία στο Google Sheet.")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης: {e}")
                    else:
                        st.warning("Συμπληρώστε το νέο όνομα της κατηγορίας.")














# ==========================================
# 3. ΠΕΡΙΒΑΛΛΟΝ TUTOR (AI_AGENT - ΚΛΕΙΔΩΜΕΝΟ)
# ==========================================
elif st.session_state.user_role == "tutor":

    st.title("AppIDE: LLM-Based Competitive Robotics Tutor")
    st.caption("Open-Hardware Competitive Robotics Learning Environment")

    # ------------------------------------------
    # ΦΟΡΤΩΣΗ ΕΡΕΥΝΗΤΙΚΩΝ ΑΡΧΕΙΩΝ
    # ------------------------------------------
    def load_research_file(filename, default_text):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        return default_text

    # ------------------------------------------
    # GROQ / GOOGLE SHEET
    # ------------------------------------------
    try:
        if "GROQ_API_KEY" in st.secrets:
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=st.secrets["GROQ_API_KEY"]
            )
        else:
            client = None
            st.error("Δεν βρέθηκε το GROQ_API_KEY στα Streamlit secrets.")

        DB_URL = st.secrets.get("GSHEET_URL", "")

    except Exception as e:
        client = None
        DB_URL = ""
        st.error(f"Config Error: {e}")

    # ------------------------------------------
    # CHAT HISTORY
    # ------------------------------------------
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ------------------------------------------
    # TABS
    # ------------------------------------------
    tab_ide, tab_config, tab_pre, tab_post, tab_exercises = st.tabs(
        ["AppIDE", "Help", "Pre Test", "Post Test", "Exercises"]
    )

    # ------------------------------------------
    # PRE TEST
    # ------------------------------------------
    with tab_pre:
        st.subheader("Αρχική Αξιολόγηση")

        pre_test_url = "https://forms.gle/wHkXG48y6xwWJV929"

        components.iframe(
            pre_test_url,
            height=800,
            scrolling=True
        )

    # ------------------------------------------
    # POST TEST
    # ------------------------------------------
    with tab_post:
        st.subheader("Τελική Αξιολόγηση")

        post_test_url = "https://forms.gle/V5AW1eTAFRHEiaBs5"

        components.iframe(
            post_test_url,
            height=800,
            scrolling=True
        )

    # ------------------------------------------
    # EXERCISES
    # ------------------------------------------
    with tab_exercises:
        st.subheader("Ασκήσεις Αθλητικής Ρομποτικής")

        st.text_area(
            "excersices.txt",
            load_research_file(
                "excersices.txt",
                "No exercises found."
            ),
            height=1200,
            disabled=True
        )

    # ------------------------------------------
    # HELP / CONFIGURATION
    # ------------------------------------------
    with tab_config:

        col_r, col_k, col_b = st.columns(3)

        with col_r:
            st.subheader("Rubric (L1-L5)")

            st.text_area(
                "rubric.txt",
                load_research_file(
                    "rubric.txt",
                    "No rubric found."
                ),
                height=500,
                disabled=True
            )

        with col_k:
            st.subheader("Competitive Robotics Knowledge Base")

            st.text_area(
                "knowledge.txt",
                load_research_file(
                    "knowledge.txt",
                    "No knowledge base found."
                ),
                height=500,
                disabled=True
            )

        with col_b:
            st.subheader("Tutor Behavior")

            st.text_area(
                "behavior.txt",
                load_research_file(
                    "behavior.txt",
                    "No behavior found."
                ),
                height=500,
                disabled=True
            )

    # ==========================================
    # MAIN IDE
    # ==========================================
    with tab_ide:

        col1, col2 = st.columns([1, 1])

        # ======================================
        # STUDENT INPUT
        # ======================================
        with col1:

            with st.form("input_form"):

                student_id = st.text_input(
                    "ID Μαθητή:",
                    "---"
                )

                # ----------------------------------
                # CATEGORY
                # ----------------------------------
                category = st.selectbox(
                    "Κατηγορία Αθλητικής Ρομποτικής:",
                    [
                        "Mini Sumo",
                        "Line Follower"
                    ]
                )

                # ----------------------------------
                # ROBOT
                # ----------------------------------
                if category == "Mini Sumo":
                    robot_options = [
                        "Custom Nano + TB6612",
                        "XMotion"
                    ]
                else:
                    robot_options = [
                        "Custom Nano + TB6612"
                    ]

                robot = st.selectbox(
                    "Robot:",
                    robot_options
                )

                # ----------------------------------
                # WORK TYPE
                # ----------------------------------
                work_type = st.selectbox(
                    "Τύπος εργασίας:",
                    [
                        "Ελεύθερη αλληλεπίδραση",
                        "Οργανωμένη άσκηση"
                    ]
                )

                # ----------------------------------
                # EXERCISE
                # ----------------------------------
                exercise = "FREE"

                if work_type == "Οργανωμένη άσκηση":

                    if category == "Mini Sumo":

                        exercise_options = [
                            "MS-01 - Opponent Detection",
                            "MS-02 - Basic Attack",
                            "MS-03 - Ring Edge Detection",
                            "MS-04 - Edge Avoidance",
                            "MS-05 - Search Strategy",
                            "MS-06 - Search, Attack and Escape",
                            "MS-07 - Debugging Mini Sumo Strategy"
                        ]

                    else:

                        exercise_options = [
                            "LF-01 - Line Detection",
                            "LF-02 - Basic Motor Correction",
                            "LF-03 - Two-Sensor Line Following",
                            "LF-04 - Speed and Stability",
                            "LF-05 - Proportional Control",
                            "LF-06 - PD/PID Line Following",
                            "LF-07 - Debugging Line-Following Algorithm"
                        ]

                    exercise = st.selectbox(
                        "Άσκηση:",
                        exercise_options
                    )

                # ----------------------------------
                # ACTION
                # ----------------------------------
                mode = st.radio(
                    "Ενέργεια:",
                    [
                        "Νέα_Εντολή",
                        "Διόρθωση"
                    ],
                    horizontal=True
                )

                # ----------------------------------
                # STUDENT PROMPT
                # ----------------------------------
                user_input = st.text_area(
                    "Κείμενο:",
                    height=180,
                    placeholder=(
                        "Περιέγραψε τι θέλεις να κάνει το ρομπότ, "
                        "ρώτησε κάτι ή περιέγραψε το πρόβλημα "
                        "που αντιμετωπίζεις..."
                    )
                )

                btn = st.form_submit_button(
                    "Εκτέλεση & Αποθήκευση"
                )

        # ======================================
        # AI RESPONSE
        # ======================================
        with col2:

            if btn and user_input:

                if client is None:
                    st.error("Δεν υπάρχει ενεργή σύνδεση με το Groq API.")
                    st.stop()

                # ----------------------------------
                # LOAD RESEARCH FILES
                # ----------------------------------
                my_rubric = load_research_file(
                    "rubric.txt",
                    "Categorize L1 to L5."
                )

                my_knowledge = load_research_file(
                    "knowledge.txt",
                    "Competitive robotics knowledge base."
                )

                my_behavior = load_research_file(
                    "behavior.txt",
                    "Be a professional competitive robotics educator."
                )

                # ----------------------------------
                # EXERCISE ID
                # ----------------------------------
                if work_type == "Οργανωμένη άσκηση":
                    exercise_id = exercise.split(" - ")[0]
                else:
                    exercise_id = "FREE"

                # ----------------------------------
                # ROBOT CONTEXT
                # ----------------------------------
                robot_context = f"""
CURRENT ROBOTICS CONTEXT

Category:
{category}

Robot:
{robot}

Work Type:
{work_type}

Exercise:
{exercise_id}

Action:
{mode}

Programming Environment:
Arduino / C++

IMPORTANT:
Use ONLY hardware information and programming interfaces
supported by the provided Knowledge Base.

Never invent:
- pins
- libraries
- sensor thresholds
- motor functions
- hardware capabilities
- electrical measurements
- competition rules
- experimental results
"""

                contextual_user_message = f"""
{robot_context}

STUDENT REQUEST:
{user_input}
"""

                # ==================================
                # 1. L1-L5 CLASSIFICATION
                # ==================================
                with st.spinner("Ανάλυση του αιτήματος..."):

                    try:

                        class_sys = f"""
You are an educational researcher studying
student interactions in competitive robotics.

Classify the student's request into exactly
one level using ONLY the following rubric:

{my_rubric}

Use the student's actual request as the main
basis for classification.

The selected exercise must NOT determine
the classification level.

Return ONLY one label:

L1
L2
L3
L4
or
L5
"""

                        class_res = client.chat.completions.create(
                            model="openai/gpt-oss-120b",
                            messages=[
                                {
                                    "role": "system",
                                    "content": class_sys
                                },
                                {
                                    "role": "user",
                                    "content": contextual_user_message
                                }
                            ]
                        )

                        auto_level = (
                            class_res
                            .choices[0]
                            .message
                            .content
                            .strip()
                        )

                        # ----------------------------------
                        # SAFETY FOR CLASSIFICATION OUTPUT
                        # ----------------------------------
                        level_match = re.search(
                            r'\bL[1-5]\b',
                            auto_level.upper()
                        )

                        if level_match:
                            auto_level = level_match.group(0)
                        else:
                            auto_level = "N/A"

                        # ==================================
                        # 2. COMPLETE TUTOR RESPONSE
                        # ==================================
                        tutor_sys = f"""{my_behavior}

==================================================
TECHNICAL KNOWLEDGE BASE
==================================================

{my_knowledge}

==================================================
CURRENT ROBOT CONFIGURATION
==================================================

{robot_context}

==================================================
INSTRUCTIONS
==================================================

You are an educational tutor for competitive robotics.

Follow the Tutor Behavior rules provided above.

Use the Technical Knowledge Base as the authoritative
technical source for the supported robots.

Use the Current Robot Configuration to determine which
technical profile is relevant.

Answer in Greek unless another language is explicitly requested.

Do not invent technical information that is not supported
by the Knowledge Base or by information supplied by the student.

If essential technical information is missing, state what
information is required instead of inventing it.

==================================================
RESPONSE FORMAT
==================================================

Return the answer using EXACTLY the following markers.

Do not use these markers anywhere else.

[ANALYSIS]
Explain what the student's request or problem means.
State only conclusions supported by the available information.

[CAUSES]
Give relevant possible causes.
Do not present possibilities as confirmed facts.
If possible causes are not relevant, write NONE.

[CHECKS]
Give practical diagnostic checks or steps when relevant.
If no checks are needed, write NONE.

[SOLUTIONS]
Give appropriate proposed solutions.
Explain briefly when each solution is appropriate.
If no solution can yet be selected, make that clear.

[CODE]
Provide Arduino C/C++ code only when useful and technically
supported by the selected robot profile and Knowledge Base.

Do NOT use Markdown code fences.

If code is not necessary or cannot safely be produced,
write exactly:
NONE

[MISSING]
List only information that is genuinely necessary to improve
or complete the answer.

If nothing else is required, write exactly:
NONE
"""

                        tutor_res = client.chat.completions.create(
                            model="openai/gpt-oss-120b",
                            messages=[
                                {
                                    "role": "system",
                                    "content": tutor_sys
                                },
                                {
                                    "role": "user",
                                    "content": contextual_user_message
                                }
                            ]
                        )

                        raw_answer = (
                            tutor_res
                            .choices[0]
                            .message
                            .content
                            .strip()
                        )

                        # ==================================
                        # 3. PARSE STRUCTURED RESPONSE
                        # ==================================
                        def extract_section(text, section, next_sections):
                            start_marker = f"[{section}]"

                            if start_marker not in text:
                                return ""

                            content = text.split(start_marker, 1)[1]

                            positions = []

                            for next_section in next_sections:
                                marker = f"[{next_section}]"
                                pos = content.find(marker)

                                if pos != -1:
                                    positions.append(pos)

                            if positions:
                                content = content[:min(positions)]

                            return content.strip()

                        analysis_text = extract_section(
                            raw_answer,
                            "ANALYSIS",
                            ["CAUSES", "CHECKS", "SOLUTIONS", "CODE", "MISSING"]
                        )

                        causes_text = extract_section(
                            raw_answer,
                            "CAUSES",
                            ["CHECKS", "SOLUTIONS", "CODE", "MISSING"]
                        )

                        checks_text = extract_section(
                            raw_answer,
                            "CHECKS",
                            ["SOLUTIONS", "CODE", "MISSING"]
                        )

                        solutions_text = extract_section(
                            raw_answer,
                            "SOLUTIONS",
                            ["CODE", "MISSING"]
                        )

                        code_text = extract_section(
                            raw_answer,
                            "CODE",
                            ["MISSING"]
                        )

                        missing_text = extract_section(
                            raw_answer,
                            "MISSING",
                            []
                        )

                        # ----------------------------------
                        # REMOVE POSSIBLE CODE FENCES
                        # ----------------------------------
                        code_text = re.sub(
                            r'```(?:cpp|c\+\+|c|arduino)?',
                            '',
                            code_text,
                            flags=re.IGNORECASE
                        ).replace(
                            '```',
                            ''
                        ).strip()

                        # ==================================
                        # 4. DISPLAY RESPONSE
                        # ==================================
                        st.markdown(
                            f"### Απάντηση — {category}"
                        )

                        st.caption(
                            f"{robot} | {exercise_id} | Επίπεδο: {auto_level}"
                        )

                        # ----------------------------------
                        # ANALYSIS
                        # ----------------------------------
                        if analysis_text and analysis_text.upper() != "NONE":

                            st.markdown("#### 🔍 Ανάλυση προβλήματος")
                            st.markdown(analysis_text)

                        # ----------------------------------
                        # POSSIBLE CAUSES
                        # ----------------------------------
                        if causes_text and causes_text.upper() != "NONE":

                            st.markdown("#### 💡 Πιθανές αιτίες")
                            st.markdown(causes_text)

                        # ----------------------------------
                        # CHECKS
                        # ----------------------------------
                        if checks_text and checks_text.upper() != "NONE":

                            st.markdown("#### 🔧 Τι να ελέγξεις")
                            st.markdown(checks_text)

                        # ----------------------------------
                        # SOLUTIONS
                        # ----------------------------------
                        if solutions_text and solutions_text.upper() != "NONE":

                            st.markdown("#### ✅ Προτεινόμενες λύσεις")
                            st.markdown(solutions_text)

                        # ----------------------------------
                        # CODE
                        # ----------------------------------
                        if code_text and code_text.upper() != "NONE":

                            st.markdown("#### 💻 Προτεινόμενος κώδικας")

                            st.code(
                                code_text,
                                language="cpp"
                            )

                        # ----------------------------------
                        # MISSING INFORMATION
                        # ----------------------------------
                        if missing_text and missing_text.upper() != "NONE":

                            st.markdown("#### 📌 Χρειάζομαι επιπλέον")

                            st.info(missing_text)

                        # ----------------------------------
                        # FALLBACK
                        # ----------------------------------
                        if not any([
                            analysis_text,
                            causes_text,
                            checks_text,
                            solutions_text,
                            code_text,
                            missing_text
                        ]):

                            st.markdown("#### Απάντηση")
                            st.markdown(raw_answer)

                        # ==================================
                        # 5. SAVE CHAT HISTORY
                        # ==================================
                        st.session_state.chat_history.append(
                            {
                                "role": "user",
                                "content": contextual_user_message
                            }
                        )

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": raw_answer
                            }
                        )

                        # ==================================
                        # 6. GOOGLE SHEET LOGGING
                        # ==================================
                        if DB_URL:

                            code_for_log = ""

                            if (
                                code_text
                                and code_text.upper() != "NONE"
                            ):
                                code_for_log = code_text.replace(
                                    '"',
                                    "'"
                                )

                            requests.post(
                                DB_URL,
                                json={
                                    "data": [
                                        {
                                            "Timestamp": str(
                                                datetime.datetime.now()
                                            ),
                                            "Student_ID": student_id,
                                            "Action": mode,
                                            "Coding_Level": auto_level,
                                            "Category": category,
                                            "Robot": robot,
                                            "Exercise_ID": exercise_id,
                                            "Prompt": user_input,
                                            "Code": code_for_log
                                        }
                                    ]
                                },
                                timeout=10
                            )

                    except Exception as e:

                        st.error(
                            f"Error: {e}"
                        )
