import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Robotics Portal", page_icon="🤖", layout="wide")

# --- CSS ΓΙΑ ΠΛΗΡΗ ΚΑΘΑΡΙΣΜΟ ΤΟΥ INTERFACE ---
st.markdown("""
    <style>
    /* Εξαφάνιση της πάνω μπάρας (Share, Star, GitHub, Fork) */
    header {visibility: hidden;}
    
    /* Εξαφάνιση του μενού κάτω δεξιά (Manage app / Made with Streamlit) */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Εξαφάνιση των συνδετήρων (anchors) δίπλα από τους τίτλους */
    .stApp a.header-anchor { display: none; }
    
    /* Ρυθμίσεις για τα Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        font-size: 18px; 
        font-weight: 600;
    }
    
    /* Απόκρυψη του κουμπιού 'Deploy' αν εμφανίζεται */
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except Exception as e:
    st.error("❌ Ελέγξτε τα Secrets (GROQ_API_KEY και GSHEET_URL)!")
    st.stop()

# 3. Δημιουργία Μενού με Tabs
tab1, tab2, tab3, app_tab = st.tabs(["📑 Tab 1", "📊 Tab 2", "⚙️ Tab 3", "🚀 App"])

with tab1:
    st.header("Ενότητα 1", anchor=False)
    st.write("Καλώς ήρθατε στην πρώτη σελίδα.")

with tab2:
    st.header("Ενότητα 2", anchor=False)
    st.write("Σελίδα στατιστικών και πληροφοριών.")

with tab3:
    st.header("Ενότητα 3", anchor=False)
    st.write("Πληροφορίες ρυθμίσεων.")

with app_tab:
    st.header("🤖 Maqueen Robotics IDE", anchor=False)
    st.divider()

    # Layout Δύο Στηλών (Side-by-Side)
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("📥 Είσοδος Μαθητή", anchor=False)
        with st.form(key='maqueen_form', clear_on_submit=True):
            student_id = st.text_input("ID Μαθητή:", value="Guest")
            user_prompt = st.text_area("Περιγράψτε την αποστολή του Maqueen:", height=200)
            submit_button = st.form_submit_button(label="🚀 Δημιουργία Κώδικα & Καταγραφή")

    with col_output:
        st.subheader("🖥️ Αποτέλεσμα AI", anchor=False)
        
        if submit_button:
            if user_prompt:
                with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
                    try:
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython. "
                                               "Αν υπάρχει εναλλακτικός τρόπος, χώρισε την απάντησή σου με τη λέξη '---ΕΝΑΛΛΑΚΤΙΚΟΣ---'."
                                },
                                {"role": "user", "content": user_prompt}
                            ]
                        )
                        full_answer = response.choices[0].message.content
                        
                        if "---ΕΝΑΛΛΑΚΤΙΚΟΣ---" in full_answer:
                            parts = full_answer.split("---ΕΝΑΛΛΑΚΤΙΚΟΣ---")
                            main_code = parts[0]
                            alt_code = parts[1]
                        else:
                            main_code = full_answer
                            alt_code = None

                        st.markdown("### 🔴 Προτεινόμενη Λύση")
                        st.info(main_code)
                        
                        if alt_code and alt_code.strip():
                            st.markdown("### 🔵 Εναλλακτική Προσέγγιση")
                            st.success(alt_code)

                        data_to_send = {
                            "data": [{
                                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Student_ID": str(student_id),
                                "Prompt": str(user_prompt),
                                "Answer": str(full_answer)
                            }]
                        }
                        requests.post(SHEETDB_URL, json=data_to_send)
                        st.toast("✅ Η δραστηριότητα καταγράφηκε!", icon="📝")
                        
                    except Exception as e:
                        st.error(f"❌ Σφάλμα: {e}")
            else:
                st.warning("⚠️ Παρακαλώ γράψε μια αποστολή.")
        else:
            st.write("Περιμένω την ερώτησή σας.")

st.divider()
st.caption("AI STEM Lab v5.1 | Private Portal Edition")
