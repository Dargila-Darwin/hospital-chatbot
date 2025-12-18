import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, time

from chatbot import (
    run_chatbot_query,
    extract_doctor_name
)

# ======================================
# FILE SETUP
# ======================================
APPT_FILE = "appointments.csv"

if not os.path.exists(APPT_FILE):
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Day", "Time"]
    ).to_csv(APPT_FILE, index=False)

# ======================================
# PAGE CONFIG
# ======================================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ======================================
# HEADER (ALWAYS VISIBLE)
# ======================================
st.markdown(
    """
    <h1 style="text-align:center; color:#084298; margin-bottom:0;">
        🏥 PRS Hospital – Chatbot Assistant
    </h1>
    <hr>
    """,
    unsafe_allow_html=True
)

# ======================================
# SIDEBAR (UNCHANGED – FULL)
# ======================================
st.sidebar.title("🏥 Hospital Dashboard")

with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
**PRS Hospital, Trivandrum**  
37+ years of excellence in healthcare with modern facilities.
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
Killipalam,  
Thiruvananthapuram,  
Kerala – 695002
""")

# Appointment numbers (clickable)
st.sidebar.subheader("📅 Appointment Booking")
appointment_numbers = [
    "+91 9876543210",
    "+91 9678547645",
    "+91 9234765840"
]
for num in appointment_numbers:
    st.sidebar.markdown(f"[📞 {num}](tel:{num.replace(' ', '')})")

# Emergency (non-clickable)
st.sidebar.subheader("🚨 Emergency Numbers")
emergency_numbers = [
    "+91 9678768843",
    "+91 9568746574"
]
for num in emergency_numbers:
    st.sidebar.markdown(f"⚠️ **{num}**")

# General contact
st.sidebar.subheader("📞 General Contact Numbers")
general_numbers = [
    "+91 9448123456",
    "+91 9448234567"
]
for num in general_numbers:
    st.sidebar.markdown(f"📱 {num}")

# ======================================
# SESSION STATE
# ======================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "active": False,
        "doctor": None,
        "patient": None
    }

# ======================================
# CHAT HISTORY
# ======================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ======================================
# USER INPUT
# ======================================
user_input = st.chat_input(
    "Ask about doctors, availability, or book an appointment…"
)

# ======================================
# CHAT LOGIC
# ======================================
if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    booking = st.session_state.booking
    reply = ""

    # START BOOKING
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)

        if not doctor:
            reply = "👨‍⚕️ Please mention the doctor's name."
        else:
            booking["active"] = True
            booking["doctor"] = doctor
            reply = (
                f"📋 Booking appointment with **{doctor}**.\n"
                "Please enter patient name."
            )

    # PATIENT NAME
    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "📅 Please select date & time below to confirm."

    # NORMAL CHAT
    else:
        response = run_chatbot_query(user_input)

        # Doctors line-by-line
        if "Dr." in response:
            reply = "\n".join(
                [f"👨‍⚕️ {d.strip()}" for d in response.split(",")]
            )
        else:
            reply = response

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )
    st.rerun()

# ======================================
# BOOKING PANEL (STABLE & CORRECT)
# ======================================
booking = st.session_state.booking

if booking["active"] and booking["patient"]:

    st.subheader("📅 Appointment Details")

    selected_date = st.date_input(
        "Select Appointment Date",
        min_value=date.today()
    )

    selected_time = st.time_input(
        "Select Appointment Time",
        value=time(10, 0)
    )

    if st.button("✅ Confirm Appointment"):

        # Time validation
        if not time(9, 0) <= selected_time <= time(20, 0):
            st.error("⛔ Appointments allowed only between 9 AM and 8 PM.")

        elif (
            selected_date == date.today()
            and selected_time <= datetime.now().time()
        ):
            st.error("⛔ Cannot book past time.")

        else:
            weekday = selected_date.strftime("%A")

            # Doctor availability
            availability = run_chatbot_query(
                f"{booking['doctor']} availability {weekday}"
            )

            if "not available" in availability.lower():
                st.error(
                    f"❌ {booking['doctor']} is not available on {weekday}."
                )

            else:
                df = pd.read_csv(APPT_FILE)

                todays_bookings = df[
                    (df["Doctor Name"] == booking["doctor"]) &
                    (df["Day"] == weekday)
                ]

                if len(todays_bookings) >= 20:
                    st.error(
                        f"❌ All 20 slots are full for "
                        f"{booking['doctor']} on {weekday}."
                    )
                else:
                    new_row = {
                        "Doctor Name": booking["doctor"],
                        "Patient Name": booking["patient"],
                        "Day": weekday,
                        "Time": selected_time.strftime("%I:%M %p")
                    }

                    df = pd.concat(
                        [df, pd.DataFrame([new_row])],
                        ignore_index=True
                    )
                    df.to_csv(APPT_FILE, index=False)

                    st.success(
                        f"""
✅ **Appointment Confirmed**

👨‍⚕️ Doctor: {booking['doctor']}  
🧑 Patient: {booking['patient']}  
📅 Day: {weekday}  
⏰ Time: {selected_time.strftime('%I:%M %p')}  
📊 Slot: {len(todays_bookings)+1}/20
"""
                    )

                    # RESET
                    st.session_state.booking = {
                        "active": False,
                        "doctor": None,
                        "patient": None
                    }
