import streamlit as st
from google import genai
import datetime
import sys
import time

# ΑΝΑΓΚΑΣΤΙΚΟ UTF-8 ΓΙΑ ΤΑ ΕΛΛΗΝΙΚΑ
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ΑΣΦΑΛΗΣ ΡΥΘΜΙΣΗ API KEY ΜΕΣΩ STREAMLIT SECRETS
# Όταν το τρέχεις τοπικά, θα χρειαστείς αρχείο .streamlit/secrets.toml
# Όταν είναι online, το βάζεις στις ρυθμίσεις του Streamlit Cloud
try:
    api_key_secret = st.secrets["GEMINI_API_KEY"]
except:
    # Προσωρινό fallback για τοπικές δοκιμές αν δεν έχεις secrets
    api_key_secret = "AIzaSyChnIwc8TbMntyf7RkMS00Ir25wWApQBfc"

client = genai.Client(api_key=api_key_secret)

st.title("🤖 AI STEM Lab: Robotics Assistant")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        max_retries = 3
        attempt = 0
        success = False
        answer = ""
        # Λίστα μοντέλων: Πρώτα το 2.0, μετά το 1.5 ως εφεδρικό
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]

        with st.spinner('Το AI επεξεργάζεται το αίτημά σου...'):
            for model_name in models_to_try:
                if success: break
                
                attempt = 0
                while attempt < max_retries and not success:
                    try:
                        response = client.models.generate_content(
                            model=model_name, 
                            contents=user_prompt
                        )
                        answer = response.text
                        success = True
                        time.sleep(1) # Μικρή ασφάλεια
                        
                    except Exception as e:
                        if "429" in str(e):
                            attempt += 1
                            wait_time = attempt * 5 
                            if attempt < max_retries:
                                st.info(f"Αναμονή λόγω κίνησης ({model_name})...")
                                time.sleep(wait_time)
                            else:
                                st.warning(f"Το μοντέλο {model_name} εξάντλησε το όριο. Δοκιμή εφεδρικού...")
                        else:
                            st.error(f"Σφάλμα συστήματος: {e}")
                            break

        if success:
            st.markdown("### Απάντηση:")
            st.write(answer)
            
            # Αποθήκευση στο αρχείο logs
            try:
                with open("research_logs.
