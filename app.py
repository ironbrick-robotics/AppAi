import streamlit as st
from openai import OpenAI # Θα χρησιμοποιήσουμε το format της OpenAI
import datetime

# Ρύθμιση σελίδας
st.set_page_config(page_title="AI STEM Lab", page_icon="🤖")

# --- ΣΥΝΔΕΣΗ ΜΕ GROQ (ΔΩΡΕΑΝ & ΣΥΜΒΑΤΟ ΜΕ OPENAI) ---
try:
    api_key = st.secrets["GROQ_API_KEY"]
    # Σύνδεση με τον server της Groq
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )
except Exception as e:
    st.error("❌ Λείπει το GROQ_API_KEY από τα Secrets!")
    st.stop()

st.title("🤖 AI STEM Lab: Robotics Assistant")

student_id = st.text_input("ID Συμμετέχοντος:", "Guest")
user_prompt = st.text_area("Γράψε το ερώτημά σου για το ρομπότ:")

if st.button("Εκτέλεση και Καταγραφή"):
    if user_prompt:
        with st.spinner('⏳ Το AI (Llama 3) σκέφτεται...'):
            try:
                # Κλήση μοντέλου Llama 3 (ταχύτατο και δωρεάν)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                answer = response.choices[0].message.content
                
                st.subheader("🤖 Απάντηση:")
                st.markdown(answer)
                
                # Καταγραφή
                with open("research_logs.txt", "a", encoding="utf-8") as f:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{ts} | {student_id} | {user_prompt} | {answer[:50]}...\n")
                st.success("✅ Καταγράφηκε!")
                
            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")
    else:
        st.warning("⚠️ Γράψε κάτι!")
