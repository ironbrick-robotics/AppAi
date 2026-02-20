import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας (Mobile Friendly & Research Ready)
st.set_page_config(page_title="Ph.D. Research Portal v7.1", page_icon="🎓", layout="wide")

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

    /* Scratch Blocks Styling (Stable Visual Logic) */
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
    .sensor { background-color: #5CB1D6; border-radius: 4px; border: 1px solid #478BA8; }
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
    st.warning("⚠️ Σύνδεση Read-Only. Ελέγξτε τα Secrets (GROQ_API_KEY, GSHEET_URL).")

# 3. Δομή Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (IDE)", "📂 Αρχεία"
])

# --- TAB 1: ΤΑΥΤΟΤΗΤΑ ---
with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης: Μοντέλα, Μέθοδοι και Επιπτώσεις στη Σύγχρονη Εκπαίδευση")
    st.write("**Ερευνητής:** PhD Candidate")

# --- TAB 2: ΠΡΟΟΔΟΣ ---
with tab_progress:
    st.header("Χρονοδιάγραμμα", anchor=False)
    st.write("- [x] 1ο Έτος: Βιβλιογραφική Ανασκόπηση")
    st.write("- [x] 2ο Έτος: ironbrick v7.1 (Advanced Analytics & Dual-Modal Context)")

# --- TAB 3: ΔΗΜΟΣΙΕΥΣΕΙΣ ---
with tab_pubs:
    st.header("Επιστημονικό Έργο", anchor=False)
    st.subheader("🌐 Διεθνή Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box"><strong>Competitive Robotics in Education</strong> (ICSE 2025)<br><a href="#">🔗 URL Δημοσίευσης</a></div>', unsafe_allow_html=True)
    st.subheader("🏛️ Εθνικά Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box" style="border-left-color: #00a0dc;"><strong>Από τον Αλγόριθμο στη Δημιουργία</strong> (ΔΙΠΑΕ)<br><a href="#">🔗 URL Δημοσίευσης</a></div>', unsafe_allow_html=True)

# --- TAB 4: Η ΕΦΑΡΜΟΓΗ (Advanced Research IDE) ---
with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    
    # Διαχείριση Ιστορικού Συνομιλίας
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Settings Row (Mobile Friendly)
    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα Προγραμματισμού:", ["MicroPython & Blocks", "Arduino C"])
    with col_set2:
        action_type = st.radio("Τύπος Ενέργειας (για το Log):", ["Νέα Αποστολή", "Διόρθωση / Debugging"], horizontal=True)

    if st.button("🗑️ Καθαρισμός Ιστορικού"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        st.subheader("📥 Input", anchor=False)
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Researcher_1")
            prompt = st.text_area("Περιγράψτε την αποστολή ή το πρόβλημα:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση & Καταγραφή")

    with col_out:
        st.subheader("🖥️ Output", anchor=False)
        if submit and prompt:
            # Αποθήκευση ερώτησης στο context
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner('⏳ Το AI συνθέτει τον κώδικα...'):
                try:
                    # System Prompt με Knowledge Injection & Context Awareness
                    if lang_choice == "MicroPython & Blocks":
                        sys_prompt = (
                            f"Είσαι καθηγητής Maqueen. Πρόθεση χρήστη: {action_type}. "
                            "Χρησιμοποίησε ΜΟΝΟ τη βιβλιοθήκη 'maqueen'. "
                            "Δώσε ΠΑΝΤΑ: 1. PYTHON: [Κώδικας] 2. BLOCKS: [HTML Blocks]. "
                            "Format Blocks: <div class='scratch-block event'>🏁 Όνομα</div>"
                        )
                    else:
                        sys_prompt = f"Είσαι ειδικός Arduino Maqueen (<DFRobot_Maqueen.h>). Πρόθεση: {action_type}. Δώσε μόνο κώδικα C++."

                    # Κλήση API με όλο το ιστορικό
                    messages_to_send = [{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages_to_send
                    )
                    ans = response.choices[0].message.content
                    
                    # Αποθήκευση απάντησης στο context
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    # Προβολή Αποτελεσμάτων
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
                        final_cpp = ans.replace("```cpp", "").replace("```", "").strip()
                        st.code(final_cpp, language='cpp')
                    
                    # ΠΛΗΡΕΣ LOGGING ΣΤΟ GOOGLE SHEETS
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()), 
                            "Student_ID": u_id, 
                            "Action": action_type,
                            "Language": lang_choice,
                            "Prompt": prompt,
                            "Answer": ans  # Καταγραφή της πλήρους απάντησης του AI
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast(f"✅ Επιτυχής καταγραφή: {action_type}")

                except Exception as e:
                    st.error(f"Σφάλμα Επικοινωνίας: {e}")

# --- TAB 5: ΔΕΔΟΜΕΝΑ ---
with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.write("Όλες οι αλληλεπιδράσεις (Prompts & Answers) αποθηκεύονται αυτόματα για ανάλυση.")
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))

st.divider()
st.caption("PhD ironbrick v7.1 | Interaction Analytics | DFRobot Ecosystem Support")
