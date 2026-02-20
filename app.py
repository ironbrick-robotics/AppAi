import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.7 | Educational IDE", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ ΠΑΡΑΣΤΑΤΙΚΑ BLOCKS & UI ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    
    /* Scratch-style Blocks με Puzzle 'κουμπώματα' */
    .block-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin-bottom: 20px; }
    .scratch-block {
        color: white; padding: 10px 15px; font-weight: bold; font-size: 14px;
        border-radius: 8px; margin-bottom: 2px; position: relative;
        box-shadow: 0 4px 0 rgba(0,0,0,0.2); display: block; width: fit-content; min-width: 200px;
    }
    /* Το κούμπωμα (notch) στο πάνω μέρος */
    .scratch-block::before {
        content: ""; position: absolute; top: -8px; left: 20px;
        width: 16px; height: 8px; background: inherit;
        clip-path: polygon(0% 100%, 20% 0%, 80% 0%, 100% 100%);
    }
    /* Χρώματα κατηγοριών */
    .event { background-color: #FFBF00; color: black; border-radius: 15px 15px 4px 4px; }
    .control { background-color: #FFAB19; }
    .motion { background-color: #4C97FF; }
    .sensor { background-color: #5CB1D6; }
    .indent { margin-left: 25px; border-left: 6px solid #FFAB19; padding-left: 10px; margin-top: -2px; }
    
    .explanation-box {
        background-color: #f0f7ff; border-left: 5px solid #007bff;
        padding: 15px; border-radius: 5px; margin-top: 10px; font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets (GROQ_API_KEY & GSHEET_URL).")

# 3. Tabs
tab_info, tab_app, tab_data = st.tabs(["📖 Ταυτότητα", "🚀 App (Visual IDE)", "📂 Αρχεία"])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική & Τεχνητή Νοημοσύνη (Ph.D. Research Tool)")

with tab_app:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_ans" not in st.session_state:
        st.session_state.last_ans = ""

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            lang_choice = st.selectbox("Γλώσσα:", ["MicroPython", "Arduino C"])
            prompt = st.text_area("Τι θέλεις να κάνει το Maqueen;", height=120)
            submit = st.form_submit_button("🚀 Δημιουργία")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Σχεδιασμός...'):
                try:
                    sys_prompt = (
                        "Είσαι καθηγητής Maqueen. Δώσε ΠΑΝΤΑ:\n"
                        "1. PYTHON: [Κώδικας]\n"
                        "2. BLOCKS: [HTML Blocks με κλάσεις scratch-block και event/control/motion/indent].\n"
                        "Κάνε τα blocks πολύ παραστατικά."
                    )
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    st.session_state.last_ans = response.choices[0].message.content
                    ans = st.session_state.last_ans
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    if "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        py_code = parts[0].replace("PYTHON:", "").strip()
                        html_blocks = parts[1].strip()
                        
                        st.markdown("#### 🐍 Κώδικας")
                        st.code(py_code, language='python' if lang_choice=="MicroPython" else 'cpp')
                        
                        st.markdown("#### 🧩 Οπτική Λογική")
                        st.markdown(f'<div class="block-container">{html_blocks}</div>', unsafe_allow_html=True)
                        
                        # LOGGING: ΜΟΝΟ ΚΩΔΙΚΑΣ (Όχι HTML/Blocks)
                        log_entry = {
                            "data": [{
                                "Timestamp": str(datetime.datetime.now()),
                                "Student_ID": str(u_id),
                                "Language": lang_choice,
                                "Prompt": str(prompt),
                                "Answer": str(py_code).replace('"', "'")
                            }]
                        }
                        requests.post(SHEETDB_URL, json=log_entry)
                        st.toast("✅ Καταγράφηκε!")

                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

    # --- ΚΟΥΜΠΙ ΕΠΕΞΗΓΗΣΗΣ (Εκτός Form για αμεσότητα) ---
    if st.session_state.last_ans:
        if st.button("💡 Εξήγησέ μου τον κώδικα"):
            with st.spinner('📚 Προετοιμασία επεξήγησης...'):
                explain_prompt = f"Εξήγησε με απλά λόγια σε έναν μαθητή τι κάνει αυτός ο κώδικας:\n{st.session_state.last_ans}"
                exp_res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": explain_prompt}]
                )
                st.markdown(f'<div class="explanation-box">{exp_res.choices[0].message.content}</div>', unsafe_allow_html=True)

with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
