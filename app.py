import streamlit as st
from google import genai
import datetime
import sys
import time

# ΑΝΑΓΚΑΣΤΙΚΟ UTF-8 ΓΙΑ ΤΑ ΕΛΛΗΝΙΚΑ
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- ΑΣΦΑΛΕΙΑ: ΛΗΨΗ API KEY ΑΠΟ ΤΑ SECRETS ---
try:
    # Εδώ το app τραβάει το κλειδί από το Streamlit Cloud Settings -> Secrets
    api_key_secret = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_secret)
except Exception as e:
    st.error("Το API Key δεν βρέθηκε στα Secrets. Παρακαλώ ρυθμίστε το GEMINI_API_KEY στα Settings του Streamlit.")
    st.stop()

st.title("🤖 AI STEM Lab: Robotics Assistant")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        max_retries = 3
        success = False
        answer = ""
        # Χρήση και των δύο μοντέλων για μεγαλύτερη αξιοπιστία
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]

        with st.spinner('Το AI σκέφτεται...'):
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
                        
                    except Exception as e:
                        if "429" in str(e):
                            attempt += 1
                            wait_time = attempt * 10
                            if attempt < max_retries:
                                time.sleep(wait_time)
                            else:
                                continue # Δοκίμασε το επόμενο μοντέλο
                        else:
                            st.error(f"Σφάλμα: {e}")
                            break

        if success:
            st.markdown("### Απάντηση:")
            st.write(answer)
            
            # Αποθήκευση
            try:
                with open("research_logs.txt", "a", encoding="utf-8") as f:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{ts} | {student_id} | {user_prompt} | {answer}\n")
                    f.write("-" * 40 + "\n")
                st.success("Καταγράφηκε!")
            except Exception as log_e:
                st.error(f"Σφάλμα logs: {log_e}")
        else:
            st.error("Υπέρβαση ορίου χρήσης. Δοκιμάστε πάλι σε λίγα λεπτά.")
            
    else:
        st.warning("Γράψε κάτι!")
