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
            if st.button("➕ Εισαγωγή Εταιρείας", use_container_width=True):
                st.session_state.admin_subpage = "insert_company"
                st.rerun()
            if st.button("📋 Λίστα Εταιρειών", use_container_width=True):
                st.session_state.admin_subpage = "list_company"
                st.rerun()
        with col_c2:
            if st.button("✏️ Επεξεργασία Εταιρείας", use_container_width=True):
                st.session_state.admin_subpage = "edit_company"
                st.rerun()

        st.markdown("---")
        st.subheader("📦 Εισαγωγή - Επεξεργασία Προϊόντος")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if st.button("➕ Εισαγωγή Προϊόντος", use_container_width=True):
                st.session_state.admin_subpage = "insert"
                st.rerun()
            if st.button("📋 Λίστα εξοπλισμού", use_container_width=True):
                st.session_state.admin_subpage = "list"
                st.rerun()
        with col_m2:
            if st.button("✏️ Επεξεργασία Προϊόντος", use_container_width=True):
                st.session_state.admin_subpage = "edit"
                st.rerun()
            if st.button("⚠️ Κατεστραμμένα", use_container_width=True):
                st.session_state.admin_subpage = "broken"
                st.rerun()

    # ------------------------------------------
    # ΣΕΛΙΔΑ Β: ΛΙΣΤΑ ΕΞΟΠΛΙΣΜΟΥ (ΠΡΟΒΟΛΗ με Χαλασμένα & Λειτουργικά)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list":
        st.subheader("📋 Εισαγωγή - Επεξεργασία Προϊόντος: Λίστα Εξοπλισμού")
        
        try:
            p_sheet = get_products_sheet()
            p_records = p_sheet.get_all_records()
            
            b_sheet = get_broken_sheet()
            b_records = b_sheet.get_all_records()
            
            # Υπολογισμός συνολικών χαλασμένων ανά προϊόν (βάσει ID ή ονόματος)
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
                    
                    # Χαλασμένα τεμάχια από το db_broken
                    broken_qty = broken_map.get(p_id, 0)
                    # Λειτουργικά τεμάχια = Συνολικά - Χαλασμένα (ελάχιστο 0)
                    functional_qty = max(0, p_qty - broken_qty)
                    
                    table_data.append({
                        "ΚΩΔΙΚΟΣ": p_id,
                        "ΕΤΑΙΡΕΙΑ": p_comp,
                        "ΚΑΤΗΓΟΡΙΑ": p_sub,
                        "ΟΝΟΜΑ ΠΡΟΪΟΝΤΟΣ": p_name,
                        "ΣΥΝΟΛΙΚΑ ΤΕΜΑΧΙΑ": p_qty,
                        "ΧΑΛΑΣΜΕΝΑ": broken_qty,
                        "ΛΕΙΤΟΥΡΓΙΚΑ": functional_qty
                    })

                df_products = pd.DataFrame(table_data)
                st.dataframe(df_products, use_container_width=True, hide_index=True)
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
                selected_company = st.selectbox("Εταιρεία (product_company)", options=company_list)
            else:
                selected_company = st.text_input("Εταιρεία (product_company) - (Δεν βρέθηκαν εταιρείες στο DB_Company)")
            
            subcategories = ["Kit", "Part"]
            selected_subcategory = st.selectbox("Κατηγορία (product_subcategory)", options=subcategories)
            
            p_name = st.text_input("Όνομα Προϊόντος (product_name)")
            p_qty = st.number_input("Τεμάχια (product_quantity)", min_value=0, step=1)
            
            insert_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_btn:
                if p_name.strip() and selected_company:
                    try:
                        p_sheet = get_products_sheet()
                        # Σειρά: product_id, product_company, product_subcategory, product_name, product_quantity
                        p_sheet.append_row([next_p_id, selected_company, selected_subcategory, p_name.strip(), p_qty])
                        st.success("Το προϊόν αποθηκεύτηκε! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να το δείτε στη λίστα.")
                    except Exception as e:
                        st.error(f"Σφάλμα εισαγωγής: {e}")
                else:
                    st.warning("Το όνομα προϊόντος και η εταιρεία είναι υποχρεωτικά.")

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
            st.warning("Δεν βρέθηκαν καταχωρημένες εταιρείες ή προϊόντα.")
        else:
            selected_edit_company = st.selectbox("Επιλέξτε Εταιρεία", options=company_options)
            
            filtered_products = []
            for idx, r in enumerate(product_records):
                comp = str(r.get("product_company", r.get("Company", ""))).strip()
                if comp == selected_edit_company:
                    p_id = str(r.get("product_id", r.get("Product ID", r.get("id", "")))).strip()
                    p_name = str(r.get("product_name", r.get("Name", ""))).strip()
                    filtered_products.append({"row_index": idx + 2, "id": p_id, "name": p_name, "data": r})

            product_display_options = {f"ID: {p['id']} - {p['name']}": p for p in filtered_products}

            if not product_display_options:
                st.info(f"Δεν υπάρχουν προϊόντα για την εταιρεία '{selected_edit_company}'.")
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
                    edit_subcategory = st.selectbox("Νέα Κατηγορία (product_subcategory)", options=["Kit", "Part"], index=["Kit", "Part"].index(curr_subcat))
                    edit_name = st.text_input("Νέο Όνομα Προϊόντος (product_name)", value=curr_name)
                    edit_qty = st.number_input("Νέα Τεμάχια (product_quantity)", min_value=0, value=curr_qty, step=1)
                    
                    edit_btn = st.form_submit_button("Οριστική Ενημέρωση")
                    
                    if edit_btn:
                        if edit_name.strip():
                            try:
                                sheet = get_products_sheet()
                                row_to_update = chosen_product["row_index"]
                                # Ενημέρωση σειράς: ID(2), Company(3), Subcategory(4), Name(5), Quantity(6)
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
            st.warning("Δεν βρέθηκαν καταχωρημένες εταιρείες ή προϊόντα.")
        else:
            selected_b_company = st.selectbox("Επιλέξτε Εταιρεία", options=company_options, key="b_comp")
            
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
                st.info(f"Δεν υπάρχουν προϊόντα για την εταιρεία '{selected_b_company}'.")
            else:
                selected_b_prod_label = st.selectbox("Επιλέξτε Προϊόν", options=list(product_display_options.keys()), key="b_prod")
                chosen_b_prod = product_display_options[selected_b_prod_label]

                with st.form("broken_form"):
                    broken_qty = st.number_input("Κατεστραμμένα Τεμάχια", min_value=0, max_value=chosen_b_prod["quantity"], step=1)
                    submit_broken = st.form_submit_button("Καταχώριση Κατεστραμμένων")
                    
                    if submit_broken:
                        if broken_qty > 0:
                            try:
                                # Αυτόματη πράξη: product_quantity - broken_quantity
                                operation_result = chosen_b_prod["quantity"] - broken_qty
                                
                                b_sheet = get_broken_sheet()
                                # Πεδία db_broken: broken_id, broken_company, broken_subcategory, broken_name, broken_quantity, operation
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
    # ΣΕΛΙΔΑ ΣΤ: ΛΙΣΤΑ ΕΤΑΙΡΕΙΩΝ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "list_company":
        st.subheader("📋 ΕΤΑΙΡΕΙΑ ΠΡΟΪΟΝΤΟΣ: Λίστα Εταιρειών")
        
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
            st.error(f"Σφάλμα φόρτωσης δεδομένων εταιρειών: {e}")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Ζ: ΕΙΣΑΓΩΓΗ ΝΕΑΣ ΕΤΑΙΡΕΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "insert_company":
        st.subheader("➕ Φόρμα Εισαγωγής Νέας Εταιρείας")
        
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
            company_name = st.text_input("Όνομα Εταιρείας (company_name)")
            insert_c_btn = st.form_submit_button("Οριστική Εισαγωγή")
            
            if insert_c_btn:
                if company_name.strip():
                    try:
                        c_sheet = get_company_sheet()
                        c_sheet.append_row([next_id, company_name.strip()])
                        st.success("Η εταιρεία αποθηκεύτηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να την δείτε.")
                    except Exception as e:
                        st.error(f"Σφάλμα αποθήκευσης: {e}")
                else:
                    st.warning("Το όνομα της εταιρείας είναι υποχρεωτικό.")

    # ------------------------------------------
    # ΣΕΛΙΔΑ Η: ΕΠΕΞΕΡΓΑΣΙΑ ΕΤΑΙΡΕΙΑΣ (DB_Company)
    # ------------------------------------------
    elif st.session_state.admin_subpage == "edit_company":
        st.subheader("✏️ Φόρμα Επεξεργασίας Εταιρείας")
        
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
            st.error(f"Σφάλμα φόρτωσης εταιρειών: {e}")

        if not company_options:
            st.warning("Δεν βρέθηκαν καταχωρημένες εταιρείες στο tab DB_Company.")
        else:
            with st.form("edit_company_form"):
                selected_option = st.selectbox("Επιλέξτε Εταιρεία προς Τροποποίηση", options=list(company_options.keys()))
                new_c_name = st.text_input("Νέο Όνομα Εταιρείας (company_name)")
                
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
                                st.success(f"Η εταιρεία με ID '{selected_id}' ενημερώθηκε επιτυχώς! Πατήστε «🔄 Ανανέωση Δεδομένων» στο πλαϊνό μενού για να το δείτε.")
                            else:
                                st.error(f"Δεν βρέθηκε η εταιρεία στο Google Sheet.")
                        except Exception as e:
                            st.error(f"Σφάλμα ενημέρωσης: {e}")
                    else:
                        st.warning("Συμπληρώστε το νέο όνομα της εταιρείας.")


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
