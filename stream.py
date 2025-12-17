import streamlit as st
from datetime import datetime
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
    **PRS Hospital**  
    Killipalam  
    Thiruvananthapuram  
    Kerala – 695002
    """)

# Appointment Booking (clickable)
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
for num in ["+91 9678768843", "+91 9568746574"]:
    st.sidebar.markdown(f"⚠️ **{num}**")

# General Contact (non-clickable)
st.sidebar.subheader("📞 General Contact")
for num in ["+91 9448123456", "+91 9448234567"]:
    st.sidebar.markdown(f"📱 {num}")

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "active": False,
        "doctor": None,
        "day": None,
        "patient": None,
        "time": None
    }

# ===============================
# CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    align = "right" if msg["role"] == "user" else "left"
    bg = "#DCF8C6" if msg["role"] == "user" else "#F1F0F0"

    with st.chat_message(msg["role"]):
        st.markdown(f"""
        <div style="
            text-align:{align};
            background-color:{bg};
            padding:10px;
            border-radius:10px;
            margin:5px;
            display:inline-block;
            white-space:pre-line;">
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# ===============================
# INPUT
# ===============================
user_input = st.chat_input(
    "Ask about doctors, timings, availability, or book an appointment…"
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

    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)

        if not doctor:
            reply = "👨‍⚕️ Please specify the doctor's name."
        else:
            booking.update({
                "active": True,
                "doctor": doctor,
                "day": day
            })
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "⏰ Enter preferred time (example: **10am to 11am**)"

    elif booking["active"] and not booking["time"]:
        try:
            start, end = user_input.lower().split("to")
            start_t = datetime.strptime(start.strip(), "%I%p")
            end_t = datetime.strptime(end.strip(), "%I%p")

            if start_t < datetime.strptime("9am", "%I%p") or end_t > datetime.strptime("8pm", "%I%p"):
                reply = "⛔ Appointments allowed only between **9am and 8pm**."
            else:
                reply = book_appointment(
                    booking["doctor"],
                    booking["patient"],
                    booking["day"] or datetime.now().strftime("%A"),
                    user_input.lower()
                )
                st.session_state.booking = {
                    "active": False,
                    "doctor": None,
                    "day": None,
                    "patient": None,
                    "time": None
                }
        except:
            reply = "❌ Invalid format. Use **10am to 11am**."

    else:
        reply = run_chatbot_query(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    st.rerun()
