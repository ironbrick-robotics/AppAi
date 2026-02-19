import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ CLEAN INTERFACE & SCRATCH-STYLE BLOCKS ---
st.markdown("""
    <style>
    /* Καθαρισμός Streamlit UI */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp a.header-anchor { display: none; }
    
    /* Ρυθμίσεις Tabs */
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

    /* --- SCRATCH / SPIKE PRIME BLOCKS CSS --- */
    .scratch-block {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: bold;
        font-size: 14px;
        padding: 10px 18px;
        margin-bottom: 4px;
        width: fit-content;
        min-width: 200px;
        position: relative;
        color: white;
        box-shadow: 0 3px 0 rgba(0,0,0,0.2);
        display: block;
    }

    /* Το "δόντι" (Notch) στην κορυφή του block */
    .scratch-block::before {
        content: "";
        position: absolute;
        top: -8px;
        left: 20px;
        width: 18px;
        height: 8px;
        background: inherit;
        clip-path: polygon(0% 100%, 20% 0%, 80% 0%, 100% 100%);
    }

    /* Χρώματα ανά κατηγορία */
    .event { background-color: #FFBF00; border-radius: 20px 20px 4px 4px; color: black; border: 1px solid #E6AC00; } 
    .control { background-color: #FFAB19; border-radius: 4px; border: 1px solid #CF8B17; }
    .motion { background-color: #4C97FF; border-radius: 4px; border: 1px solid #3373CC; }
    .sensor { background-color: #5CB1D6; border-radius: 4px; border: 1px solid #478BA8; }
    
    /* Εσοχή για τα Loops/Nested Blocks */
    .indent { margin-left: 25px; border-left: 8px solid #FFAB19; padding-left: 5px; margin-top: -2px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("⚠️ Σύνδεση σε λειτουργία Read-Only. Ελέγξτε τα Secrets.")

# 3. Δομή Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα Έρευνας", 
    "📈 Πρόοδος", 
    "📚 Δημοσιεύσεις", 
    "🚀 App (IDE)", 
    "📂 Αρχεία"
])

# --- TAB 1: ΤΑΥΤΟΤΗΤΑ ---
with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.subheader("Τίτλος Διδακτορικού", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης: Μοντέλα, Μέθοδοι και Επιπτώσεις στη Σύγχρονη Εκπαίδευση")
    st.write("**Ερευνητική Περιοχή:** Python Software Development, System Prompting & Interaction Logging.")

# --- TAB 2: ΠΡΟΟΔΟΣ ---
with tab_progress:
    st.header("Χρονοδιάγραμμα & Ορόσημα", anchor=False)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1ο Έτος\n- [x] Βιβλιογραφική Ανασκόπηση\n- [x] Κατάθεση Υπομνήματος")
    with col2:
        st.markdown("### 2ο Έτος\n- [x] Ανάπτυξη Λογισμικού (v6.0)\n- [ ] Dual-Modal Coding Interface")
    with col3:
        st.markdown("### 3ο Έτος\n- [ ] Τελική Συλλογή Δεδομένων\n- [ ] Συγγραφή Διατριβής")

# --- TAB 3: ΔΗΜΟΣΙΕΥΣΕΙΣ ---
with tab_pubs:
    st.header("Επιστημονικές Δημοσιεύσεις", anchor=False)
    
    st.subheader("🌐 Διεθνή Συνέδρια με Κριτές", anchor=False)
    st.markdown("""
    <div class="pub-box">
        <strong>1. "Competitive Robotics in Education: Didactic Approach and Technological Analysis of a Mini Sumo Robot"</strong><br>
        4th International Conference on Sport & Education (ICSE 2025), Lisbon, Portugal.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🏛️ Εθνικά Συνέδρια & Ημερίδες", anchor=False)
    st.markdown("""
    <div class="pub-box" style="border-left-color: #00a0dc;">
        <strong>2. "Από τον Αλγόριθμο στη Δημιουργία: Ενσωμάτωση της Παραγωγικής ΤΝ στην Εκπαίδευση"</strong><br>
        Τεχνητή Νοημοσύνη και Καινοτομία στην Εκπαίδευση, ΔΙΠΑΕ, Θεσσαλονίκη.
    </div>
    """, unsafe_allow_html=True)

# --- TAB 4: Η ΕΦΑΡΜΟΓΗ (IDE) ---
with tab_app:
    st.header("🔬 AI Robotics Research Interface (Dual-Modal)", anchor=False)
    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        st.subheader("📥 Interaction Input", anchor=False)
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("Researcher ID:", value="Expert_User")
            prompt = st.text_area("Περιγράψτε την αποστολή του Maqueen:", height=150)
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
                            Πρέπει να παρέχεις ΠΑΝΤΑ δύο ενότητες στην απάντησή σου:
                            
                            1. Ξεκίνα με τη λέξη 'PYTHON:' και δώσε τον κώδικα MicroPython.
                            2. Μετά, γράψε τη λέξη 'BLOCKS:' και σχεδίασε τη λογική χρησιμοποιώντας ΑΠΟΚΛΕΙΣΤΙΚΑ αυτά τα HTML tags:
                            - <div class='scratch-block event'>🏁 Όνομα Συμβάντος</div> (για την αρχή)
                            - <div class='scratch-block motion'>🚀 Εντολή Κίνησης</div> (για κίνηση)
                            - <div class='scratch-block control'>⚙️ Εντολή Ελέγχου</div> (για repeat/if)
                            - Χρησιμοποίησε <div class='indent'>...</div> για να βάζεις εντολές μέσα σε βρόχους (loops).
                            
                            Απάντα στα Ελληνικά."""},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ans = response.choices[0].message.content
                    
                    # Διαχωρισμός και Απεικόνιση
                    if "BLOCKS:" in ans:
                        code_part = ans.split("BLOCKS:")[0].replace("PYTHON:", "").strip()
                        block_part = ans.split("BLOCKS:")[1].strip()
                        
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(code_part, language='python')
                        
                        st.markdown("#### 🧩 Visual Logic (Scratch-Style)")
                        st.markdown(block_part, unsafe_allow_html=True)
                    else:
                        st.info(ans)
                    
                    # Logging
                    requests.post(SHEETDB_URL, json={"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt, "Answer": ans}]})
                    st.toast("✅ Interaction Logged!")
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

# --- TAB 5: ΑΡΧΕΙΑ ---
with tab_data:
    st.header("Διαχείριση Ερευνητικών Δεδομένων", anchor=False)
    st.write("Όλες οι αλληλεπιδράσεις καταγράφονται αυτόματα στο Google Sheets για ποιοτική ανάλυση.")
    st.link_button("📊 Άνοιγμα Database", st.secrets.get("GSHEET_URL_LINK", "https://docs.google.com/spreadsheets/"))

st.divider()
st.caption("PhD v6.3 | Hybrid Visual Research Lab")
