import streamlit as st
from openai import OpenAI
import datetime
import requests
import streamlit.components.v1 as components

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.4 | Official Fix", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ ΤΗΝ ΤΑΥΤΟΤΗΤΑ ΤΟΥ SITE ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    .pub-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .main-btn {
        background-color: #00a0dc; color: white; padding: 20px;
        border-radius: 10px; text-align: center; display: block;
        text-decoration: none; font-weight: bold; font-size: 20px;
        margin-top: 20px; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets.")

# 3. Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (Official Bridge)", "📂 Αρχεία"
])

# --- TAB 1, 2, 3 (Ως είχαν) ---
with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης (Ph.D. Candidate)")

# --- TAB 4: Η ΕΦΑΡΜΟΓΗ (The Official Bridge) ---
with tab_app:
    st.header("🔬 Official MakeCode Research Bridge", anchor=False)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα:", ["MicroPython", "Arduino C"])
    with col_set2:
        action_type = st.radio("Ενέργεια:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση & Μεταφορά")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Παραγωγή επίσημου κώδικα...'):
                try:
                    sys_prompt = "Είσαι ειδικός Maqueen. Δώσε ΜΟΝΟ τον κώδικα Python (MicroPython). Χωρίς κείμενο ή XML."
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    py_code = response.choices[0].message.content.replace("```python", "").replace("```", "").strip()
                    st.session_state.messages.append({"role": "assistant", "content": py_code})

                    # --- ΠΡΟΒΟΛΗ ΚΩΔΙΚΑ ---
                    st.markdown("#### 🐍 Generated MicroPython")
                    st.code(py_code, language='python')
                    
                    # --- THE OFFICIAL BRIDGE SOLUTION ---
                    st.markdown("#### 🧩 Official MakeCode Integration")
                    
                    # Δημιουργία του URL που ανοίγει τον κώδικα απευθείας στον Editor
                    makecode_magic_url = f"https://makecode.microbit.org/#pub:_python:{requests.utils.quote(py_code)}"
                    
                    st.markdown(f"""
                        <a href="{makecode_magic_url}" target="_blank" class="main-btn">
                            🚀 ΑΝΟΙΓΜΑ ΣΤΟ OFFICIAL MAKECODE (BLOCKS)
                        </a>
                        <p style='text-align:center; font-size:12px; color:gray; margin-top:5px;'>
                            Κάντε κλικ για να δείτε τα Blocks και τον Simulator στο επίσημο περιβάλλον.
                        </p>
                    """, unsafe_allow_html=True)
                    
                    # Προσθήκη Simulator (ως fallback)
                    st.info("💡 Μπορείτε να κάνετε επικόλληση τον κώδικα στον επίσημο editor για πλήρη έλεγχο.")
                    
                    # --- SAFE LOGGING (Fix για Screenshot 2 & 3) ---
                    log_entry = {
                        "data": [{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": str(u_id),
                            "Action": str(action_type),
                            "Prompt": str(prompt),
                            "Answer": str(py_code).replace('"', "'")
                        }]
                    }
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast("✅ Καταγράφηκε!")

                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
