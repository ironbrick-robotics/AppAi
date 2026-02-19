import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας (Mobile Friendly & Professional)
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ CLEAN INTERFACE & STABLE SCRATCH BLOCKS ---
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
    st.write("- [x] 2ο Έτος: ironbrick v6.6 (Stable Visual Logic & Multi-modal)")

with tab_pubs:
    st.header("Επιστημονικό Έργο", anchor=False)
    st.subheader("🌐 Διεθνή Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box"><strong>Competitive Robotics in Education</strong> (ICSE 2025)<br><a href="#">🔗 URL Δημοσίευσης</a></div>', unsafe_allow_html=True)
    st.subheader("🏛️ Εθνικά Συνέδρια", anchor=False)
    st.markdown('<div class="pub-box" style="border-left-color: #00a0dc;"><strong>Από τον Αλγόριθμο στη Δημιουργία</strong> (ΔΙΠΑΕ)<br><a href="#">🔗 URL Δημοσίευσης</a></div>', unsafe_allow_html=True)

with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    lang_choice = st.selectbox("Γλώσσα Προγραμματισμού:", ["MicroPython & Blocks", "Arduino C"])
    st.divider()

    col_in, col_out = st.columns([1, 1])
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Δημιουργία")

    with col_out:
        if submit and prompt:
            with st.spinner('⏳ Επεξεργασία AI...'):
                try:
                    # Θωρακισμένο Prompt με Few-Shot Examples
                    if lang_choice == "MicroPython & Blocks":
                        sys_prompt = (
                            "Είσαι κορυφαίος μηχανικός της DFRobot. "
                            "Γνωρίζεις όλες τις βιβλιοθήκες του οικοσυστήματος (DFRobot_Maqueen, DFRobot_HuskyLens, DFRobot_NeoPixel).\n"
                            "Αν ο χρήστης ζητήσει προηγμένες λειτουργίες (π.χ. αναγνώριση χρωμάτων), χρησιμοποίησε τις αντίστοιχες βιβλιοθήκες της DFRobot.\n"
                            "Ο κώδικας πρέπει να είναι βελτιστοποιημένος για το Maqueen Plus ή το Maqueen Lite."
                            "ΠΡΕΠΕΙ ΝΑ ΠΑΡΑΓΕΙΣ ΠΑΝΤΑ ΔΥΟ ΕΝΟΤΗΤΕΣ:\n"
                            "1. PYTHON: [Κώδικας]\n"
                            "2. BLOCKS: [HTML Blocks]\n\n"
                            "ΠΑΡΑΔΕΙΓΜΑ BLOCKS:\n"
                            "<div class='scratch-block event'>🏁 Όταν ξεκινήσει</div>\n"
                            "<div class='scratch-block control'>⚙️ Για πάντα</div>\n"
                            "<div class='indent'><div class='scratch-block motion'>🚀 motor_run(M1, CW, 30)</div></div>"
                        )
                    else:
                        sys_prompt = "Είσαι ειδικός Arduino Maqueen. Χρησιμοποίησε <DFRobot_Maqueen.h>. Δώσε μόνο τον κώδικα C++."

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}]
                    )
                    ans = response.choices[0].message.content
                    
                    if lang_choice == "MicroPython & Blocks" and "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        # Καθαρισμός κώδικα από backticks
                        py_code = parts[0].replace("PYTHON:", "").replace("```python", "").replace("```", "").strip()
                        html_blocks = parts[1].replace("```html", "").replace("```", "").strip()
                        
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(py_code, language='python')
                        st.markdown("#### 🧩 Visual Logic (Scratch-Style)")
                        st.markdown(html_blocks, unsafe_allow_html=True)
                    else:
                        st.code(ans.replace("```cpp", "").replace("```", "").strip(), language='cpp')
                    
                    requests.post(SHEETDB_URL, json={"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt}]})
                    st.toast("✅ Logged!")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab_data:
    st.header("Βάση Δεδομένων", anchor=False)
    st.link_button("📊 Open Database", st.secrets.get("GSHEET_URL_LINK", "#"))

st.divider()
st.caption("PhD v6.7 | AI Robotics Research Interface")

