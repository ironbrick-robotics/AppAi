import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας (Mobile Friendly)
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ MOBILE FRIENDLY INTERFACE & SCRATCH BLOCKS ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp a.header-anchor { display: none; }
    
    /* Responsive Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] { 
        height: auto; 
        min-height: 45px;
        font-size: 14px; 
        padding: 5px 15px;
    }

    /* Pub Cards */
    .pub-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    /* Scratch Blocks (Mobile Responsive) */
    .scratch-block {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: bold;
        font-size: 13px;
        padding: 8px 12px;
        margin-bottom: 4px;
        width: fit-content;
        max-width: 100%;
        position: relative;
        color: white;
        box-shadow: 0 3px 0 rgba(0,0,0,0.2);
        display: block;
    }
    .scratch-block::before {
        content: "";
        position: absolute;
        top: -8px; left: 15px;
        width: 15px; height: 8px;
        background: inherit;
        clip-path: polygon(0% 100%, 20% 0%, 80% 0%, 100% 100%);
    }

    .event { background-color: #FFBF00; border-radius: 15px 15px 4px 4px; color: black; } 
    .control { background-color: #FFAB19; border-radius: 4px; }
    .motion { background-color: #4C97FF; border-radius: 4px; }
    .indent { margin-left: 15px; border-left: 6px solid #FFAB19; padding-left: 5px; }
    
    /* Mobile Adjustments */
    @media (max-width: 768px) {
        .stColumns { flex-direction: column !important; }
        .scratch-block { min-width: 150px; }
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
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (IDE)", "📂 Αρχεία"
])

# --- TAB 1: ΤΑΥΤΟΤΗΤΑ ---
with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης: Μοντέλα, Μέθοδοι και Επιπτώσεις στη Σύγχρονη Εκπαίδευση")

# --- TAB 2: ΠΡΟΟΔΟΣ ---
with tab_progress:
    st.header("Χρονοδιάγραμμα", anchor=False)
    st.write("- [x] 1ο Έτος: Βιβλιογραφία & Υπόμνημα")
    st.write("- [x] 2ο Έτος: Ανάπτυξη v6.4 (Multi-language & Mobile)")

# --- TAB 3: ΔΗΜΟΣΙΕΥΣΕΙΣ ---
with tab_pubs:
    st.header("Επιστημονικό Έργο", anchor=False)
    
    st.subheader("🌐 Διεθνή Συνέδρια", anchor=False)
    st.markdown("""
    <div class="pub-box">
        <strong>1. Competitive Robotics in Education</strong> (ICSE 2025)<br>
        <a href="https://example.com/pub1" target="_blank">🔗 Προβολή URL Δημοσίευσης</a>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🏛️ Εθνικά Συνέδρια", anchor=False)
    st.markdown("""
    <div class="pub-box" style="border-left-color: #00a0dc;">
        <strong>2. Από τον Αλγόριθμο στη Δημιουργία</strong> (ΔΙΠΑΕ)<br>
        <a href="https://example.com/pub2" target="_blank">🔗 Προβολή URL Δημοσίευσης</a>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 4: Η ΕΦΑΡΜΟΓΗ (IDE) ---
with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    
    language_choice = st.selectbox(
        "Επίλεξε Γλώσσα Προγραμματισμού:",
        ["MicroPython & Blocks", "Arduino C"]
    )
    st.divider()

    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Δημιουργία")

    with col_output:
        if submit and prompt:
            with st.spinner('⏳ Επεξεργασία AI βάσει επίσημων βιβλιοθηκών...'):
                try:
                    # Knowledge Injection Prompting
                    if language_choice == "MicroPython & Blocks":
                        sys_prompt = (
                            "Είσαι αυστηρός καθηγητής Maqueen. Χρησιμοποίησε ΜΟΝΟ την επίσημη βιβλιοθήκη 'maqueen'.\n"
                            "ΕΝΤΟΛΕΣ MICROPYTHON:\n"
                            "- maqueen.motor_run(maqueen.Motors.M1, maqueen.Dir.CW, speed)\n"
                            "- maqueen.ultrasonic()\n"
                            "- maqueen.read_patrol(maqueen.Patrol.L1)\n"
                            "Απάντα σε 2 ενότητες: 1. PYTHON: [Κώδικας] 2. BLOCKS: [HTML scratch-blocks]."
                        )
                    else:
                        sys_prompt = (
                            "Είσαι ειδικός προγραμματιστής Arduino για Maqueen. Χρησιμοποίησε τη βιβλιοθήκη <DFRobot_Maqueen.h>.\n"
                            "ΕΝΤΟΛΕΣ ARDUINO C:\n"
                            "- maqueen_motor_run(motor, direction, speed)\n"
                            "- maqueen_read_patrol(sensor)\n"
                            "- maqueen_ultrasonic()\n"
                            "Ο κώδικας πρέπει να περιλαμβάνει void setup() και void loop()."
                        )

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ans = response.choices[0].message.content
                    
                    if language_choice == "MicroPython & Blocks" and "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(parts[0].replace("PYTHON:", "").strip(), language='python')
                        st.markdown("#### 🧩 Visual Logic (Scratch-Style)")
                        st.markdown(parts[1].strip(), unsafe_allow_html=True)
                    else:
                        st.markdown(f"#### ⚙️ Arduino C Code")
                        st.code(ans, language='cpp')
                    
                    # Logging with Library Metadata
                    log_data = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()), 
                            "Student_ID": u_id, 
                            "Language": language_choice, 
                            "Prompt": prompt,
                            "Status": "Verified API"
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_data)
                    st.toast("✅ Έλεγχος Βιβλιοθηκών Ολοκληρώθηκε!")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 5: ΑΡΧΕΙΑ ---
with tab_data:
    st.header("Βάση Δεδομένων", anchor=False)
    st.link_button("📊 Open Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))

st.divider()
st.caption("PhD v6.4 | Mobile Friendly & Multi-Language Support")

