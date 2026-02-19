import streamlit as st
from openai import OpenAI
import datetime

st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖")

try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
except Exception as e:
    st.error("❌ Λείπει το API Key!")
    st.stop()

st.title("🤖 Maqueen Micro:bit Assistant")

student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Τι θέλεις να κάνει το Maqueen;")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Είσαι ειδικός στο Maqueen Micro:bit. Απάντα στα Ελληνικά και δίνε πάντα κώδικα MicroPython για το Maqueen."},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                answer = response.choices[0].message.content
                st.subheader("🤖 Ο κώδικας σου:")
                st.markdown(answer)
                
                # Αποθήκευση
                with open("research_logs.txt", "a", encoding="utf-8") as f:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"TS: {ts} | ID: {student_id}\nPROMPT: {user_prompt}\nANSWER: {answer[:100]}...\n{'-'*20}\n")
                st.success("✅ Καταγράφηκε!")
            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")
    else:
        st.warning("⚠️ Γράψε μια ερώτηση!")

# Sidebar για κατέβασμα των Logs
st.sidebar.title("Διαχείριση")
if st.sidebar.checkbox("Εμφάνιση Επιλογών Admin"):
    try:
        with open("research_logs.txt", "r", encoding="utf-8") as f:
            st.sidebar.download_button("📥 Κατέβασμα Logs (TXT)", f, "research_logs.txt")
    except:
        st.sidebar.write("Δεν υπάρχουν ακόμα καταγραφές.")
