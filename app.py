import streamlit as st
from google import genai
import datetime
import sys

# Ρύθμιση σελίδας
st.set_page_config(page_title="AI STEM Lab", page_icon="🤖")

# ΑΝΑΓΚΑΣΤΙΚΟ UTF-8 ΓΙΑ ΤΑ ΕΛΛΗΝΙΚΑ
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- ΣΥΝΔΕΣΗ ΜΕ ΤΟ API ---
try:
    # Λήψη από τα Secrets του Streamlit Cloud
    api_key_secret = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_secret)
except Exception as e:
    st.error("❌ Το API Key δεν βρέθηκε στα Secrets!")
    st.info("Πήγαινε στο Streamlit Cloud: Settings -> Secrets και πρόσθεσε: GEMINI_API_KEY = 'το-κλειδί-σου'")
    st.stop()

st.title("🤖 AI STEM Lab: Robotics Assistant")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        answer = ""
        success = False
        
        # Χρησιμοποιούμε ένα Spinner που ενημερώνει τον χρήστη
        with st.spinner('⏳ Το AI επεξεργάζεται την ερώτηση... παρακαλώ περιμένετε.'):
            try:
                # Δοκιμάζουμε το gemini-1.5-flash για μέγιστη συμβατότητα
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=user_prompt
                )
                
                if response and response.text:
                    answer = response.text
                    success = True
                else:
                    st.error("⚠️ Το AI δεν επέστρεψε κείμενο. Δοκίμασε ξανά.")

            except Exception as e:
                # Εμφάνιση του ακριβούς σφάλματος για να ξέρουμε τι φταίει
                st.error
