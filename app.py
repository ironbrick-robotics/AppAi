import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Lab IDE", page_icon="🤖", layout="wide")

# Custom CSS για τα πλαίσια
st.markdown("""
    <style>
    .main-code { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    .alt-code { background-color: #e8f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #00a0dc; }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except Exception as e:
    st.error("❌ Ελέγξτε τα Secrets!")
    st.stop()

# --- ΛΕΙΤΟΥΡΓΙΑ ΚΑΘΑΡΙΣΜΟΥ (Session State) ---
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

def submit_action():
    st.session_state.submit_clicked = True

# --- ΤΙΤΛΟΣ ---
st.title("🤖 Maqueen Robotics IDE")
st.divider()

# 3. Layout Δύο Στηλών
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("📥 Είσοδος Μαθητή")
    
    # Χρήση Form για να λειτουργεί το Enter
    with st.form(key='my_form', clear_on_submit=True):
        student_id = st.text_input("ID Μαθητή:", value="Guest")
        # Το text_area παίρνει την τιμή από το state
        user_prompt = st.text_area("Περιγράψτε την αποστολή του Maqueen:", height=200, key="prompt_area")
        submit_button = st.form_submit_button(label="🚀 Δημιουργία Κώδικα & Καταγραφή")

with col_output:
    st.subheader("🖥️ Αποτέλεσμα AI")
    
    if submit_button:
        if user_prompt:
            with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
                try:
                    # Κλήση AI
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython. "
                                           "Αν υπάρχει εναλλακτικός τρόπος, χώρισε την απάντησή σου με τη λέξη '---ΕΝΑΛΛΑΚΤΙΚΟΣ---'."
                            },
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    
                    full_answer = response.choices[0].message.content
                    
                    # Διαχωρισμός και Εμφάνιση
                    parts = full_answer.split("---ΕΝΑΛΛΑΚΤΙΚΟΣ---")
                    main_code = parts[0]
                    alt_code = parts[1] if len(parts) > 1 else None

                    st.markdown('<p style="color:#ff4
