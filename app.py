import streamlit as st
from openai import OpenAI
import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Robotics Lab", page_icon="🤖", layout="wide")

# 2. Σύνδεση με το API της Groq και το Google Sheets
try:
    # API Key για Groq
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key_secret
    )
    
    # Σύνδεση με Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    gsheet_url = st.secrets["GSHEET_URL"]
    
except Exception as e:
    st.error(f"❌ Σφάλμα ρυθμίσεων: Βεβαιωθείτε ότι τα GROQ_API_KEY και GSHEET_URL υπάρχουν στα Secrets.")
    st.stop()

# 3. Sidebar - Διαχείριση Admin
st.sidebar.title("⚙️ Διαχείριση Admin")
if st.sidebar.checkbox("Εμφάνιση Επιλογών Κατεβάσματος"):
    try:
        # Διάβασμα των δεδομένων από το Google Sheet για τοπικό κατέβασμα αν χρειαστεί
        df_logs = conn.read(spreadsheet=gsheet_url)
        st.sidebar.download_button(
            label="📥 Κατέβασμα Logs από Google Sheets (CSV)",
            data=df_logs.to_csv(index=False).encode('utf-8'),
            file_name=f"robotics_logs_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.sidebar.warning(f"Δεν ήταν δυνατή η ανάγνωση των logs: {e}")

# 4. Κύριο Περιβάλλον Μαθητή
st.title("🤖 Maqueen Micro:bit AI Assistant")
st.info("Γράψε τι θέλεις να κάνει το ρομπότ Maqueen και πάρε τον κώδικα σε Python!")

student_id = st.text_input("ID Μαθητή:", "Guest")
user_prompt = st.text_area("Περίγραψε την αποστολή (π.
