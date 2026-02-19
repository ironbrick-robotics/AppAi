import streamlit as st
from openai import OpenAI
import datetime
import requests

# 1. Ρύθμιση Σελίδας (Wide Mode για να χωράνε οι στήλες)
st.set_page_config(page_title="Maqueen Lab IDE", page_icon="🤖", layout="wide")

# Custom CSS για τα χρώματα των πλαισίων
st.markdown("""
    <style>
    .main-code {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .alt-code {
        background-color: #e8f4f8;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00a0dc;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Σύνδεση με Groq & SheetDB
try:
    api_key_secret = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_secret)
    SHEETDB_URL = st.secrets["GSHEET_URL"]
except Exception as e:
    st.error("❌ Ελέγξτε τα Secrets!")
    st.stop()

st.title("🤖 Maqueen Robotics IDE")
st.divider()

# 3. Δημιουργία δύο στηλών (Αριστερή για Εισαγωγή - Δεξιά για Αποτελέσματα)
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("📥 Είσοδος Μαθητή")
    student_id = st.text_input("ID Μαθητή:", "Guest")
    user_prompt = st.text_area("Περιγράψτε την αποστολή του Maqueen:", height=200)
    run_button = st.button("🚀 Δημιουργία Κώδικα & Καταγραφή")

with col_output:
    st.subheader("🖥️ Αποτέλεσμα AI")
    if run_button:
        if user_prompt:
            with st.spinner('⏳ Το AI δημιουργεί τον κώδικα...'):
                try:
                    # Κλήση AI με εντολή για δομημένη απάντηση
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": "Είσαι ειδικός καθηγητής Maqueen. Απάντα στα Ελληνικά με κώδικα MicroPython. "
                                           "Αν υπάρχει εναλλακτικός τρόπος (π.χ. χωρίς βιβλιοθήκη ή με άλλο αισθητήρα), "
                                           "χώρισε την απάντησή σου με τη λέξη '---ΕΝΑΛΛΑΚΤΙΚΟΣ---'."
                            },
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    
                    full_answer = response.choices[0].message.content
                    
                    # Διαχωρισμός κύριου και εναλλακτικού κώδικα
                    parts = full_answer.split("---ΕΝΑΛΛΑΚΤΙΚΟΣ---")
                    main_code = parts[0]
                    alt_code = parts[1] if len(parts) > 1 else None

                    # Εμφάνιση Κύριου Κώδικα σε πλαίσιο
                    st.markdown('<p style="color:#ff4b4b; font-weight:bold;">Προτεινόμενη Λύση:</p>', unsafe_allow_html=True)
                    st.info(main_code)
                    
                    # Εμφάνιση Εναλλακτικού Κώδικα αν υπάρχει
                    if alt_code:
                        st.markdown('<p style="color:#00a0dc; font-weight:bold;">Εναλλακτική Προσέγγιση:</p>', unsafe_allow_html=True)
                        st.success(alt_code)

                    # ΑΠΟΘΗΚΕΥΣΗ ΜΕΣΩ SHEETDB
                    data_to_send = {
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Student_ID": str(student_id),
                        "Prompt": str(user_prompt),
                        "Answer": str(full_answer)
                    }
                    requests.post(SHEETDB_URL, json={"data": [data_to_send]})
                    
                except Exception as e:
                    st.error(f"❌ Σφάλμα: {e}")
        else:
            st.warning("⚠️ Παρακαλώ γράψε μια ερώτηση.")
    else:
        st.write("Η απάντηση θα εμφανιστεί εδώ μόλις πατήσετε το κουμπί.")

st.divider()
st.caption("AI STEM Lab v4.0 | Side-by-Side IDE Edition")
