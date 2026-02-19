import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Ph.D. Research Portal", page_icon="🎓", layout="wide")

# --- CSS ΓΙΑ SCRATCH / SPIKE PRIME BLOCKS ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp a.header-anchor { display: none; }
    
    /* Scratch Block Container */
    .scratch-block {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: bold;
        font-size: 14px;
        padding: 8px 15px;
        margin-bottom: 2px;
        width: fit-content;
        min-width: 180px;
        position: relative;
        color: white;
        box-shadow: 0 2px 0 rgba(0,0,0,0.2);
    }

    /* Το "δόντι" (Notch) στην κορυφή του block */
    .scratch-block::before {
        content: "";
        position: absolute;
        top: -8px;
        left: 20px;
        width: 16px;
        height: 8px;
        background: inherit;
        clip-path: polygon(0% 100%, 20% 0%, 80% 0%, 100% 100%);
    }

    /* Χρώματα ανά κατηγορία (Scratch/Spike Style) */
    .event { background-color: #FFBF00; border-radius: 20px 20px 4px 4px; border: 1px solid #E6AC00; color: black; } /* Events/Hat */
    .control { background-color: #FFAB19; border-radius: 4px; border: 1px solid #CF8B17; } /* Control */
    .motion { background-color: #4C97FF; border-radius: 4px; border: 1px solid #3373CC; } /* Motion */
    .sensor { background-color: #5CB1D6; border-radius: 4px; border: 1px solid #478BA8; } /* Sensing */
    
    /* Εσοχή για τα Loops (C-shape) */
    .indent { margin-left: 20px; border-left: 10px solid #FFAB19; padding-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["GROQ_API_KEY"])
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except:
    st.error("Σφάλμα σύνδεσης. Ελέγξτε τα Secrets.")

# 3. Tabs
tab_info, tab_app = st.tabs(["📖 Ταυτότητα Έρευνας", "🚀 Research App"])

with tab_app:
    st.header("🔬 Dual-Modal Research Interface", anchor=False)
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        with st.form(key='research_form', clear_on_submit=True):
            u_id = st.text_input("Researcher ID:", value="Expert_User")
            prompt = st.text_area("Περιγραφή Αποστολής Maqueen:", height=150)
            btn = st.form_submit_button("🚀 Generate Logic")

    with col_out:
        if btn and prompt:
            with st.spinner('⏳ Converting to Blocks...'):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": """Είσαι ειδικός καθηγητής Maqueen. 
                            Πρέπει να παράγεις ΠΑΝΤΑ δύο ενότητες:
                            1. PYTHON: [Κώδικας Python]
                            2. BLOCKS: [Λίστα από εντολές σε μορφή HTML Blocks]
                            
                            Για τα BLOCKS χρησιμοποίησε ΑΥΣΤΗΡΑ αυτή τη δομή:
                            <div class='scratch-block event'>🏁 Όταν ξεκινήσει</div>
                            <div class='scratch-block motion'>🚀 Κινήσου Εμπρός</div>
                            <div class='indent'>
                                <div class='scratch-block motion'>🔄 Στρίψε Δεξιά</div>
                            </div>
                            Απάντα στα Ελληνικά."""},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ans = response.choices[0].message.content
                    
                    if "BLOCKS:" in ans:
                        code_part = ans.split("BLOCKS:")[0].replace("PYTHON:", "")
                        block_part = ans.split("BLOCKS:")[1]
                        
                        st.subheader("🖥️ Python Code")
                        st.code(code_part, language='python')
                        
                        st.subheader("🧩 Scratch-Style Blocks")
                        st.markdown(block_part, unsafe_allow_html=True)
                    
                    # Logging
                    requests.post(SHEETDB_URL, json={"data": [{"Timestamp": str(datetime.datetime.now()), "Student_ID": u_id, "Prompt": prompt, "Answer": ans}]})
                except Exception as e:
                    st.error(f"Error: {e}")

st.divider()
st.caption("Ph.D. Research Tool v6.0 | Scratch-UI Simulation")
