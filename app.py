import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# CSS για Clean Interface
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
    .pub-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("Σύνδεση σε λειτουργία Read-Only (Λείπουν τα API Keys)")

# 3. Δημιουργία Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα Έρευνας", 
    "📈 Πρόοδος", 
    "📚 Δημοσιεύσεις",
    "🚀 App (IDE)", 
    "📂 Αρχεία"
])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.subheader("Τίτλος Διδακτορικού", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης: Μοντέλα, Μέθοδοι και Επιπτώσεις στη Σύγχρονη Εκπαίδευση")
    st.write("**Υποστήριξη:** Το λογισμικό επιτρέπει την τυποποίηση συμπεριφοράς μοντέλου και την αυτόματη καταγραφή ιστορικού αλληλεπίδρασης.")

with tab_progress:
    st.header("Χρονοδιάγραμμα & Ορόσημα", anchor=False)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1ο Έτος")
        st.write("- [x] Βιβλιογραφική Ανασκόπηση\n- [x] Κατάθεση Υπομνήματος\n- [x] Σχεδιασμός Μεθοδολογίας")
    with col2:
        st.markdown("### 2ο Έτος")
        st.write("- [x] Ανάπτυξη Λογισμικού\n- [ ] Expert-based Evaluation\n- [ ] Πιλοτική Εφαρμογή")
    with col3:
        st.markdown("### 3ο Έτος")
        st.write("- [ ] Τελική Συλλογή Δεδομένων\n- [ ] Συγγραφή Διατριβής\n- [ ] Υποστήριξη")

with tab_pubs:
    st.header("Επιστημονικό Έργο", anchor=False)
    
    # --- ΕΤΟΣ 2024 ---
    with st.expander("📅 Δημοσιεύσεις 2025", expanded=True):
        st.markdown("""
        **Τίτλος:** *Παράδειγμα Τίτλου Δημοσίευσης 1* **Είδος:** Περιοδικό (Journal)  
        **Φορέας:** IEEE Transactions on Education  
        **URL:** [Προβολή Δημοσίευσης](https://example.com)
        """)
        st.divider()
        st.markdown("""
        **Τίτλος:** *Παράδειγμα Τίτλου Δημοσίευσης 2* **Είδος:** Συνέδριο (Conference)  
        **Φορέας:** EDUCON 2024  
        **URL:** [Προβολή Δημοσίευσης](https://example.com)
        """)

    # --- ΕΤΟΣ 2023 ---
    with st.expander("📅 Δημοσιεύσεις 2023", expanded=False):
        st.write("Δεν υπάρχουν καταχωρημένες δημοσιεύσεις για το έτος 2023.")

with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    col_in, col_out = st.columns(2, gap="large")
    with col_in:
        st.subheader("Interaction Input", anchor=False)
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("Researcher ID:", value="Expert_1")
            prompt = st.text_area("Περιγραφή Αποστολής Maqueen:", height=150)
            btn = st.form_submit_button("Execute & Log Interaction")
    
    with col_out:
        st.subheader("AI Response", anchor=False)
        if btn and prompt:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython."},
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = response.choices[0].message.content
                st.info(answer)
                
                # Logging
                data = {"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt, "Answer": answer}]}
                requests.post(SHEETDB_URL, json=data)
                st.toast("Καταγράφηκε!")
            except Exception as e:
                st.error(f"Σφάλμα: {e}")

with tab_data:
    st.header("Διαχείριση Δεδομένων", anchor=False)
    st.link_button("📊 Άνοιγμα Database (Google Sheets)", "https://docs.google.com/spreadsheets/d/ΣΥΝΔΕΣΜΟΣ_ΣΟΥ")

st.divider()
st.caption("PhD v5.5 | Integrated Research & Publications Management")
