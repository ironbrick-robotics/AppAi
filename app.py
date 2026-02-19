import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# CSS για Clean Interface και Visual Blocks
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
    /* Στυλ για τα Virtual Blocks */
    .block-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 10px 0;
    }
    .block-event { background-color: #ffab19; color: white; padding: 10px; border-radius: 8px 8px 0 0; font-weight: bold; border: 2px solid #e69100; }
    .block-control { background-color: #ff6680; color: white; padding: 10px; margin-left: 20px; border-left: 10px solid #d33; font-weight: bold; }
    .block-motion { background-color: #4c97ff; color: white; padding: 10px; margin-left: 40px; border-radius: 4px; border: 1px solid #3373cc; margin-top: 2px; }
    .pub-box {
        background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("⚠️ Σύνδεση σε λειτουργία Read-Only.")

# 3. Δομή Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα Έρευνας", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (IDE)", "📂 Αρχεία"
])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.subheader("Τίτλος Διδακτορικού", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης: Μοντέλα, Μέθοδοι και Επιπτώσεις στη Σύγχρονη Εκπαίδευση")

with tab_progress:
    st.header("Χρονοδιάγραμμα & Ορόσημα", anchor=False)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1ο Έτος\n- [x] Βιβλιογραφική Ανασκόπηση\n- [x] Κατάθεση Υπομνήματος")
    with col2:
        st.markdown("### 2ο Έτος\n- [x] Ανάπτυξη Λογισμικού (v5.6)\n- [ ] Dual-Modal Coding Interface")

with tab_pubs:
    st.header("Επιστημονικές Δημοσιεύσεις", anchor=False)
    st.subheader("🌐 Διεθνή Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box"><strong>"Competitive Robotics in Education"</strong><br>ICSE 2025, Lisbon</div>', unsafe_allow_html=True)
    st.subheader("🏛️ Εθνικά Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box" style="border-left-color: #00a0dc;"><strong>"Από τον Αλγόριθμο στη Δημιουργία"</strong><br>ΔΙΠΑΕ, Θεσσαλονίκη</div>', unsafe_allow_html=True)

with tab_app:
    st.header("🔬 AI Robotics Research Interface (Dual-Modal)", anchor=False)
    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        st.subheader("📥 Interaction Input", anchor=False)
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("Researcher ID:", value="Expert_User")
            prompt = st.text_area("Περιγραφή Αποστολής (π.χ. Ακολούθησε τη γραμμή):", height=150)
            btn = st.form_submit_button("🚀 Generate Code & Blocks")

    with col_out:
        st.subheader("🖥️ AI Output (Python & Blocks)", anchor=False)
        if btn and prompt:
            with st.spinner('⏳ Generative AI is working...'):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": """Είσαι ειδικός καθηγητής Maqueen. 
                            Για κάθε ερώτηση, πρέπει να παρέχεις:
                            1. Τον κώδικα Python για Microbit.
                            2. Μια ενότητα που ξεκινά με τη λέξη 'BLOCKS:' όπου θα περιγράφεις τη λογική σε μορφή Pseudo-blocks χρησιμοποιώντας HTML-like ορολογία (π.χ. [ΕΝΑΡΞΗ], [ΕΠΑΝΑΛΗΨΗ]).
                            Απάντα στα Ελληνικά."""},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ans = response.choices[0].message.content
                    
                    # Διαχωρισμός Python και Blocks για το UI
                    if "BLOCKS:" in ans:
                        code_part, block_part = ans.split("BLOCKS:")
                        st.code(code_part, language='python')
                        st.markdown("### 🧩 Visual Logic Representation")
                        st.markdown(f'<div style="background-color:#f0f0f0; padding:15px; border-radius:10px;">{block_part}</div>', unsafe_allow_html=True)
                    else:
                        st.info(ans)
                    
                    # Logging
                    requests.post(SHEETDB_URL, json={"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt, "Answer": ans}]})
                    st.toast("✅ Interaction Logged!")
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

with tab_data:
    st.header("Διαχείριση Δεδομένων", anchor=False)
    st.link_button("📊 Open Database", st.secrets.get("GSHEET_URL_LINK", "https://docs.google.com/spreadsheets/"))

st.divider()
st.caption("PhD v6.1 | Interaction Logging & Visual Logic Synthesis")
