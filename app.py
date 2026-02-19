import streamlit as st
from google import genai
import datetime
import sys

# Ρύθμιση σελίδας
st.set_page_config(page_title="AI STEM Lab", page_icon="🤖")

# --- ΣΥΝΔΕΣΗ ΜΕ ΤΟ API ---
try:
    # Λήψη από τα Secrets του Streamlit Cloud
    api_key_secret = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_secret)
except Exception as e:
    st.error(f"❌ Πρόβλημα με το API Key στα Secrets: {e}")
    st.stop()

st.title("🤖 AI STEM Lab: Robotics Assistant")

# Ενημερωτικό μήνυμα
st.info("Το AI μπορεί να απαντήσει στις ερωτήσεις σου για τη Ρομποτική και τον Προγραμματισμό.")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        # Spinner για να ξέρει ο μαθητής ότι το σύστημα δουλεύει
        with st.spinner('⏳ Το AI σκέφτεται... παρακαλώ περιμένετε'):
            try:
                # Χρήση του 1.5 Flash που είναι το πιο αξιόπιστο για Free Tier
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=user_prompt
                )
                
                if response and hasattr(response, 'text'):
                    answer = response.text
                    st.subheader("🤖 Απάντηση:")
                    st.markdown(answer)
                    
                    # Προσπάθεια καταγραφής
                    try:
                        with open("research_logs.txt", "a", encoding="utf-8") as f:
                            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            f.write(f"{ts} | {student_id} | {user_prompt} | {answer}\n")
                            f.write("-" * 40 + "\n")
                        st.success("✅ Η δραστηριότητα καταγράφηκε!")
                    except:
                        st.warning("⚠️ Η απάντηση δόθηκε, αλλά η εγγραφή στο αρχείο απέτυχε (αναμενόμενο σε ορισμένα Cloud περιβάλλοντα).")
                else:
                    st.error("⚠️ Το AI δεν επέστρεψε κείμενο. Παρακαλώ δοκίμασε ξανά.")

            except Exception as e:
                # Εμφάνιση του σφάλματος με σωστή σύνταξη
                st.error(f"❌ Σφάλμα κατά την κλήση του AI: {str(e)}")
    else:
        st.warning("⚠️ Παρακαλώ γράψε μια ερώτηση πρώτα!")

st.divider()
st.caption("AI STEM Lab v2.3")
