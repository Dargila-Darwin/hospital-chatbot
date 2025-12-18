import streamlit as st
from datetime import datetime, date, time
from collections import defaultdict

from chatbot import (
    run_chatbot_query,
    extract_doctor_name
)

# ======================================
# PAGE CONFIG (FIRST!)
# ======================================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ======================================
# BACKGROUND IMAGE + UI STYLING
# ======================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            rgba(255,255,255,0.92),
            rgba(255,255,255,0.92)
        ),
        url("hos-image.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    .chat-box {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 80%;
        margin-bottom: 8px;
    }

    .header {
        position: sticky;
        top: 0;
        z-index: 100;
        background-color: #ffffff;
        padding: 12px;
        border-bottom: 2px solid #084298;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: #084298;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================
# HEADER (ALWAYS VISIBLE)
# ======================================
st.markdown(
    '<div class="header">🏥 PRS Hospital – Chatbot Assistant</div>',
    unsafe_allow_html=True
)

# ======================================
# SIDEBAR
# ======================================
st.sidebar.title("🏥 Hospital Dashboard")

with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    **PRS Hospital, Trivandrum**  
    37+ years of trusted healthcare.
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

st.sidebar.subheader("📅 Appointment Booking")
appointment_numbers = ["+91 9876543210", "+91 9678547645", "+91 9234765840"]
for num in appointment_numbers:
    st.sidebar.markdown(f"📞 {num}")

st.sidebar.subheader("🚨 Emergency Numbers")
emergency_numbers = ["+91 9678768843", "+91 9568746574"]
for num in emergency_numbers:
    st.sidebar.markdown(f"⚠️ **{num}**")

st.sidebar.subheader("📞 General Contact Numbers")
general_numbers = ["+91 9448123456", "+91 9448234567"]
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
        "patient": None,
        "date": None,
        "time": None
    }

if "booking_count" not in st.session_state:
    st.session_state.booking_count = defaultdict(lambda: defaultdict(int))

# ======================================
# CHAT HISTORY (CLEAN & REALISTIC)
# ======================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(
            f'<div class="chat-box">{msg["content"]}</div>',
            unsafe_allow_html=True
        )

# ======================================
# USER INPUT (CLEARS AFTER SEND)
# ======================================
user_input = st.chat_input(
    "Ask about doctors, availability, or book appointment…"
)

# ======================================
# CHAT & BOOKING LOGIC
# ======================================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    booking = st.session_state.booking
    reply = ""

    # ----------------------------------
    # START BOOKING
    # ----------------------------------
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)

        if not doctor:
            reply = "👨‍⚕️ Please mention the doctor's name."
        else:
            booking.update({
                "active": True,
                "doctor": doctor
            })
            reply = f"📋 Booking appointment with **{doctor}**.\nPlease enter patient name."

    # ----------------------------------
    # PATIENT NAME
    # ----------------------------------
    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "📅 Please select appointment date below."

    # ----------------------------------
    # DATE PICKER
    # ----------------------------------
    elif booking["active"] and booking["patient"] and not booking["date"]:

        selected_date = st.date_input(
            "📅 Appointment Date",
            min_value=date.today()
        )
        booking["date"] = selected_date
        reply = "⏰ Please select appointment time."

    # ----------------------------------
    # TIME PICKER
    # ----------------------------------
    elif booking["active"] and booking["date"] and not booking["time"]:

        selected_time = st.time_input(
            "⏰ Appointment Time",
            value=time(10, 0)
        )

        if not time(9, 0) <= selected_time <= time(20, 0):
            reply = "⛔ Appointments allowed only between **9 AM and 8 PM**."

        elif booking["date"] == date.today() and selected_time <= datetime.now().time():
            reply = "⛔ You cannot book a past time."

        else:
            doctor = booking["doctor"]
            appt_date = booking["date"]

            availability = run_chatbot_query(
                f"{doctor} availability {appt_date.strftime('%A')}"
            )

            if "not available" in availability.lower():
                reply = f"❌ {doctor} is not available on {appt_date.strftime('%A')}."
            elif st.session_state.booking_count[doctor][appt_date] >= 20:
                reply = f"❌ All slots are booked for {doctor} on this date."
            else:
                st.session_state.booking_count[doctor][appt_date] += 1

                reply = (
                    f"✅ **Appointment Confirmed**\n\n"
                    f"👨‍⚕️ Doctor: {doctor}\n"
                    f"🧑 Patient: {booking['patient']}\n"
                    f"📅 Date: {appt_date.strftime('%d %B %Y')}\n"
                    f"⏰ Time: {selected_time.strftime('%I:%M %p')}\n"
                    f"📊 Slots Left: {20 - st.session_state.booking_count[doctor][appt_date]}"
                )

                st.session_state.booking = {
                    "active": False,
                    "doctor": None,
                    "patient": None,
                    "date": None,
                    "time": None
                }

    # ----------------------------------
    # NORMAL CHAT (LINE-BY-LINE DOCTORS)
    # ----------------------------------
    else:
        response = run_chatbot_query(user_input)

        if "Dr." in response:
            reply = "\n".join(
                [f"👨‍⚕️ {line.strip()}" for line in response.split(",")]
            )
        else:
            reply = response

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()




















