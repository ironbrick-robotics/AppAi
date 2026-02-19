import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# CSS για Clean Research Interface
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp a.header-anchor { display: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        font-size: 16px; 
        font-weight: bold;
        border-radius: 10px 10px 0 0;
    }
    /* Στυλ για τις κάρτες δημοσιεύσεων */
    .pub-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("⚠️ Σύνδεση σε λειτουργία Read-Only (Ελέγξτε τα Secrets).")

# 3. Δομή Tabs
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
    st.write("**Ερευνητική Περιοχή:** Python Software Development, System Prompting & Interaction Logging.")

with tab_progress:
    st.header("Χρονοδιάγραμμα & Ορόσημα", anchor=False)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1ο Έτος")
        st.write("- [x] Βιβλιογραφική Ανασκόπηση\n- [x] Κατάθεση Υπομνήματος\n- [x] Σχεδιασμός Μεθοδολογίας")
    with col2:
        st.markdown("### 2ο Έτος (Σε εξέλιξη)")
        st.write("- [x] Ανάπτυξη Λογισμικού (v5.4)\n- [ ] Expert-based Evaluation\n- [ ] Πιλοτική Εφαρμογή")
    with col3:
        st.markdown("### 3ο Έτος")
        st.write("- [ ] Τελική Συλλογή Δεδομένων\n- [ ] Συγγραφή Διατριβής\n- [ ] Υποστήριξη")

with tab_pubs:
    st.header("Επιστημονικές Δημοσιεύσεις", anchor=False)
    
    # --- ΔΙΕΘΝΗ ΣΥΝΕΔΡΙΑ ---
    st.subheader("🌐 Διεθνή Συνέδρια με Κριτές", anchor=False)
    with st.container():
        st.markdown("""
        <div class="pub-box">
            <strong>Τίτλος:</strong> "Competitive Robotics in Education: Didactic Approach and Technological Analysis of a Mini Sumo Robot"<br>
            <strong>Είδος:</strong> Διεθνές Συνέδριο (Conference Paper)<br>
            <strong>Συνέδριο:</strong> 4th International Conference on Sport & Education (ICSE 2025)<br>
            <strong>Τοποθεσία:</strong> Lisbon, Portugal<br>
            <a href="#">🔗 URL Δημοσίευσης (Coming Soon)</a>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- ΕΘΝΙΚΑ ΣΥΝΕΔΡΙΑ / ΗΜΕΡΙΔΕΣ ---
    st.subheader("🏛️ Εθνικά Συνέδρια & Ημερίδες", anchor=False)
    with st.container():
        st.markdown("""
        <div class="pub-box" style="border-left-color: #00a0dc;">
            <strong>Τίτλος:</strong> "Από τον Αλγόριθμο στη Δημιουργία: Ενσωμάτωση της Παραγωγικής ΤΝ στην Εκπαίδευση"<br>
            <strong>Είδος:</strong> Ημερίδα / Συνέδριο<br>
            <strong>Φορέας:</strong> Τεχνητή Νοημοσύνη και Καινοτομία στην Εκπαίδευση, ΔΙΠΑΕ<br>
            <strong>Τοποθεσία:</strong> Θεσσαλονίκη, Ελλάδα<br>
            <a href="#">🔗 URL Δημοσίευσης</a>
        </div>
        """, unsafe_allow_html=True)

with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    col_in, col_out = st.columns(2, gap="large")
    with col_in:
        st.subheader("Interaction Input", anchor=False)
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("Researcher ID:", value="Expert_User")
            prompt = st.text_area("Περιγραφή Αποστολής Maqueen:", height=150)
            btn = st.form_submit_button("🚀 Execute & Log")
    
    with col_out:
        st.subheader("AI Response", anchor=False)
        if btn and prompt:
            with st.spinner('⏳ Παραγωγή κώδικα...'):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython. Χώρισε με ---ΕΝΑΛΛΑΚΤΙΚΟΣ--- αν υπάρχει 2η λύση."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ans = response.choices[0].message.content
                    st.info(ans)
                    
                    # Log to Google Sheets
                    data = {"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt, "Answer": ans}]}
                    requests.post(SHEETDB_URL, json=data)
                    st.toast("✅ Καταγράφηκε επιτυχώς!")
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

with tab_data:
    st.header("Διαχείριση Ερευνητικών Δεδομένων", anchor=False)
    st.write("Η βάση δεδομένων περιλαμβάνει τα logs από τις expert-based αξιολογήσεις.")
    st.link_button("📊 Άνοιγμα Google Sheets Database", st.secrets.get("GSHEET_URL_LINK", "https://docs.google.com/spreadsheets/"))

st.divider()
st.caption("PhD v5.6 | Integrated Research Management")
