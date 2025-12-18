import streamlit as st
import pandas as pd
from datetime import datetime, date, time

from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    book_appointment
)

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)


# ===============================
# STICKY CENTERED HEADER
# ===============================
st.markdown("""
<style>
.header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background: white;
    z-index: 1000;
    padding: 14px 0;
    border-bottom: 1px solid #ddd;
    text-align: center;
    font-size: 26px;
    font-weight: bold;
    color: #084298;
}
.content {
    margin-top: 90px;
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

    with st.expander("🩺 Specialities"):
        specialities = [
            "Cardiologist", "ENT", "Gastroenterologist", "Gynecologist",
            "Nephrologist", "Neurologist", "Urologist", "Pulmonologist",
            "Dermatologist", "Ophthalmologist", "Orthopaedician", "Oncologist",
            "Pathologist", "Radiologist", "Psychiatrist", "Psychologist",
            "Endocrinologist", "General Surgeon", "Paediatrician"
        ]

        for spec in specialities:
            if st.button(spec, key=spec):
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
        "date": None
    }

if "selected_speciality" not in st.session_state:
    st.session_state.selected_speciality = None

# ===============================
# HELPER
# ===============================
def get_day_name(d):
    return d.strftime("%A").lower()

def format_doctors_line_by_line(response):
    formatted = ""
    parts = response.replace("•", "\n").split("\n")
    for p in parts:
        p = p.strip()
        if p:
            formatted += f"👨‍⚕️ {p}\n"
    return formatted

# ===============================
# SPECIALITY CLICK HANDLER
# ===============================
if st.session_state.selected_speciality:
    spec = st.session_state.selected_speciality
    response = run_chatbot_query(f"{spec} doctors today")

    formatted = format_doctors_line_by_line(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"🩺 **{spec} Doctors Available Today:**\n\n{formatted}"
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
    reply = ""

    # ===============================
    # BOOKING FLOW
    # ===============================
    if booking["step"] == "patient":
        booking["patient"] = user_input.strip()
        booking["step"] = "date"
        reply = "📅 Please select appointment date below."

    elif "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "❗ Please mention the doctor name."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📝 Booking appointment with **{doctor}**.\n\nPlease enter patient name."

    else:
        response = run_chatbot_query(user_input)
        reply = format_doctors_line_by_line(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )
    st.rerun()

# ===============================
# DATE SELECTION
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

# ===============================
# TIME SELECTION (FINAL BOOKING)
# ===============================
if booking["step"] == "time":
    selected_time = st.time_input(
        "Select Time",
        value=time(9, 0)
    )

    if st.button("Confirm Appointment"):
        if not time(9, 0) <= selected_time <= time(20, 0):
            st.error("⛔ Appointments allowed only between 9 AM and 8 PM.")
        else:
            day_name = get_day_name(booking["date"])

            result = book_appointment(
                booking["doctor"],
                booking["patient"],
                day_name,
                selected_time.strftime("%I:%M%p")
            )

            st.session_state.messages.append(
                {"role": "assistant", "content": result}
            )

            st.session_state.booking = {
                "step": None,
                "doctor": None,
                "patient": None,
                "date": None
            }
            st.rerun()

