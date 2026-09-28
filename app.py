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


# ==========================================
# SIDEBAR: ΠΑΝΤΑ ΔΙΑΘΕΣΙΜΑ ΚΟΥΜΠΙΑ ΨΗΛΑ
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Γενικός Έλεγχος")
    
    # 1. Κουμπί Ανανέωσης Δεδομένων (Καθαρισμός cache)
    if st.button("🔄 Ανανέωση Δεδομένων", use_container_width=True):
        st.cache_resource.clear()
        st.success("Η μνήμη ανανεώθηκε!")
        st.rerun()

    # 2. Κουμπί Επιστροφή στο Μενού (αν δεν είμαστε ήδη στο μενού)
    if st.session_state.user_role == "admin" and st.session_state.admin_subpage != "menu":
        if st.button("🏠 Επιστροφή στο Μενού", use_container_width=True):
            st.session_state.admin_subpage = "menu"
            st.rerun()

    st.markdown("---")
    
    # 3. Κουμπί Αποσύνδεσης
    if st.button("🚪 Αποσύνδεση", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.admin_subpage = "menu"
        st.rerun()


# ==========================================
# 2. ΠΕΡΙΒΑΛΛΟΝ ΔΙΑΧΕΙΡΙΣΤΗ (ADMIN / DB_ROBOTICS)
# ==========================================
if st.session_state.user_role == "admin":
    
    # Κεντρικός τίτλος ενότητας (ΚΛΕΙΔΩΜΕΝΟΣ)
    st.title("Διαχείριση εξοπλισμού Ρομποτικής")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Α: ΚΕΝΤΡΙΚΟ ΜΕΝΟΥ ΔΙΑΧΕΙΡΙΣΤΗ
    # ------------------------------------------
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
    # ΣΕΛΙΔΑ Β: ΛΙΣΤΑ ΕΞΟΠΛΙΣΜΟΥ (ΠΡΟΒΟΛΗ με Αχρησιμοποίητα και Extra Parts)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list":
        st.subheader("📋 Λίστα Εξοπλισμού")
        
        try:
            p_sheet = get_products_sheet()
            p_records = p_sheet.get_all_records()
            
            b_sheet = get_broken_sheet()
            b_records = b_sheet.get_all_records()

            l_sheet = get_loans_sheet()
            l_records = l_sheet.get_all_records()

            r_sheet = get_robots_sheet()
            r_records = r_sheet.get_all_records()
            
            # Υπολογισμός χαλασμένων
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

            # Υπολογισμός δανεισμένων
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

            # Υπολογισμός χρησιμοποιούμενων σε ρομπότ ανά προϊόν (βασικά + extra_parts με ποσότητες)
            robot_usage_map = {}
            for rr in r_records:
                status_r = str(rr.get("status", rr.get("Status", "Ενεργό"))).strip()
                if status_r != "Διαλυμένο":
                    board = str(rr.get("board", "")).strip()
                    
                    s1 = str(rr.get("sensor1", "")).strip()
                    try:
                        s1_qty = int(rr.get("sensor1_qty", 1))
                    except:
                        s1_qty = 1

                    s2 = str(rr.get("sensor2", "")).strip()
                    try:
                        s2_qty = int(rr.get("sensor2_qty", 1))
                    except:
                        s2_qty = 1

                    batt = str(rr.get("battery", "")).strip()
                    
                    try:
                        motors_qty = int(rr.get("motors_qty", 0))
                    except:
                        motors_qty = 0
                    motors_name = str(rr.get("motors", "")).strip()

                    try:
                        wheels_qty = int(rr.get("wheels_qty", 0))
                    except:
                        wheels_qty = 0
                    wheels_name = str(rr.get("wheels", "")).strip()

                    extra_str = str(rr.get("extra_parts", "")).strip()

                    if board: robot_usage_map[board] = robot_usage_map.get(board, 0) + 1
                    if s1: robot_usage_map[s1] = robot_usage_map.get(s1, 0) + s1_qty
                    if s2: robot_usage_map[s2] = robot_usage_map.get(s2, 0) + s2_qty
                    if batt: robot_usage_map[batt] = robot_usage_map.get(batt, 0) + 1
                    if motors_name and motors_qty > 0: robot_usage_map[motors_name] = robot_usage_map.get(motors_name, 0) + motors_qty
                    if wheels_name and wheels_qty > 0: robot_usage_map[wheels_name] = robot_usage_map.get(wheels_name, 0) + wheels_qty

                    if extra_str:
                        parts_list = extra_str.split(",")
                        for part in parts_list:
                            if ":" in part:
                                p_part_name, p_part_qty_str = part.split(":", 1)
                                p_part_name = p_part_name.strip()
                                try:
                                    p_part_qty = int(p_part_qty_str.strip())
                                except:
                                    p_part_qty = 0
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
                    try:
                        p_qty = int(pr.get("product_quantity", pr.get("Quantity", 0)))
                    except:
                        pass
                    
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
                selected_company = st.selectbox("Κατηγορία (product_company)", options=company_list)
            else:
                selected_company = st.text_input("Κατηγορία (product_company) - (Δεν βρέθηκαν κατηγορίες στο DB_Company)")
            
            subcategories = ["Kit", "Part"]
            selected_subcategory = st.selectbox("Υποκατηγορία (product_subcategory)", options=subcategories)
            
            p_name = st.text_input("Όνομα Προϊόντος (product_name)")
            p_qty = st.number_input("Τεμάχια (product_quantity)", min_value=0, step=1)
            
            insert_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_btn:
                if p_name.strip() and selected_company:
                    try:
                        p_sheet = get_products_sheet()
                        p_sheet.append_row([next_p_id, selected_company, selected_subcategory, p_name.strip(), p_qty])
                        st.success("Το προϊόν αποθηκεύτηκε! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να το δείτε στη λίστα.")
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
            c_sheet = get_company_sheet()
            c_recs = c_sheet.get_all_records()
            for r in c_recs:
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_name and c_name not in company_options:
                    company_options.append(c_name)
            
            p_sheet = get_products_sheet()
            product_records = p_sheet.get_all_records()
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

            product_display_options = {f"ID: {p['id']} - {p['name']}": p for p in filtered_products}

            if not product_display_options:
                st.info(f"Δεν υπάρχουν προϊόντα για την κατηγορία '{selected_edit_company}'.")
            else:
                selected_prod_label = st.selectbox("Επιλέξτε Προϊόν", options=list(product_display_options.keys()))
                chosen_product = product_display_options[selected_prod_label]
                
                curr_data = chosen_product["data"]
                curr_subcat = str(curr_data.get("product_subcategory", curr_data.get("Subcategory", "Kit"))).strip()
                if curr_subcat not in ["Kit", "Part"]:
                    curr_subcat = "Kit"
                
                curr_name = str(curr_data.get("product_name", curr_data.get("Name", ""))).strip()
                
                try:
                    curr_qty = int(curr_data.get("product_quantity", curr_data.get("Quantity", 0)))
                except:
                    curr_qty = 0

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
                                st.success(f"Το προϊόν ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να το δείτε.")
                            except Exception as e:
                                st.error(f"Σφάλμα ενημέρωσης: {e}")
                        else:
                            st.warning("Το όνομα προϊόντος είναι υποχρεωτικό.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ε: ΔΙΑΧΕΙΡΙΣΗ ΚΑΤΕΣΤΡΑΜΜΕΝΩΝ (db_broken)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "broken":
        st.subheader("⚠️ Διαχείριση Κατεστραμμένων Προϊόντων")
        
        company_options = []
        product_records = []
        try:
            c_sheet = get_company_sheet()
            c_recs = c_sheet.get_all_records()
            for r in c_recs:
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_name and c_name not in company_options:
                    company_options.append(c_name)
            
            p_sheet = get_products_sheet()
            product_records = p_sheet.get_all_records()
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

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
                    try:
                        p_qty = int(r.get("product_quantity", r.get("Quantity", 0)))
                    except:
                        p_qty = 0
                    filtered_products.append({"id": p_id, "subcategory": p_sub, "name": p_name, "quantity": p_qty})

            product_display_options = {f"ID: {p['id']} - {p['name']} (Διαθέσιμα: {p['quantity']})": p for p in filtered_products}

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
                                st.success(f"Καταγράφηκαν {broken_qty} κατεστραμμένα τεμάχια. Υπόλοιπο λειτουργικά: {operation_result}. Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                            except Exception as e:
                                st.error(f"Σφάλμα αποθήκευσης κατεστραμμένων: {e}")
                        else:
                            st.warning("Παρακαλώ εισάγετε αριθμό μεγαλύτερο του 0.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Θ: ΔΑΝΕΙΣΜΟΣ ΕΞΟΠΛΙΣΜΟΥ (db_loans)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "loans":
        st.subheader("🤝 Δανεισμός & Επιστροφή Εξοπλισμού")

        tab_borrow, tab_return = st.tabs(["📝 Καταγραφή Νέου Δανεισμού", "↩️ Επιστροφή / Ενεργοί Δανεισμοί"])

        with tab_borrow:
            product_records = []
            try:
                p_sheet = get_products_sheet()
                product_records = p_sheet.get_all_records()
            except Exception as e:
                st.error(f"Σφάλμα φόρτωσης προϊόντων: {e}")

            if not product_records:
                st.warning("Δεν βρέθηκαν διαθέσιμα προϊόντα.")
            else:
                prod_options = {f"ID: {r.get('product_id', r.get('id', ''))} - {r.get('product_name', r.get('Name', ''))} (Κατηγορία: {r.get('product_company', r.get('Company', ''))})": r for r in product_records}

                with st.form("loan_form"):
                    selected_prod_label = st.selectbox("Επιλέξτε Προϊόν για Δανεισμό", options=list(prod_options.keys()))
                    chosen_p = prod_options[selected_prod_label]
                    
                    borrower_name = st.text_input("Όνομα Δανειζόμενου (Μέλους Ομάδας)")
                    quantity_borrowed = st.number_input("Ποσότητα Δανεισμού", min_value=1, step=1)
                    
                    loan_submit = st.form_submit_button("Καταχώριση Δανεισμού")

                    if loan_submit:
                        if borrower_name.strip() and quantity_borrowed > 0:
                            try:
                                l_sheet = get_loans_sheet()
                                l_records = l_sheet.get_all_records()
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
                                st.success(f"Ο δανεισμός καταγράφηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                            except Exception as e:
                                st.error(f"Σφάλμα καταγραφής δανεισμού: {e}")
                        else:
                            st.warning("Συμπληρώστε το όνομα του δανειζόμενου και έγκυρη ποσότητα.")

        with tab_return:
            st.write("Ενεργοί Δανεισμοί που εκκρεμούν προς επιστροφή:")
            try:
                l_sheet = get_loans_sheet()
                l_records = l_sheet.get_all_records()
                
                active_loans = []
                for idx, r in enumerate(l_records):
                    status = str(r.get("status", r.get("Status", ""))).strip()
                    if status == "Ενεργός Δανεισμός":
                        active_loans.append({"row_index": idx + 2, "data": r})

                if not active_loans:
                    st.info("Δεν υπάρχουν ενεργοί δανεισμοί αυτή τη στιγμή.")
                else:
                    active_options = {f"Δανεισμός ID: {l['data'].get('loan_id', l['data'].get('ID',''))} | Προϊόν: {l['data'].get('product_name', l['data'].get('Product Name',''))} | Ποιος: {l['data'].get('borrower_name', l['data'].get('Borrower',''))}": l for l in active_loans}

                    with st.form("return_form"):
                        selected_active_label = st.selectbox("Επιλέξτε Δανεισμό προς Επιστροφή", options=list(active_options.keys()))
                        chosen_loan = active_options[selected_active_label]
                        
                        return_submit = st.form_submit_button("Καταχώριση Επιστροφής")

                        if return_submit:
                            try:
                                row_to_up = chosen_loan["row_index"]
                                today_str = str(datetime.date.today())
                                l_sheet.update_cell(row_to_up, 6, "Επιστράφηκε")
                                l_sheet.update_cell(row_to_up, 7, today_str)
                                st.success(f"Η επιστροφή καταχωρήθηκε! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                            except Exception as e:
                                st.error(f"Σφάλμα ενημέρωσης επιστροφής: {e}")
            except Exception as e:
                st.error(f"Σφάλμα φόρτωσης δανείων: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ J: ΚΑΤΑΣΚΕΥΗ ΡΟΜΠΟΤ (db_robots)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "robot_build":
        st.subheader("🤖 Κατασκευή Νέου Ρομπότ")

        product_records = []
        try:
            p_sheet = get_products_sheet()
            product_records = p_sheet.get_all_records()
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης προϊόντων: {e}")

        if not product_records:
            st.warning("Δεν βρέθηκαν προϊόντα στην αποθήκη.")
        else:
            product_names = [str(r.get("product_name", r.get("Name", ""))).strip() for r in product_records if str(r.get("product_name", r.get("Name", ""))).strip()]
            product_names = sorted(list(set(product_names)))

            with st.form("robot_build_form"):
                operator_name = st.text_input("Όνομα Χειριστή")
                robot_name = st.text_input("Όνομα Ρομπότ (π.χ. KAGE)")

                board = st.selectbox("Πλακέτα", options=[""] + product_names)
                
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    sensor1 = st.selectbox("Τύπος Αισθητήρων (Είδος 1)", options=[""] + product_names)
                with col_s2:
                    sensor1_qty = st.number_input("Ποσότητα Είδους 1", min_value=0, step=1, value=1)
                with col_s3:
                    sensor2 = st.selectbox("Τύπος Αισθητήρων (Είδος 2)", options=[""] + product_names)
                with col_s4:
                    sensor2_qty = st.number_input("Ποσότητα Είδους 2", min_value=0, step=1)

                battery = st.selectbox("Μπαταρία", options=[""] + product_names)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    motors = st.selectbox("Κινητήρες", options=[""] + product_names)
                with col_m2:
                    motors_qty = st.number_input("Ποσότητα Κινητήρων", min_value=0, step=1)

                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    wheels = st.selectbox("Ρόδες", options=[""] + product_names)
                with col_w2:
                    wheels_qty = st.number_input("Ποσότητα Ρόδων", min_value=0, step=1)

                chassis = st.text_input("Σασί (Πλαίσιο - Ελεύθερο κείμενο)")

                st.markdown("---")
                st.subheader("🔌 Open Source / Extra Υλικά (Καλώδια, Αντάπτορες, Drivers, Πυκνωτές, Αντιστάσεις, Buttons κ.λπ.)")
                
                selected_extras = st.multiselect("Επιλέξτε επιπλέον υλικά από την αποθήκη", options=product_names, key="build_extras_multi")
                
                extra_qtys = {}
                if selected_extras:
                    st.write("Ορίστε τεμάχια για καθένα από τα extra υλικά:")
                    for ex in selected_extras:
                        extra_qtys[ex] = st.number_input(f"Τεμάχια για: {ex}", min_value=1, step=1, value=1, key=f"build_ex_qty_{ex}")
                
                build_submit = st.form_submit_button("Οριστική Κατασκευή Ρομπότ")

                if build_submit:
                    if operator_name.strip() and robot_name.strip():
                        try:
                            r_sheet = get_robots_sheet()
                            r_records = r_sheet.get_all_records()
                            next_robot_id = len(r_records) + 1 if r_records else 1

                            extra_parts_str = ", ".join([f"{ex}:{extra_qtys[ex]}" for ex in selected_extras])

                            r_sheet.append_row([
                                next_robot_id,
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
                            st.success(f"Το ρομπότ '{robot_name}' κατασκευάστηκε και καταγράφηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                        except Exception as e:
                            st.error(f"Σφάλμα αποθήκευσης ρομπότ: {e}")
                    else:
                        st.warning("Συμπληρώστε το όνομα χειριστή και το όνομα του ρομπότ.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ K: ΕΠΕΞΕΡΓΑΣΙΑ / ΑΛΛΑΓΗ ΕΞΑΡΤΗΜΑΤΩΝ ΡΟΜΠΟΤ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "robot_edit":
        st.subheader("✏️ Επεξεργασία & Αλλαγή Εξαρτημάτων Ρομπότ")

        robot_records = []
        product_records = []
        try:
            r_sheet = get_robots_sheet()
            robot_records = r_sheet.get_all_records()

            p_sheet = get_products_sheet()
            product_records = p_sheet.get_all_records()
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης δεδομένων: {e}")

        if not robot_records:
            st.info("Δεν βρέθηκαν καταχωρημένα ρομπότ.")
        else:
            active_robots = []
            for idx, r in enumerate(robot_records):
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

                product_names = [str(p.get("product_name", p.get("Name", ""))).strip() for p in product_records if str(p.get("product_name", p.get("Name", ""))).strip()]
                product_names = sorted(list(set(product_names)))

                existing_extras = {}
                curr_extra_str = str(r_data.get("extra_parts", "")).strip()
                if curr_extra_str:
                    for part in curr_extra_str.split(","):
                        if ":" in part:
                            pn, pq = part.split(":", 1)
                            try:
                                existing_extras[pn.strip()] = int(pq.strip())
                            except:
                                existing_extras[pn.strip()] = 1

                with st.form("robot_edit_form"):
                    edit_operator = st.text_input("Νέο Όνομα Χειριστή", value=str(r_data.get("operator_name", r_data.get("Operator", ""))))
                    edit_robot_name = st.text_input("Νέο Όνομα Ρομπότ", value=str(r_data.get("robot_name", r_data.get("Robot Name", ""))))

                    curr_board = str(r_data.get("board", ""))
                    edit_board = st.selectbox("Πλακέτα", options=[""] + product_names, index=(product_names.index(curr_board) + 1) if curr_board in product_names else 0)

                    curr_s1 = str(r_data.get("sensor1", ""))
                    try:
                        curr_s1_qty = int(r_data.get("sensor1_qty", 1))
                    except:
                        curr_s1_qty = 1

                    curr_s2 = str(r_data.get("sensor2", ""))
                    try:
                        curr_s2_qty = int(r_data.get("sensor2_qty", 1))
                    except:
                        curr_s2_qty = 1

                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    with col_s1:
                        edit_sensor1 = st.selectbox("Τύπος Αισθητήρων (Είδος 1)", options=[""] + product_names, index=(product_names.index(curr_s1) + 1) if curr_s1 in product_names else 0)
                    with col_s2:
                        edit_sensor1_qty = st.number_input("Ποσότητα Είδους 1", min_value=0, value=curr_s1_qty, step=1)
                    with col_s3:
                        edit_sensor2 = st.selectbox("Τύπος Αισθητήρων (Είδος 2)", options=[""] + product_names, index=(product_names.index(curr_s2) + 1) if curr_s2 in product_names else 0)
                    with col_s4:
                        edit_sensor2_qty = st.number_input("Ποσότητα Είδους 2", min_value=0, value=curr_s2_qty, step=1)

                    curr_batt = str(r_data.get("battery", ""))
                    edit_battery = st.selectbox("Μπαταρία", options=[""] + product_names, index=(product_names.index(curr_batt) + 1) if curr_batt in product_names else 0)

                    curr_motors = str(r_data.get("motors", ""))
                    try:
                        curr_mqty = int(r_data.get("motors_qty", 0))
                    except:
                        curr_mqty = 0

                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        edit_motors = st.selectbox("Κινητήρες", options=[""] + product_names, index=(product_names.index(curr_motors) + 1) if curr_motors in product_names else 0)
                    with col_m2:
                        edit_motors_qty = st.number_input("Ποσότητα Κινητήρων", min_value=0, value=curr_mqty, step=1)

                    curr_wheels = str(r_data.get("wheels", ""))
                    try:
                        curr_wqty = int(r_data.get("wheels_qty", 0))
                    except:
                        curr_wqty = 0

                    col_w1, col_w2 = st.columns(2)
                    with col_w1:
                        edit_wheels = st.selectbox("Ρόδες", options=[""] + product_names, index=(product_names.index(curr_wheels) + 1) if curr_wheels in product_names else 0)
                    with col_w2:
                        edit_wheels_qty = st.number_input("Ποσότητα Ρόδων", min_value=0, value=curr_wqty, step=1)

                    curr_chassis = str(r_data.get("chassis", ""))
                    edit_chassis = st.text_input("Σασί (Πλαίσιο - Ελεύθερο κείμενο)", value=curr_chassis)

                    st.markdown("---")
                    st.subheader("🔌 Open Source / Extra Υλικά (Επεξεργασία)")
                    default_selected_extras = [k for k in existing_extras.keys() if k in product_names]
                    edit_selected_extras = st.multiselect("Επιλέξτε επιπλέον υλικά από την αποθήκη", options=product_names, default=default_selected_extras, key="edit_extras_multi")
                    
                    edit_extra_qtys = {}
                    if edit_selected_extras:
                        st.write("Ορίστε τεμάχια για καθένα από τα extra υλικά:")
                        for ex in edit_selected_extras:
                            default_val = existing_extras.get(ex, 1)
                            edit_extra_qtys[ex] = st.number_input(f"Τεμάχια για: {ex}", min_value=1, step=1, value=default_val, key=f"edit_ex_qty_{ex}")

                    edit_submit = st.form_submit_button("Οριστική Ενημέρωση Ρομπότ")

                    if edit_submit:
                        try:
                            r_sheet = get_robots_sheet()
                            row_idx = chosen_robot["row_index"]

                            edit_extra_parts_str = ", ".join([f"{ex}:{edit_extra_qtys[ex]}" for ex in edit_selected_extras])

                            r_sheet.update_cell(row_idx, 2, edit_operator.strip())
                            r_sheet.update_cell(row_idx, 3, edit_robot_name.strip())
                            r_sheet.update_cell(row_idx, 4, edit_board)
                            r_sheet.update_cell(row_idx, 5, edit_sensor1)
                            r_sheet.update_cell(row_idx, 6, edit_sensor1_qty)
                            r_sheet.update_cell(row_idx, 7, edit_sensor2)
                            r_sheet.update_cell(row_idx, 8, edit_sensor2_qty)
                            r_sheet.update_cell(row_idx, 9, edit_battery)
                            r_sheet.update_cell(row_idx, 10, edit_motors)
                            r_sheet.update_cell(row_idx, 11, edit_motors_qty)
                            r_sheet.update_cell(row_idx, 12, edit_wheels)
                            r_sheet.update_cell(row_idx, 13, edit_wheels_qty)
                            r_sheet.update_cell(row_idx, 14, edit_chassis.strip())
                            r_sheet.update_cell(row_idx, 15, edit_extra_parts_str)

                            st.success("Το ρομπότ ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού.")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης ρομπότ: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ L: ΛΙΣΤΑ ΡΟΜΠΟΤ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "robot_list":
        st.subheader("📋 Λίστα Κατασκευασμένων Ρομπότ")

        try:
            r_sheet = get_robots_sheet()
            r_records = r_sheet.get_all_records()

            robot_list_data = []
            for r in r_records:
                r_id = str(r.get("robot_id", r.get("ID", ""))).strip()
                op_name = str(r.get("operator_name", r.get("Operator", ""))).strip()
                r_name = str(r.get("robot_name", r.get("Robot Name", ""))).strip()
                board = str(r.get("board", r.get("Board", ""))).strip()
                
                s1 = str(r.get("sensor1", "")).strip()
                try:
                    s1_q = int(r.get("sensor1_qty", 1))
                except:
                    s1_q = 1

                s2 = str(r.get("sensor2", "")).strip()
                try:
                    s2_q = int(r.get("sensor2_qty", 0))
                except:
                    s2_q = 0

                s_types = f"{s1} (x{s1_q})"
                if s2:
                    s_types += f", {s2} (x{s2_q})"

                batt = str(r.get("battery", r.get("Battery", ""))).strip()
                motors = f"{r.get('motors', '')} ({r.get('motors_qty', 0)})".strip()
                wheels = f"{r.get('wheels', '')} ({r.get('wheels_qty', 0)})".strip()
                chassis = str(r.get("chassis", r.get("Chassis", ""))).strip()
                extras = str(r.get("extra_parts", "")).strip()
                status = str(r.get("status", r.get("Status", "Ενεργό"))).strip()

                robot_list_data.append({
                    "ID": r_id,
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
            st.error(f"Σφάλμα φόρτωσης λίστας ρομπότ: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ι: ΛΙΣΤΑ ΕΝΕΡΓΩΝ ΔΑΝΕΙΣΜΩΝ
    # ------------------------------------------
    elif st.session_state.admin_subpage == "active_loans_list":
        st.subheader("📋 Λίστα Ενεργών Δανεισμών")
        
        try:
            l_sheet = get_loans_sheet()
            l_records = l_sheet.get_all_records()
            
            active_list_data = []
            for r in l_records:
                status = str(r.get("status", r.get("Status", ""))).strip()
                if status == "Ενεργός Δανεισμός":
                    l_id = str(r.get("loan_id", r.get("ID", ""))).strip()
                    p_name = str(r.get("product_name", r.get("Product Name", ""))).strip()
                    borrower = str(r.get("borrower_name", r.get("Borrower", ""))).strip()
                    l_date = str(r.get("loan_date", r.get("Date", ""))).strip()
                    
                    l_qty = 0
                    try:
                        l_qty = int(r.get("quantity_borrowed", r.get("Quantity", 0)))
                    except:
                        pass
                    
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
            st.error(f"Σφάλμα φόρτωσης ενεργών δανεισμών: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Κ: ΛΙΣΤΑ ΚΑΤΕΣΤΡΑΜΜΕΝΩΝ (db_broken)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "broken_list":
        st.subheader("📋 Λίστα Κατεστραμμένων Προϊόντων")
        
        try:
            b_sheet = get_broken_sheet()
            b_records = b_sheet.get_all_records()
            
            broken_list_data = []
            for r in b_records:
                b_id = str(r.get("broken_id", r.get("ID", ""))).strip()
                b_comp = str(r.get("broken_company", r.get("Company", ""))).strip()
                b_sub = str(r.get("broken_subcategory", r.get("Subcategory", ""))).strip()
                b_name = str(r.get("broken_name", r.get("Name", ""))).strip()
                
                b_qty = 0
                try:
                    b_qty = int(r.get("broken_quantity", r.get("Quantity", 0)))
                except:
                    pass
                
                op_val = 0
                try:
                    op_val = int(r.get("operation", r.get("Operation", 0)))
                except:
                    pass
                
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
            st.error(f"Σφάλμα φόρτωσης κατεστραμμένων: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ ΣΤ: ΛΙΣΤΑ ΚΑΤΗΓΟΡΙΩΝ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list_company":
        st.subheader("📋 Λίστα Κατηγοριών")
        
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
            st.error(f"Σφάλμα φόρτωσης δεδομένων κατηγοριών: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ζ: ΕΙΣΑΓΩΓΗ ΝΕΑΣ ΚΑΤΗΓΟΡΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "insert_company":
        st.subheader("➕ Φόρμα Εισαγωγής Νέας Κατηγορίας")
        
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
            company_name = st.text_input("Όνομα Κατηγορίας")
            insert_c_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_c_btn:
                if company_name.strip():
                    try:
                        c_sheet = get_company_sheet()
                        c_sheet.append_row([next_id, company_name.strip()])
                        st.success("Η κατηγορία αποθηκεύτηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να την δείτε.")
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
            c_sheet = get_company_sheet()
            records = c_sheet.get_all_records()
            for r in records:
                c_id = str(r.get("company_id", r.get("Company ID", ""))).strip()
                c_name = str(r.get("company_name", r.get("Company Name", ""))).strip()
                if c_id:
                    company_options[f"ID: {c_id} - {c_name}"] = c_id
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης κατηγοριών: {e}")

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
                                row_num = cell.row
                                c_sheet.update_cell(row_num, 2, new_c_name.strip())
                                st.success(f"Η κατηγορία με ID '{selected_id}' ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να το δείτε.")
                            else:
                                st.error(f"Δεν βρέθηκε η κατηγορία στο Google Sheet.")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης: {e}")
                    else:
                        st.warning("Συμπληρώστε το νέο όνομα της κατηγορίας.")


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
