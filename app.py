import streamlit as st
from google import genai
import datetime
import sys
import time # Απαραίτητο για την αναμονή

# ΑΝΑΓΚΑΣΤΙΚΟ UTF-8 ΓΙΑ ΤΑ ΕΛΛΗΝΙΚΑ
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ΡΥΘΜΙΣΗ ΜΕ ΤΗ ΝΕΑ ΒΙΒΛΙΟΘΗΚΗ
client = genai.Client(api_key="AIzaSyChnIwc8TbMntyf7RkMS00Ir25wWApQBfc")

st.title("🤖 AI STEM Lab: Robotics Assistant")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        # --- ΜΗΧΑΝΙΣΜΟΣ RETRY ---
        max_retries = 3
        attempt = 0
        success = False
        answer = ""

        with st.spinner('Το AI σκέφτεται...'):
            while attempt < max_retries and not success:
                try:
                    # Κλήση του μοντέλου
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=user_prompt
                    )
                    answer = response.text
                    success = True
                    # Μικρή παύση για να μην "χτυπάμε" το όριο των 15 RPM συνέχεια
                    time.sleep(2) 
                    
                except Exception as e:
                    if "429" in str(e):
                        attempt += 1
                        wait_time = attempt * 10 # 10s την 1η φορά, 20s τη 2η...
                        st.warning(f"Το σύστημα είναι απασχολημένο (Quota 429). Προσπάθεια {attempt}/{max_retries}. Αναμονή {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        st.error(f"Σφάλμα: {e}")
                        break # Σταματάμε αν είναι άλλο είδος σφάλματος

        if success:
            st.markdown("### Απάντηση:")
            st.write(answer)
            
            # Αποθήκευση
            try:
                with open("research_logs.txt", "a", encoding="utf-8") as f:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{ts} | {student_id} | {user_prompt} | {answer}\n")
                    f.write("-" * 40 + "\n")
                st.success("Καταγράφηκε επιτυχώς!")
            except Exception as log_e:
                st.error(f"Σφάλμα κατά την αποθήκευση: {log_e}")
        elif attempt == max_retries:
            st.error("Εξαντλήθηκαν οι προσπάθειες. Το ημερήσιο όριο (Quota) μάλλον τελείωσε.")
            
    else:
        st.warning("Γράψε κάτι!")

        #py -3.12 -m streamlit run "C:\Users\argyk\source\repos\app.py"