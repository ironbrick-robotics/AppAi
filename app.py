import streamlit as st
from openai import OpenAI
import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖", layout="wide")

# 2. Σύνδεση με το API της Groq και το Google Sheets
try:
    # API Key για Groq από τα Secrets
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key_secret
    )
    
    # Σύνδεση με Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    gsheet_url = st.secrets["GSHEET_URL"]
    
except Exception as e:
    st.error(f"❌ Σφάλμα ρυθμίσεων: Ελέγξτε τα Secrets για GROQ_API_KEY και GSHEET_URL.")
    st.stop()

# 3. Sidebar - Διαχείριση Admin
st.sidebar.title("⚙️ Διαχείριση Admin")
if st.sidebar.checkbox("Εμφάνιση Επιλογών Κατεβάσματος"):
    try:
        # Ανάγνωση δεδομένων απευθείας από το Google Sheet
        df_logs = conn.read(spreadsheet=gsheet_url)
        st.sidebar.download_button(
            label="📥 Κατέβασμα Logs (CSV)",
            data=df_logs.to_csv(index=False).encode('utf-8'),
            file_name=f"robotics_logs_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.sidebar.warning("Δεν υπάρχουν ακόμα δεδομένα στο Sheet.")

# 4. Κύριο Περιβάλλον Μαθητή
st.title("🤖 Maqueen Micro:bit AI Assistant")
st.info("Περίγραψε την αποστολή του Maqueen και λάβε τον κώδικα σε Python!")

student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Τι θέλεις να κάνει το ρομπότ;")

# 5. Εκτέλεση και Παραγωγή Κώδικα
if st.button("🚀 Δημιουργία Κώδικα & Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI επεξεργάζεται την ερώτηση...'):
            try:
                # Κλήση του AI με οδηγίες για Maqueen
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Είσαι ειδικός καθηγητής Maqueen. Απαντάς στα Ελληνικά και δίνεις πάντα ολόκληρο τον κώδικα MicroPython για Micro:bit."
                        },
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                answer = response.choices[0].message.content
                st.subheader("📝 Ο Κώδικας σου:")
                st.markdown(answer)
                
                # 6. Αποθήκευση στο Google Sheet (Χωρίς περικοπή κειμένου)
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Student_ID": student_id,
                    "Prompt": user_prompt,
                    "Answer": answer
                }])
                
                try:
                    # Διάβασμα παλαιών και συγχώνευση με τα νέα
                    existing_data = conn.read(spreadsheet=gsheet_url)
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    conn.update(spreadsheet=gsheet_url, data=updated_df)
                    st.success("✅ Η δραστηριότητα αποθηκεύτηκε μόνιμα στο Google Sheet!")
                except Exception as sheet_err:
                    st.warning(f"⚠️ Η απάντηση δόθηκε, αλλά η αποθήκευση στο Sheet απέτυχε: {sheet_err}")

            except Exception as e:
                st.error(f"❌ Σφάλμα API: {e}")
    else:
        st.warning("⚠️ Παρακαλώ γράψε μια ερώτηση.")

st.divider()
st.caption("AI STEM Lab v3.0 | Cloud Logging Enabled")
