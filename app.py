import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας
st.set_page_config(page_title="Maqueen Lab IDE", page_icon="🤖", layout="wide")

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key_secret
    )
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except Exception as e:
    st.error("❌ Ελέγξτε τα Secrets (GROQ_API_KEY και GSHEET_URL)!")
    st.stop()

# --- ΤΙΤΛΟΣ ---
st.title("🤖 Maqueen Robotics IDE")
st.divider()

# 3. Layout Δύο Στηλών
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("📥 Είσοδος Μαθητή")
    
    # Χρήση Form για Enter support και αυτόματο καθάρισμα (clear_on_submit)
    with st.form(key='maqueen_form', clear_on_submit=True):
        student_id = st.text_input("ID Μαθητή:", value="Guest")
        user_prompt = st.text_area("Περιγράψτε την αποστολή του Maqueen:", height=200)
        submit_button = st.form_submit_button(label="🚀 Δημιουργία Κώδικα & Καταγραφή")

with col_output:
    st.subheader("🖥️ Αποτέλεσμα AI")
    
    if submit_button:
        if user_prompt:
            with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
                try:
                    # Κλήση AI
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython. "
                                           "Αν υπάρχει εναλλακτικός τρόπος, χώρισε την απάντησή σου με τη λέξη '---ΕΝΑΛΛΑΚΤΙΚΟΣ---'."
                            },
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    
                    full_answer = response.choices[0].message.content
                    
                    # Διαχωρισμός Κύριας και Εναλλακτικής Λύσης
                    if "---ΕΝΑΛΛΑΚΤΙΚΟΣ---" in full_answer:
                        parts = full_answer.split("---ΕΝΑΛΛΑΚΤΙΚΟΣ---")
                        main_code = parts[0]
                        alt_code = parts[1]
                    else:
                        main_code = full_answer
                        alt_code = None

                    # Εμφάνιση Κύριας Λύσης (Κόκκινο/Γκρι πλαίσιο)
                    st.markdown("### 🔴 Προτεινόμενη Λύση")
                    st.info(main_code)
                    
                    # Εμφάνιση Εναλλακτικής Λύσης (Μπλε πλαίσιο)
                    if alt_code and alt_code.strip():
                        st.markdown("### 🔵 Εναλλακτική Προσέγγιση")
                        st.success(alt_code)

                    # ΑΠΟΘΗΚΕΥΣΗ ΜΕΣΩ SHEETDB
                    data_to_send = {
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Student_ID": str(student_id),
                        "Prompt": str(user_prompt),
                        "Answer": str(full_answer)
                    }
                    
                    post_req = requests.post(SHEETDB_URL, json={"data": [data_to_send]})
                    
                    if post_req.status_code == 201:
                        st.toast("✅ Η ερώτηση καταγράφηκε επιτυχώς!")
                    else:
                        st.error(f"⚠️ Πρόβλημα καταγραφής: {post_req.text}")
                    
                except Exception as e:
                    st.error(f"❌ Σφάλμα API: {e}")
        else:
            st.warning("⚠️ Παρακαλώ γράψε μια αποστολή για το ρομπότ.")
    else:
        st.write("Περιμένω την ερώτησή σου...")

st.divider()
st.caption("AI STEM Lab v4.2 | Maqueen side-by-side Edition")
