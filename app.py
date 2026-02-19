import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Ecosystem", page_icon="🎓", layout="wide")

# CSS για πλήρη καθαρισμό και επαγγελματικό στυλ
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp a.header-anchor { display: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        font-size: 16px; 
        font-weight: bold;
        border-radius: 10px 10px 0 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq (για το App Tab)
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("Σύνδεση σε λειτουργία Read-Only (Λείπουν τα API Keys)")

# 3. Δημιουργία Tabs
tab_info, tab_progress, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα Έρευνας", 
    "📈 Πρόοδος ανά Έτος", 
    "🚀 Research App (IDE)", 
    "📂 Αρχείο & Εργαλεία"
])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.subheader("Τίτλος Διδακτορικού", anchor=False)
    st.write("*Εδώ γράφεις τον επίσημο τίτλο της διατριβής σου.*")
    st.info("Σκοπός: Η ανάπτυξη εξειδικευμένου λογισμικού για την τυποποίηση της συμπεριφοράς AI μοντέλων στη Ρομποτική.")

with tab_progress:
    st.header("Χρονοδιάγραμμα & Ορόσημα", anchor=False)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1ο Έτος")
        st.write("- [x] Βιβλιογραφική Ανασκόπηση")
        st.write("- [x] Κατάθεση Υπομνήματος")
        st.write("- [x] Σχεδιασμός Μεθοδολογίας")
        
    with col2:
        st.markdown("### 2ο Έτος (Σε εξέλιξη)")
        st.write("- [x] Ανάπτυξη Λογισμικού (Python/Streamlit)")
        st.write("- [ ] Expert-based Evaluation")
        st.write("- [ ] Πιλοτική Εφαρμογή")

    with col3:
        st.markdown("### 3ο Έτος")
        st.write("- [ ] Τελική Συλλογή Δεδομένων")
        st.write("- [ ] Συγγραφή Διατριβής")
        st.write("- [ ] Υποστήριξη")

with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    # Εδώ μπαίνει ο κώδικας της εφαρμογής που φτιάξαμε
    col_in, col_out = st.columns(2, gap="large")
    with col_in:
        st.subheader("Interaction Input", anchor=False)
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("Researcher/User ID:", value="Expert_1")
            prompt = st.text_area("Περιγραφή Αποστολής Maqueen:", height=150)
            btn = st.form_submit_button("Execute & Log")
    
    with col_out:
        st.subheader("AI Output", anchor=False)
        if btn and prompt:
            # (Εδώ τρέχει η κλήση στο AI όπως πριν...)
            st.success("Ο κώδικας θα εμφανιστεί εδώ και θα καταγραφεί αυτόματα.")

with tab_data:
    st.header("Διαχείριση Δεδομένων", anchor=False)
    st.write("Όλες οι αλληλεπιδράσεις καταγράφονται για ποιοτική ανάλυση.")
    st.link_button("Άνοιγμα Google Sheets (Database)", "https://docs.google.com/spreadsheets/d/ΣΥΝΔΕΣΜΟΣ_ΣΟΥ")

st.divider()
st.caption("PhD Ecosystem v5.3 | Interaction Logging & Research Management")
