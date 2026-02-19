import streamlit as st
from openai import OpenAI
import datetime

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖", layout="wide")

# 2. Σύνδεση με το API της Groq (Συμβατό με OpenAI format)
try:
    # Λήψη API Key από τα Secrets του Streamlit Cloud
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key_secret
    )
except Exception as e:
    st.error("❌ Το API Key (GROQ_API_KEY) δεν βρέθηκε στα Secrets!")
    st.stop()

# 3. Sidebar - Διαχείριση για τον Καθηγητή
st.sidebar.title("⚙️ Διαχείριση Admin")
if st.sidebar.checkbox("Εμφάνιση Επιλογών Κατεβάσματος"):
    try:
        with open("research_logs.txt", "r", encoding="utf-8") as f:
            st.sidebar.download_button(
                label="📥 Κατέβασμα Logs (TXT)",
                data=f,
                file_name=f"robotics_logs_{datetime.date.today()}.txt",
                mime="text/plain"
            )
    except FileNotFoundError:
        st.sidebar.warning("Δεν υπάρχουν ακόμα καταγραφές.")

# 4. Κύριο Περιβάλλον Μαθητή
st.title("🤖 Maqueen Micro:bit AI Assistant")
st.info("Περίγραψε τι θέλεις να κάνει το ρομπότ Maqueen και πάρε τον κώδικα σε Python!")

student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Περίγραψε την αποστολή (π.χ. 'Αποφυγή εμποδίων με υπερήχους'):")

# 5. Εκτέλεση και Παραγωγή Κώδικα
if st.button("🚀 Δημιουργία Κώδικα & Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
            try:
                # Κλήση του Llama 3 με System Prompt για Maqueen
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Είσαι ένας έμπειρος καθηγητής ρομποτικής Maqueen. "
                                "Απαντάς πάντα στα Ελληνικά. "
                                "Δίνεις πάντα ολόκληρο τον κώδικα MicroPython για το Micro:bit. "
                                "Χρησιμοποίησε σωστές βιβλιοθήκες και pins για το Maqueen. "
                                "Εξήγησε αναλυτικά τι κάνει κάθε τμήμα του κώδικα."
                            )
                        },
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                answer = response.choices[0].message.content
                
                # Εμφάνιση Αποτελέσματος στην οθόνη
                st.subheader("📝 Ο Κώδικας Python:")
                st.markdown(answer)
                
                # 6. Απο
