import streamlit as st
from google import genai
import datetime
import sys
import time

# ΑΝΑΓΚΑΣΤΙΚΟ UTF-8 ΓΙΑ ΤΑ ΕΛΛΗΝΙΚΑ
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- ΡΥΘΜΙΣΗ ΑΣΦΑΛΕΙΑΣ API KEY ---
try:
    # Τραβάει το κλειδί από το Streamlit Cloud Dashboard -> Settings -> Secrets
    api_key_secret = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_secret)
except Exception as e:
    st.error("❌ Το API Key δεν βρέθηκε! Πήγαινε στα Settings του Streamlit Cloud και πρόσθεσε το GEMINI_API_KEY στα Secrets.")
    st.stop()

st.set_page_config(page_title="AI STEM Lab", page_icon="🤖")
st.title("🤖 AI STEM Lab: Robotics Assistant")
st.info("Το AI μπορεί να απαντήσει στις ερωτήσεις σου για τη Ρομποτική και τον Προγραμματισμό.")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        max_retries = 2
        success = False
        answer = ""
        
        # Λίστα μοντέλων προς δοκιμή
        # Δοκιμάζουμε πρώτα το 2.0 και μετά το 1.5 αν υπάρξει πρόβλημα
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]

        with st.spinner('⏳ Το AI επεξεργάζεται την ερώτησή σου...'):
            for model_name in models_to_try:
                if success:
                    break
                
                attempt = 0
                while attempt < max_retries and not success:
                    try:
                        # Κλήση της νέας βιβλιοθήκης google-genai
                        response = client.models.generate_content(
                            model=model_name, 
                            contents=user_prompt
                        )
                        answer = response.text
                        success = True
                        
                    except Exception as e:
                        error_msg = str(e)
                        # Διαχείριση ορίου (429)
                        if "429" in error_msg:
                            attempt += 1
                            if attempt < max_retries:
                                time.sleep(5) # Αναμονή 5 δευτερόλεπτα
                            else:
                                # Αν εξαντληθούν οι προσπάθειες στο 2.0, πάμε στο επόμενο μοντέλο
                                continue 
                        # Διαχείριση λάθος μοντέλου ή έκδοσης (404)
                        elif "404" in error_msg:
                            break # Πή
