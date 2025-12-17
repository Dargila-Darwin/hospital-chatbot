# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import run_chatbot_query, extract_doctor_name, df, is_doctor_available, book_appointment

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# TITLE
# ===============================
st.markdown("""
<h1 style="text-align:center; color:#084298;">
🏥 PRS Hospital – Chatbot Assistant
</h1>
<hr>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("🏥 Hospital Dashboard")

with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    **PRS Hospital, Trivandrum**  
    37+ years of excellence in healthcare.
    """)

with st.sidebar.expander("🩺 Specialities"):
    st.markdown("""
    - Cardiologist  
    - ENT  
    - Gastroenterologist  
    - Gynecologist  
    - Nephrologist  
    - Neurologist  
    - Urologist  
    - Pulmonologist  
    - Dermatologist  
    - Ophthalmologist  
    - Orthopaedician  
    - Oncologist  
    - Pathologist  
    - Radiologist  
    - Psychiatrist  
    - Psychologist  
    - Endocrinologist  
    - General Surgeon  
    - Paediatrician  

    """)

with st.sidebar.expander("📍 Location"):
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram, Kerala – 695002
    """)

st.sidebar.subheader("📅 Appointment Booking")
HOSPITAL_CONTACTS = ["+91 9876543210", "+91 9678547645"]
for num in HOSPITAL_CONTACTS:
    st.sidebar.markdown(f"📞 {num}")
    st.sidebar.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

st.sidebar.subheader("🚨 Emergency")
st.sidebar.markdown("⚠️ **+91 9568746574**")

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "step": None,
        "doctor": None,
        "patient": None,
        "date": None,
        "time": None
    }

# ===============================
# CHAT DISPLAY
# ===============================
for msg in st.session_state.messages:
    align = "right" if msg["role"] == "user" else "left"
    color = "#DCF8C6" if msg["role"] == "user" else "#F1F0F0"

    with st.chat_message(msg["role"]):
        st.markdown(f"""
        <div style="
            text-align:{align};
            background:{color};
            padding:10px;
            border-radius:10px;
            display:inline-block;
            white-space:pre-line;
        ">
        {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, speciality, degree, location, or book appointment")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    booking = st.session_state.booking
    reply = ""

    # ---------------- BOOKING FLOW ----------------
    if "book" in user_input.lower() and booking["step"] is None:
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "Please mention doctor name for booking."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    elif booking["step"] == "patient":
        booking["patient"] = user_input.strip()
        booking["step"] = "date"
        reply = "📆 Select appointment date from calendar below."

    elif booking["step"] in ["date", "time"]:
        pass  # handled below

    else:
        reply = run_chatbot_query(user_input)

    if reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ===============================
# CALENDAR + TIME UI
# ===============================
booking = st.session_state.booking

if booking["step"] == "date":
    d = st.date_input("Select appointment date", min_value=date.today())
    if st.button("Confirm Date"):
        booking["date"] = d
        booking["step"] = "time"
        st.rerun()

if booking["step"] == "time":
    selected_doctor = df[df["Doctor Name"] == booking["doctor"]].iloc[0]
    consult_start, consult_end = selected_doctor["Consultation Time"].split("to")
    consult_start = datetime.strptime(consult_start.strip(), "%I%p").time()
    consult_end = datetime.strptime(consult_end.strip(), "%I%p").time()

    t = st.time_input(
        f"Select appointment time (available: {consult_start.strftime('%I:%M%p')} to {consult_end.strftime('%I:%M%p')})",
        value=consult_start
    )

    if st.button("Confirm Time"):
        # Check availability
        appointment_result = book_appointment(selected_doctor, booking["patient"], booking["date"], t)
        st.session_state.messages.append({"role": "assistant", "content": appointment_result})

        # Reset booking
        st.session_state.booking = {
            "step": None,
            "doctor": None,
            "patient": None,
            "date": None,
            "time": None
        }
        st.rerun()
