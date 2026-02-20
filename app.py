import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v8.8 | PhD Edition", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ ΠΑΡΑΣΤΑΤΙΚΑ BLOCKS & CLEAN UI ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Scratch-style Blocks */
    .scratch-block {
        color: white; padding: 12px 18px; font-weight: bold; font-family: 'Arial', sans-serif;
        border-radius: 8px; margin-bottom: 4px; position: relative;
        box-shadow: 0 4px 0 rgba(0,0,0,0.2); display: block; width: fit-content; min-width: 220px;
    }
    .scratch-block::before {
        content: ""; position: absolute; top: -8px; left: 25px;
        width: 20px; height: 8px; background: inherit;
        clip-path: polygon(0% 100%, 20% 0%, 80% 0%, 100% 100%);
    }
    .event { background-color: #FFBF00; color: black; border-radius: 15px 15px 4px 4px; }
    .control { background-color: #FFAB19; }
    .motion { background-color: #4C97FF; }
    .sensor { background-color: #5CB1D6; }
    .indent { margin-left: 30px; border-left: 6px solid #FFAB19; padding-left: 10px; }
    
    /* Explanation Styling */
    .stExpander { border: 2px solid #00a0dc; border-radius: 10px; background-color: #f0f9ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Σφάλμα Secrets.")

# 3. Tabs
tab_info, tab_app, tab_data = st.tabs(["📖 Ταυτότητα", "🚀 App (Visual IDE)", "📂 Αρχεία"])

with tab_app:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_py" not in st.session_state:
        st.session_state.last_py = ""

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
                    # Πιο αυστηρό System Prompt για αποφυγή του "AI-style" μπερδέματος
                    sys_prompt = (
                        "Είσαι αυστηρός καθηγητής Maqueen. Απάντα ΜΟΝΟ Ελληνικά.\n"
                        "Format: PYTHON: [Κώδικας] BLOCKS: [HTML Blocks]\n"
                        "Μη βάζεις επεξήγηση σε αυτό το στάδιο.\n"
                        "Χρησιμοποίησε κλάσεις: scratch-block + (event, control, motion, sensor, indent)."
                    )
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    ans = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    if "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        st.session_state.last_py = parts[0].replace("PYTHON:", "").replace("```python", "").replace("```", "").strip()
                        html_blocks = parts[1].strip()
                        
                        st.markdown("#### 🐍 Κώδικας")
                        st.code(st.session_state.last_py, language='python' if lang_choice=="MicroPython" else 'cpp')
                        
                        st.markdown("#### 🧩 Οπτική Λογική")
                        st.markdown(html_blocks, unsafe_allow_html=True)
                        
                        # LOGGING (Μόνο κώδικας)
                        requests.post(SHEETDB_URL, json={
                            "data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt, "Answer": st.session_state.last_py}]
                        })
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

    # --- ΕΠΕΞΗΓΗΣΗ ΣΕ EXPANDER ---
    if st.session_state.last_py:
        with st.expander("💡 Χρειάζεσαι βοήθεια; Πάτα εδώ για την επεξήγηση του κώδικα!"):
            with st.spinner('📚 Μεταφράζω τη λογική...'):
                # Ξεχωριστό prompt για καθαρή, ελληνική επεξήγηση χωρίς HTML
                explain_msg = [
                    {"role": "system", "content": "Είσαι καθηγητής. Εξήγησε τον κώδικα ΜΟΝΟ στα Ελληνικά, απλά και παραστατικά. Μην χρησιμοποιείς HTML ή Blocks στην απάντηση."},
                    {"role": "user", "content": f"Εξήγησε αυτόν τον κώδικα:\n{st.session_state.last_py}"}
                ]
                exp_res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=explain_msg)
                st.write(exp_res.choices[0].message.content)

with tab_data:
    st.header("Ερευνητικά Δεδομένα", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
