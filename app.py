import streamlit as st
import google.generativeai as genai # Χρήση της πιο σταθερής βιβλιοθήκης
import datetime

# Ρύθμιση σελίδας
st.set_page_config(page_title="AI STEM Lab", page_icon="🤖")

# --- ΣΥΝΔΕΣΗ ΜΕ ΤΟ API ---
try:
    api_key_secret = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key_secret)
    # Χρησιμοποιούμε το 1.5 Flash που είναι το πιο σίγουρο για Free Tier
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ Πρόβλημα στις ρυθμίσεις: {e}")
    st.stop()

st.title("🤖 AI STEM Lab: Robotics Assistant")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI σκέφτεται...'):
            try:
                # Άμεση κλήση χωρίς περιττά περιτυλίγματα
                response = model.generate_content(user_prompt)
                
                if response.text:
                    st.subheader("🤖 Απάντηση:")
                    st.markdown(response.text)
                    
                    # Καταγραφή
                    try:
                        with open("research_logs.txt", "a", encoding="utf-8") as f:
                            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            f.write(f"{ts} | {student_id} | {user_prompt} | {response.text[:100]}...\n")
                        st.success("✅ Καταγράφηκε!")
                    except:
                        pass
                else:
                    st.error("⚠️ Το AI δεν έδωσε απάντηση.")
            except Exception as e:
                st.error(f"❌ Νέο Σφάλμα: {e}")
    else:
        st.warning("⚠️ Γράψε μια ερώτηση!")
