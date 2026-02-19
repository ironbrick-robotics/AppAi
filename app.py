import streamlit as st
from openai import OpenAI
import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Σύνδεση με Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
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
    st.error("❌ Το API Key (GROQ_API_KEY) δεν βρέθηκε στα Secrets του Streamlit Cloud!")
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
st.info("Γράψε τι θέλεις να κάνει το ρομπότ Maqueen και θα λάβεις τον κώδικα σε Python!")

student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Περίγραψε την αποστολή (π.χ. 'Αποφυγή εμποδίων με υπερήχους'):")

# 5. Εκτέλεση και Παραγωγή Κώδικα
if st.button("🚀 Δημιουργία Κώδικα & Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Είσαι ειδικός καθηγητής ρομποτικής Maqueen. "
                                "Απαντάς στα Ελληνικά. Δίνεις πάντα κώδικα MicroPython για Micro:bit. "
                                "Εξήγησε σύντομα τι κάνει ο κώδικας."
                            )
                        },
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                answer = response.choices[0].message.content
                st.subheader("📝 Ο Κώδικας σου:")
                st.markdown(answer)
                
                # 6. Αποθήκευση στο Google Sheet
new_data = pd.DataFrame([{
    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "Student_ID": student_id,
    "Prompt": user_prompt,
    "Answer": answer
}])

# Διάβασμα υπαρχόντων και προσθήκη νέας γραμμής
try:
    existing_data = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
    conn.update(spreadsheet=st.secrets["GSHEET_URL"], data=updated_df)
    st.success("✅ Η δραστηριότητα αποθηκεύτηκε στο Google Sheet!")
except Exception as e:
    st.error(f"Σφάλμα σύνδεσης με Google Sheets: {e}")
            except Exception as e:
                st.error(f"❌ Σφάλμα API: {e}")
    else:
        st.warning("⚠️ Παρακαλώ γράψε μια ερώτηση.")

st.divider()
st.caption("AI STEM Lab v2.6 | Maqueen Python Edition")

