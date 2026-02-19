import streamlit as st
from openai import OpenAI
import datetime

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖", layout="wide")

# 2. Σύνδεση με το API της Groq
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key_secret
    )
except Exception as e:
    st.error("❌ Το API Key (GROQ_API_KEY) δεν βρέθηκε στα Secrets!")
    st.stop()

# 3. Sidebar - Διαχείριση Admin
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

# 4. Περιβάλλον Μαθητή
st.title("🤖 Maqueen Micro:bit AI Assistant")
st.info("Περίγραψε τι θέλεις να κάνει το ρομπότ Maqueen και πάρε τον κώδικα σε Python!")

student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Περίγραψε την αποστολή (π.χ. 'Αποφυγή εμποδίων'):")

# 5. Εκτέλεση
if st.button("🚀 Δημιουργία Κώδικα & Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Είσαι ειδικός καθηγητής Maqueen. Απαντάς στα Ελληνικά και δίνεις πάντα ολόκληρο τον κώδικα MicroPython."
                        },
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                answer = response.choices[0].message.content
                st.subheader("📝 Ο Κώδικας σου:")
                st.markdown(answer)
                
                # 6. Αποθήκευση ΟΛΟΚΛΗΡΗΣ της απάντησης (Διορθωμένο Syntax)
                try:
                    with open("research_logs.txt", "a", encoding="utf-8") as f:
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"TS: {ts} | ID: {student_id}\n")
                        f.write(f"PROMPT: {user_prompt}\n")
