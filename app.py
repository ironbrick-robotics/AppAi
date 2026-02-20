import streamlit as st
from openai import OpenAI
import datetime
import requests
import streamlit.components.v1 as components

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal v7.6", page_icon="🎓", layout="wide")

# 2. Σύνδεση με Groq & SheetDB
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.warning("⚠️ Σφάλμα σύνδεσης. Ελέγξτε τα Secrets.")

# 3. Tabs
tab_info, tab_app, tab_data = st.tabs(["📖 Ταυτότητα", "🚀 App (Full IDE)", "📂 Αρχεία"])

with tab_app:
    st.header("🔬 Full-Scale Robotics Research IDE", anchor=False)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    col_set1, col_set2 = st.columns(2)
    with col_set1:
        lang_choice = st.selectbox("Γλώσσα:", ["MicroPython & Blocks", "Arduino C"])
    with col_set2:
        action_type = st.radio("Τύπος Ενέργειας:", ["Νέα Αποστολή", "Διόρθωση"], horizontal=True)

    col_in, col_out = st.columns([1, 1], gap="large")
    
    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("User ID:", value="Researcher_1")
            prompt = st.text_area("Περιγράψτε την αποστολή (π.χ. 'χρησιμοποίησε μια μεταβλητή για την απόσταση'):", height=150)
            submit = st.form_submit_button("🚀 Εκτέλεση")

    with col_out:
        if submit and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner('⏳ Σύνθεση XML & Logic...'):
                try:
                    # Πλήρες System Prompt για να καλύπτει όλες τις κατηγορίες
                    sys_prompt = (
                        "Είσαι ειδικός στο Micro:bit Maqueen. Χρησιμοποίησε XML για Blockly.\n"
                        "Υποστηριζόμενα blocks:\n"
                        "- Logic: 'controls_if', 'logic_compare', 'logic_operation', 'logic_boolean'\n"
                        "- Loops: 'controls_repeat_ext', 'controls_whileUntil', 'controls_for'\n"
                        "- Math: 'math_number', 'math_arithmetic', 'math_single'\n"
                        "- Variables: 'variables_get', 'variables_set'\n"
                        "- Maqueen: 'maqueen_forward', 'maqueen_backward', 'maqueen_stop', 'maqueen_ultrasonic'\n"
                        "Δώσε: 1. PYTHON: [Κώδικας] 2. BLOCKS: [XML]."
                    )

                    messages_to_send = [{"role": "system", "content": sys_prompt}] + st.session_state.messages
                    response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_to_send)
                    ans = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": ans})

                    if "BLOCKS:" in ans:
                        parts = ans.split("BLOCKS:")
                        py_code = parts[0].replace("PYTHON:", "").strip()
                        xml_code = parts[1].replace("```xml", "").replace("```", "").strip()
                        
                        st.markdown("#### 🐍 MicroPython Code")
                        st.code(py_code, language='python')
                        
                        # --- FULL BLOCKLY INJECTION (Standard + Custom) ---
                        st.markdown("#### 🧩 Official Blockly Workspace")
                        blockly_html = f"""
                        <script src="https://unpkg.com/blockly/blockly.min.js"></script>
                        <script src="https://unpkg.com/blockly/blocks_compressed.js"></script>
                        <script src="https://unpkg.com/blockly/javascript_compressed.js"></script>
                        <script src="https://unpkg.com/blockly/msg/el.js"></script>
                        
                        <div id="blocklyDiv" style="height: 500px; width: 100%; border: 1px solid #ccc; border-radius:10px;"></div>
                        
                        <script>
                            // Ορισμός Maqueen Blocks (Custom)
                            Blockly.Blocks['maqueen_forward'] = {{
                              init: function() {{
                                this.appendValueInput("speed").setCheck("Number").appendField("🚀 Maqueen Εμπρός Ταχύτητα:");
                                this.setPreviousStatement(true, null); this.setNextStatement(true, null);
                                this.setColour(160);
                              }}
                            }};
                            Blockly.Blocks['maqueen_ultrasonic'] = {{
                              init: function() {{
                                this.appendDummyInput().appendField("📏 Υπέρηχος (cm)");
                                this.setOutput(true, "Number");
                                this.setColour(230);
                              }}
                            }};
                            Blockly.Blocks['maqueen_stop'] = {{
                              init: function() {{
                                this.appendDummyInput().appendField("🛑 Σταμάτα");
                                this.setPreviousStatement(true, null); this.setNextStatement(true, null);
                                this.setColour(0);
                              }}
                            }};

                            // Αρχικοποίηση Workspace με υποστήριξη όλων των blocks
                            var workspace = Blockly.inject('blocklyDiv', {{
                                readOnly: true,
                                scrollbars: true,
                                theme: Blockly.Themes.Classic,
                                zoom: {{controls: true, wheel: true}}
                            }});
                            
                            try {{
                                var xml = Blockly.utils.xml.textToDom(`{xml_code}`);
                                Blockly.Xml.domToWorkspace(xml, workspace);
                            }} catch (e) {{ console.error(e); }}
                        </script>
                        """
                        components.html(blockly_html, height=520)
                    
                    # LOGGING
                    log_entry = {{"data": [{{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Action": action_type, "Prompt": prompt, "Answer": ans}}]}}
                    requests.post(SHEETDB_URL, json=log_entry)
                except Exception as e:
                    st.error(f"Error: {e}")
