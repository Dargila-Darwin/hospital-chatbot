import streamlit as st
from datetime import datetime, date, time

from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day,
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
# FIXED TITLE
# ===============================
st.markdown(
    """
    <h1 style="text-align:center; color:#084298;">
        🏥 PRS Hospital – Chatbot Assistant
    </h1>
    <hr>
    """,
    unsafe_allow_html=True
)

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
    - Psychiatrist  
    - Paediatrician  
    """)

with st.sidebar.expander("📍 Location"):
    st.markdown("""
    **PRS Hospital**  
    Killipalam, Thiruvananthapuram  
    Kerala – 695002
    """)

# ===============================
# SESSION STATE
# ===============================
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

# ===============================
# CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input(
    "Ask about doctors, availability, or book an appointment…"
)

# ===============================
# CHAT + BOOKING LOGIC
# ===============================
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    booking = st.session_state.booking

    # ---------- START BOOKING ----------
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)

        if not doctor:
            reply = "👨‍⚕️ Please mention the doctor's name."
        else:
            booking["active"] = True
            booking["doctor"] = doctor
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter **patient name**."

    # ---------- PATIENT NAME ----------
    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "📅 Please select appointment **date** below."

    # ---------- DATE PICKER ----------
    elif booking["active"] and not booking["date"]:
        selected_date = st.date_input(
            "Select appointment date",
            min_value=date.today()
        )

        booking["date"] = selected_date
        reply = "⏰ Now select **appointment time**."

    # ---------- TIME PICKER ----------
    elif booking["active"] and not booking["time"]:
        selected_time = st.time_input(
            "Select appointment time",
            value=time(10, 0)
        )

        # Global hospital rule
        if not time(9, 0) <= selected_time <= time(20, 0):
            reply = "⛔ Appointments allowed only between **9 AM – 8 PM**."
        else:
            booking["time"] = selected_time.strftime("%I%p")
            day_name = booking["date"].strftime("%A")

            reply = book_appointment(
                booking["doctor"],
                booking["patient"],
                day_name,
                booking["time"]
            )

            # Reset booking state
            st.session_state.booking = {
                "active": False,
                "doctor": None,
                "patient": None,
                "date": None,
                "time": None
            }

    # ---------- NORMAL CHAT ----------
    else:
        reply = run_chatbot_query(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    st.rerun()
