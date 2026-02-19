import streamlit as st
from openai import OpenAI
import datetime
import requests 

st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖", layout="wide")

# Σύνδεση με Groq
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except Exception as e:
    st.error("❌ Ελέγξτε τα Secrets (GROQ_API_KEY και GSHEET_URL). ❌")
    st.stop()

st.title("AI Assistant: Maqueen Micro:bit ")
student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Τι θέλεις να κάνει το ρομπότ;")

if st.button("🚀 Δημιουργία Κώδικα & Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Επεξεργασία...'):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython."},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                answer = response.choices[0].message.content
                st.subheader("Ο Κώδικας σου:")
                st.markdown(answer)
                
                # --- ΑΠΟΘΗΚΕΥΣΗ ΜΕΣΩ SHEETDB (CRUD ENABLED) ---
                data_to_send = {
                    "data": [{
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Student_ID": student_id,
                        "Prompt": user_prompt,
                        "Answer": answer
                    }]
                }
                
                post_req = requests.post(SHEETDB_URL, json=data_to_send)
                
                if post_req.status_code == 201:
                    st.success("✅ Η δραστηριότητα αποθηκεύτηκε.")
                else:
                    st.warning(f"⚠️ Σφάλμα αποθήκευσης: {post_req.text}")

            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")

