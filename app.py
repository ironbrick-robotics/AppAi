import streamlit as st
from openai import OpenAI
import datetime

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖", layout="wide")

# 2. Σύνδεση με το API της Groq
try:
    # Τραβάει το κλειδί από το Settings -> Secrets του Streamlit Cloud
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
st.sidebar.info("Εδώ μπορείτε να κατεβάσετε τις δραστηριότητες των μαθητών.")

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
        st.sidebar.warning("Δεν υπάρχουν ακόμα καταγραφές στο αρχείο.")

# 4. Κύριο Περιβάλλον Μαθητή
st.title("🤖 Maqueen Micro:bit AI Assistant")
st.markdown("Γράψε τι θέλεις να κάνει το ρομπότ σου και το AI θα σου δώσει τον κώδικα σε Python!")

# Πεδία Εισαγωγής
col1, col2 = st.columns([1, 3])
with col1:
    student_id = st.text_input("ID Μαθητή:", "Guest")
with col2:
    user_prompt = st.text_area("Περίγραψε την αποστολή του ρομπότ (π.χ. 'Ακολούθησε τη μαύρη γραμμή'):")

# 5. Εκτέλεση και Παραγωγή Κώδικα
if st.button("🚀 Δημιουργία Κώδικα & Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI δημιουργεί τον κώδικα για το Maqueen...'):
            try:
                # Κλήση του μοντέλου με ειδικές οδηγίες για το Maqueen
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Είσαι ένας έμπειρος καθηγητής ρομποτικής. "
                                "Απαντάς πάντα στα Ελληνικά. "
                                "Δίνεις πάντα κώδικα MicroPython ειδικά για το ρομπότ Maqueen και το Micro:bit. "
                                "Χρησιμοποίησε τις τυπικές εντολές για το Maqueen (π.χ. pin8, pin12 για υπερήχους, κτλ). "
                                "Εξήγησε με απλά λόγια τι κάνει κάθε τμήμα του κώδικα."
                            )
                        },
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                answer = response.choices[0].message.content
                
                # Εμφάνιση Αποτελέσματος
                st.subheader("📝 Ο Κώδικας Python:")
                st.markdown(answer)
                
                # 6. Αποθήκευση στα Logs
                with open("research_logs.txt", "a", encoding="utf-8") as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"TIMESTAMP: {timestamp}\n")
                    f.write(f"STUDENT ID: {student_id}\n")
                    f.write(f"QUESTION: {user_prompt}\n")
                    f.write(f"ANSWER: {answer}\n")
