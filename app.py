import streamlit as st
from openai import OpenAI
import datetime
import requests
import streamlit.components.v1 as components
import json

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="ironbrick v7.8 | Master Research IDE", page_icon="🎓", layout="wide")

# --- CSS ΕΠΑΝΑΦΟΡΑΣ ---
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

# 2. Σύνδεση
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("⚠️ Ελέγξτε τα Secrets.")

# 3. Tabs
tab_info, tab_progress, tab_pubs, tab_app, tab_data = st.tabs([
    "📖 Ταυτότητα", "📈 Πρόοδος", "📚 Δημοσιεύσεις", "🚀 App (Full IDE)", "📂 Αρχεία"
])

with tab_info:
    st.header("Ερευνητικό Υπόμνημα", anchor=False)
    st.info("Εκπαιδευτική Ρομποτική με Ενσωμάτωση Τεχνητής Νοημοσύνης (Ph.D. Candidate)")

with tab_app:
    st.header("🔬 AI Robotics Research Interface", anchor=False)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα:", ["MicroPython & Blocks", "Arduino C"])
    with col_set2:
        action_type = st.radio("Ενέργεια:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Student_1")
            prompt = st.text_area("Περιγράψτε την αποστολή:", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Σύνθεση XML & Logic...'):
                try:
                    sys_prompt = (
                        "Είσαι ειδικός στο Micro:bit Maqueen. Χρησιμοποίησε XML για Blockly.\n"
                        "Υποστηριζόμενα blocks: 'maqueen_forward', 'maqueen_stop', 'logic_compare', 'math_number', 'procedures_defnoreturn'.\n"
                        "ΠΡΕΠΕΙ ΝΑ ΔΩΣΕΙΣ ΠΑΝΤΑ: 1. PYTHON: [Κώδικας] 2. BLOCKS: [XML]. Μη δώσεις ποτέ απλό κείμενο στα blocks."
                    )

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    )
                    ans = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    if "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        py_code = parts[0].replace("PYTHON:", "").strip()
                        xml_data = parts[1].replace("```xml", "").replace("```", "").strip()
                        
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(py_code, language='python')
                        
                        st.markdown("#### 🧩 Official Blockly Workspace")
                        # Δυναμικό Injection με όλες τις βιβλιοθήκες
                        blockly_html = f"""
                        <script src="https://unpkg.com/blockly/blockly.min.js"></script>
                        <script src="https://unpkg.com/blockly/blocks_compressed.js"></script>
                        <script src="https://unpkg.com/blockly/msg/el.js"></script>
                        <div id="blocklyDiv" style="height: 500px; width: 100%; border: 1px solid #ccc; border-radius:10px;"></div>
                        <script>
                            Blockly.Blocks['maqueen_forward'] = {{ init: function() {{
                                this.appendValueInput("speed").setCheck("Number").appendField("🚀 Κίνηση Εμπρός:");
                                this.setPreviousStatement(true, null); this.setNextStatement(true, null);
                                this.setColour(160);
                            }} }};
                            Blockly.Blocks['maqueen_stop'] = {{ init: function() {{
                                this.appendDummyInput().appendField("🛑 Σταμάτα");
                                this.setPreviousStatement(true, null); this.setNextStatement(true, null);
                                this.setColour(0);
                            }} }};

                            var workspace = Blockly.inject('blocklyDiv', {{
                                readOnly: true, scrollbars: true,
                                theme: Blockly.Themes.Classic,
                                zoom: {{controls: true, wheel: true}}
                            }});
                            try {{
                                var xml = Blockly.utils.xml.textToDom(`{xml_data}`);
                                Blockly.Xml.domToWorkspace(xml, workspace);
                            }} catch(e) {{ console.error(e); }}
                        </script>
                        """
                        components.html(blockly_html, height=520)
                    
                    # LOGGING (Fixed String Conversion)
                    log_entry = {{
                        "data": [{{
                            "Timestamp": str(datetime.datetime.now()),
                            "Student_ID": str(u_id),
                            "Action": str(action_type),
                            "Prompt": str(prompt),
                            "Answer": str(ans).replace('"', "'")
                        }}]
                    }}
                    requests.post(SHEETDB_URL, json=log_entry)
                    st.toast("✅ Καταγράφηκε!")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab_data:
    st.header("Βάση Δεδομένων", anchor=False)
    st.link_button("📊 Άνοιγμα Google Sheets", st.secrets.get("GSHEET_URL_LINK", "#"))
