import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας (Mobile Friendly & Research Ready)
st.set_page_config(page_title="Ph.D. Research Portal v7.0", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ CLEAN INTERFACE & SCRATCH-STYLE BLOCKS ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp a.header-anchor { display: none; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] { 
        height: auto; min-height: 45px; font-size: 14px; padding: 5px 15px; font-weight: bold;
    }

    .pub-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
    }

    /* Scratch Blocks Styling */
    .scratch-block {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: bold; font-size: 13px; padding: 8px 12px; margin-bottom: 4px;
        width: fit-content; max-width: 100%; position: relative; color: white;
        box-shadow: 0 3px 0 rgba(0,0,0,0.2); display: block;
    }
    .scratch-block::before {
        content: ""; position: absolute; top: -8px; left: 15px;
        width: 15px; height: 8px; background: inherit;
        clip-path: polygon(0% 100%, 20% 0%, 80% 0%, 100% 100%);
    }

    .event { background-color: #FFBF00; border-radius: 15px 15px 4px 4px; color: black; border: 1px solid #E6AC00; } 
    .control { background-color: #FFAB19; border-radius: 4px; border: 1px solid #CF8B17; }
    .motion { background-color: #4C97FF; border-radius: 4px; border: 1px solid #3373CC; }
    .indent { margin-left: 20px; border-left: 6px solid #FFAB19; padding-left: 5px; margin-top: -2px; }
    
    @media (max-width: 768px) {
        .stColumns { flex-direction: column !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("⚠️ Σύνδεση Read-Only. Ελέγξτε τα Secrets.")

# 3. Δομή Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (IDE)", "📂 Αρχεία"
])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης: Μοντέλα, Μέθοδοι και Επιπτώσεις στη Σύγχρονη Εκπαίδευση")

with tab_progress:
    st.header("Χρονοδιάγραμμα", anchor=False)
    st.write("- [x] 1ο Έτος: Βιβλιογραφία & Υπόμνημα")
    st.write("- [x] 2ο Έτος: ironbrick v7.0 (Context-Aware Logging & Action Analytics)")

with tab_pubs:
    st.header("Επιστημονικό Έργο", anchor=False)
    st.subheader("🌐 Διεθνή Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box"><strong>Competitive Robotics in Education</strong> (ICSE 2025)<br><a href="#">🔗 URL Δημοσίευσης</a></div>', unsafe_allow_html=True)
    st.subheader("🏛️ Εθνικά Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box" style="border-left-color: #00a0dc;"><strong>Από τον Αλγόριθμο στη Δημιουργία</strong> (ΔΙΠΑΕ)<br><a href="#">🔗 URL Δημοσίευσης</a></div>', unsafe_allow_html=True)

with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    
    # Αρχικοποίηση Ιστορικού
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Settings Row
    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα:", ["MicroPython & Blocks", "Arduino C"])
    with col_set2:
        action_type = st.radio("Τύπος Ενέργειας:", ["Νέα Αποστολή", "Διόρθωση / Debugging"], horizontal=True)

    if st.button("🗑️ Καθαρισμός Συνομιλίας"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Researcher_1")
            prompt = st.text_area("Περιγράψτε την αποστολή ή το πρόβλημα:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση")

    with col_out:
        if submit and prompt:
            # Προσθήκη στο ιστορικό
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner('⏳ Επεξεργασία AI βάσει ιστορικού...'):
                try:
                    # System Prompt με Knowledge Injection & Action Context
                    if lang_choice == "MicroPython & Blocks":
                        sys_prompt = (
                            f"Είσαι καθηγητής Maqueen. Πρόθεση χρήστη: {action_type}.\n"
                            "Χρησιμοποίησε τη βιβλιοθήκη 'maqueen'.\n"
                            "Δώσε ΠΑΝΤΑ: 1. PYTHON: [Κώδικας] 2. BLOCKS: [HTML Blocks].\n"
                            "Παράδειγμα: <div class='scratch-block event'>🏁 Όταν ξεκινήσει</div>"
                        )
                    else:
                        sys_prompt = f"Είσαι ειδικός Arduino Maqueen (<DFRobot_Maqueen.h>). Πρόθεση: {action_type}. Δώσε μόνο κώδικα C++."

                    # Σύνθεση μηνυμάτων
                    api_messages = [{"role": "system", "content": sys_prompt}] + st.session_state.messages

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=api_messages
                    )
                    ans = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    # Καθαρισμός και Προβολή
                    if lang_choice == "MicroPython & Blocks" and "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        py_code = parts[0].replace("PYTHON:", "").replace("```python", "").replace("```", "").strip()
                        html_blocks = parts[1].replace("```html", "").replace("```", "").strip()
                        
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(py_code, language='python')
                        st.markdown("#### 🧩 Visual Logic (Scratch-Style)")
                        st.markdown(html_blocks, unsafe_allow_html=True)
                    else:
                        st.markdown("#### ⚙️ Arduino C Code")
                        st.code(ans.replace("```cpp", "").replace("```", "").strip(), language='cpp')
                    
                    # LOGGING ΜΕ ACTION TYPE
                    # LOGGING ΜΕ ΟΛΑ ΤΑ ΠΕΔΙΑ (Συμπεριλαμβανομένου του Answer)
log_data = {
    "data": [{
        "Timestamp": str(datetime.datetime.now()), 
        "Student_ID": u_id, 
        "Action": action_type,
        "Language": lang_choice,
        "Prompt": prompt,
        "Answer": ans  # <--- Προστέθηκε το πεδίο Answer
    }]
}
requests.post(SHEETDB_URL, json=log_data)
st.toast(f"✅ Καταγράφηκε επιτυχώς!")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab_data:
    st.header("Βάση Δεδομένων", anchor=False)
    st.write("Στο Google Sheet θα βρείτε τη στήλη 'Action' για τον διαχωρισμό New Task vs Debugging.")
    st.link_button("📊 Άνοιγμα Database", st.secrets.get("GSHEET_URL_LINK", "#"))

st.divider()
st.caption("PhD ironbrick v7.0 | Advanced Research Analytics & Multi-modal IDE")

