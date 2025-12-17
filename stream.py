# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import run_chatbot_query, extract_doctor_name

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# STICKY HEADER
# ===============================
st.markdown("""
<style>
.header {
    position: fixed;
    top: 0;
    width: 100%;
    background: white;
    z-index: 999;
    padding: 10px;
    border-bottom: 1px solid #ddd;
    text-align: center;
    font-size: 26px;
    font-weight: bold;
    color: #084298;
}
.content {
    margin-top: 80px;
}
</style>

<div class="header">🏥 PRS Hospital – Chatbot Assistant</div>
<div class="content"></div>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR WITH EXPANDERS
# ===============================
with st.sidebar:
    st.title("🏥 PRS Hospital")

    # About
    with st.expander("ℹ️ About"):
        st.write(
            "PRS Hospital, Thiruvananthapuram, has over 37 years of excellence "
            "in multi-specialty healthcare and advanced medical services."
        )

    # Specialities
    with st.expander("🩺 Specialities"):
        specialities = [
            "Cardiologist", "ENT", "Gastroenterologist", "Gynecologist",
            "Nephrologist", "Neurologist", "Urologist", "Pulmonologist",
            "Dermatologist", "Ophthalmologist", "Orthopaedician", "Oncologist",
            "Pathologist", "Radiologist", "Psychiatrist", "Psychologist",
            "Endocrinologist", "General Surgeon", "Paediatrician"
        ]
        for spec in specialities:
            st.markdown(f"- {spec}")

    # Location
    with st.expander("📍 Location"):
        st.markdown("""
        **PRS Hospital**  
        Killipalam,  
        Thiruvananthapuram, Kerala – 695002
        """)

    # Appointment Booking
    st.markdown("### 📞 Appointment Booking")
    st.markdown("📞 +91 98765 43210")
    st.markdown("📞 +91 96785 47645")
    st.markdown("[📲 Call Hospital](tel:+919876543210)")

    # Emergency
    st.markdown("### ☎️ Emergency")
    st.markdown("🚨 **+91 95687 46574**")

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
# APPOINTMENT STORAGE
# ===============================
APPT_FILE = "appointments.csv"
MAX_SLOTS_PER_DOCTOR = 5

if not pd.io.common.file_exists(APPT_FILE):
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Day", "Time"]
    ).to_csv(APPT_FILE, index=False)

def save_appointment(doc, patient, d, t):
    df = pd.read_csv(APPT_FILE)
    slots = df[(df["Doctor Name"] == doc) & (df["Day"] == str(d))]

    if len(slots) >= MAX_SLOTS_PER_DOCTOR:
        return f"⛔ Slot full for **{doc}** on **{d}**."

    df.loc[len(df)] = [doc, patient, str(d), t]
    df.to_csv(APPT_FILE, index=False)

    return (
        f"✅ **Appointment Confirmed**\n\n"
        f"👨‍⚕️ Doctor: **{doc}**\n"
        f"👤 Patient: **{patient}**\n"
        f"📅 Date: **{d}**\n"
        f"⏰ Time: **{t}**"
    )

# ===============================
# CHAT DISPLAY
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input(
    "Ask about doctors, availability, degree, location, or book appointment"
)

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    booking = st.session_state.booking
    reply = None

    # ---------- BOOKING FLOW ----------
    if booking["step"] is not None:
        if booking["step"] == "patient":
            booking["patient"] = user_input.strip()
            booking["step"] = "date"
            reply = "📆 Please select appointment date below."
        else:
            reply = "⚠️ Please complete the appointment booking steps below."

    elif "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "Please mention the doctor name to book an appointment."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    else:
        # Run chatbot query
        response = run_chatbot_query(user_input)

        # If the response includes multiple doctors, split line by line
        if "\n" in response:
            response_lines = response.split("\n")
            reply = ""
            for line in response_lines:
                reply += f"{line}\n"
        else:
            reply = response

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )
    st.rerun()

# ===============================
# CALENDAR & TIME PICKER
# ===============================
booking = st.session_state.booking

if booking["step"] == "date":
    selected_date = st.date_input(
        "Select Appointment Date",
        min_value=date.today()
    )
    if st.button("Confirm Date"):
        booking["date"] = selected_date
        booking["step"] = "time"
        st.rerun()

if booking["step"] == "time":
    selected_time = st.time_input(
        "Select Time",
        value=time(9, 0)
    )

    if st.button("Confirm Time"):
        combined = datetime.combine(booking["date"], selected_time)

        if combined < datetime.now():
            st.error("⛔ Cannot book past time.")
        elif not time(9, 0) <= selected_time <= time(20, 0):
            st.error("⛔ Appointments allowed only between 9 AM and 8 PM.")
        else:
            result = save_appointment(
                booking["doctor"],
                booking["patient"],
                booking["date"],
                selected_time.strftime("%I:%M %p")
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": result}
            )
            # Reset booking
            st.session_state.booking = {
                "step": None,
                "doctor": None,
                "patient": None,
                "date": None,
                "time": None
            }
            st.rerun()
