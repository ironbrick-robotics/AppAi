import streamlit as st
from openai import OpenAI
import datetime
import requests
import streamlit.components.v1 as components

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal v7.3", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ ΤΟ INTERFACE ---
st.markdown("""
    <style>
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 12px; flex-wrap: wrap; }
    .pub-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
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

# 3. Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (IDE)", "📂 Αρχεία"
])

# --- TAB 4: Η ΕΦΑΡΜΟΓΗ (BLOCKLY EDITION) ---
with tab_app:
    st.header("🔬 Official Blockly Research IDE", anchor=False)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα:", ["MicroPython & Blocks", "Arduino C"])
    with col_set2:
        action_type = st.radio("Τύπος Ενέργειας:", ["Νέα Αποστολή", "Διόρθωση / Debugging"], horizontal=True)

    st.divider()

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Researcher_1")
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση & Καταγραφή")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner('⏳ Το AI δημιουργεί XML Blocks...'):
                try:
                    # SYSTEM PROMPT ΓΙΑ XML ΠΑΡΑΓΩΓΗ
                    if lang_choice == "MicroPython & Blocks":
                        sys_prompt = (
                            f"Είσαι καθηγητής Maqueen. Πρόθεση: {action_type}. "
                            "ΠΡΕΠΕΙ ΝΑ ΔΩΣΕΙΣ ΠΑΝΤΑ ΔΥΟ ΕΝΟΤΗΤΕΣ:\n"
                            "1. PYTHON: [Κώδικας]\n"
                            "2. BLOCKS: [XML κώδικας για Blockly]\n"
                            "Παράδειγμα XML: <xml><block type='controls_repeat_ext'><value name='TIMES'><shadow type='math_number'><field name='NUM'>10</field></shadow></value></block></xml>"
                        )
                    else:
                        sys_prompt = f"Είσαι ειδικός Arduino Maqueen. Δώσε μόνο κώδικα C++."

                    api_messages = [{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=api_messages)
                    ans = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    if lang_choice == "MicroPython & Blocks" and "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        py_code = parts[0].replace("PYTHON:", "").strip()
                        xml_code = parts[1].replace("```xml", "").replace("```", "").strip()
                        
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(py_code, language='python')
                        
                        # --- ΕΠΙΣΗΜΟ BLOCKLY RENDERING ---
                        st.markdown("#### 🧩 Official Blockly Blocks")
                        blockly_html = f"""
                        <script src="https://unpkg.com/blockly/blockly.min.js"></script>
                        <div id="blocklyDiv" style="height: 300px; width: 100%; border-radius:10px;"></div>
                        <xml id="toolbox" style="display: none"><block type="controls_repeat_ext"></block></xml>
                        <script>
                            var workspace = Blockly.inject('blocklyDiv', {{readOnly: true, scrollbars: true}});
                            var xml_text = `{xml_code}`;
                            var xml = Blockly.utils.xml.textToDom(xml_text);
                            Blockly.Xml.domToWorkspace(xml, workspace);
                        </script>
                        """
                        components.html(blockly_html, height=320)
                    else:
                        st.code(ans.strip(), language='cpp')
                    
                    # LOGGING
                    requests.post(SHEETDB_URL, json={"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Action": action_type, "Prompt": prompt, "Answer": ans}]})
                    st.toast("✅ Καταγράφηκε!")
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")

# (Τα υπόλοιπα Tabs παραμένουν ως έχουν)
