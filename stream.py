import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import run_chatbot_query, extract_doctor_name

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot Assistant",
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

<div class="header">🏥 PRS Hospital Chatbot Assistant</div>
<div class="content"></div>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("🏥 PRS Hospital")

    with st.expander("ℹ️ About"):
        st.write(
            "PRS Hospital, Thiruvananthapuram, has over 37 years of excellence "
            "in multi-specialty healthcare and advanced medical services."
        )

    # Clickable Specialities
    with st.expander("🩺 Specialities"):
        specialities = [
            "Cardiologist", "ENT", "Gastroenterologist", "Gynecologist",
            "Nephrologist", "Neurologist", "Urologist", "Pulmonologist",
            "Dermatologist", "Ophthalmologist", "Orthopaedician", "Oncologist",
            "Pathologist", "Radiologist", "Psychiatrist", "Psychologist",
            "Endocrinologist", "General Surgeon", "Paediatrician"
        ]

        for spec in specialities:
            if st.button(spec, key=f"spec_{spec}"):
                st.session_state.selected_speciality = spec
                st.rerun()

    with st.expander("📍 Location"):
        st.markdown("""
        **PRS Hospital**  
        Killipalam,  
        Thiruvananthapuram, Kerala – 695002
        """)

    st.markdown("### 📞 Appointment Booking")
    st.markdown("📞 +91 98765 43210")
    st.markdown("📞 +91 96785 47645")

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

if "selected_speciality" not in st.session_state:
    st.session_state.selected_speciality = None

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

    for col in ["Doctor Name", "Patient Name", "Day", "Time"]:
        if col not in df.columns:
            df[col] = ""

    slots = df[
        (df["Doctor Name"] == doc) &
        (df["Day"] == str(d))
    ]

    if len(slots) >= MAX_SLOTS_PER_DOCTOR:
        return f"⛔ Slot full for **{doc}** on **{d}**."

    new_row = {
        "Doctor Name": doc,
        "Patient Name": patient,
        "Day": str(d),
        "Time": t
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(APPT_FILE, index=False)

    return (
        f"✅ **Appointment Confirmed**\n\n"
        f"👨‍⚕️ Doctor: **{doc}**\n"
        f"👤 Patient: **{patient}**\n"
        f"📅 Date: **{d}**\n"
        f"⏰ Time: **{t}**"
    )

def get_available_slots(doctor_name, d):
    df = pd.read_csv(APPT_FILE)
    booked = df[
        (df["Doctor Name"] == doctor_name) &
        (df["Day"] == str(d))
    ]
    return MAX_SLOTS_PER_DOCTOR - len(booked)

# ===============================
# SPECIALITY AUTO RESPONSE
# ===============================
if st.session_state.selected_speciality:
    spec = st.session_state.selected_speciality
    response = run_chatbot_query(f"list {spec} doctors")

    formatted = ""
    for line in response.split("\n"):
        if line.strip():
            formatted += f"• {line.strip()}\n"

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"🩺 **{spec} Doctors Available:**\n\n{formatted}"
    })

    st.session_state.selected_speciality = None
    st.rerun()

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
    "Ask about doctors, availability, or book an appointment"
)

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    booking = st.session_state.booking
    reply = None

    if booking["step"] == "patient":
        booking["patient"] = user_input.strip()
        booking["step"] = "date"
        reply = "📆 Please select appointment date below."

    elif "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "Please mention the doctor name."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📅 Booking appointment with **{doctor}**.\nEnter patient name."

    else:
        response = run_chatbot_query(user_input)

        doctor = extract_doctor_name(user_input)
        if doctor:
            today = date.today()
            slots = get_available_slots(doctor, today)
            response += f"\n\n📅 **Available slots today ({today})**: {slots}/{MAX_SLOTS_PER_DOCTOR}"

        reply = ""
        for line in response.split("\n"):
            if line.strip():
                reply += f"• {line.strip()}\n"

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )
    st.rerun()

# ===============================
# DATE & TIME PICKER
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
    selected_time = st.time_input("Select Time", value=time(9, 0))

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

            st.session_state.booking = {
                "step": None,
                "doctor": None,
                "patient": None,
                "date": None,
                "time": None
            }
            st.rerun()
