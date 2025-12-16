import streamlit as st
from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day,
    book_appointment
)
from datetime import datetime
import base64

# ===============================
# Page Config
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="wide"
)

# ===============================
# Background Image
# ===============================
def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        .main-container {{
            background-color: rgba(255,255,255,0.88);
            padding: 20px;
            border-radius: 20px;
        }}

        .chat-box {{
            height: 60vh;
            overflow-y: auto;
            padding: 10px;
        }}

        .user-msg {{
            background-color: rgba(0,123,255,0.85);
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 60%;
            margin-left: auto;
            margin-bottom: 10px;
        }}

        .bot-msg {{
            background-color: rgba(240,240,240,0.9);
            color: black;
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 60%;
            margin-bottom: 10px;
        }}

        .hospital-header {{
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #0b5394;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("hospital image.jpg")

# ===============================
# Sidebar
# ===============================
with st.sidebar:
    st.markdown("## 🏥 PRS Hospital")
    st.markdown("📍 Killipalam, Trivandrum")
    st.markdown("🚑 **Emergency:** +91 9497 247 365")
    st.markdown("---")
    st.markdown("### Specialities")
    st.markdown("""
    - Cardiologist  
    - ENT  
    - Gastroenterologist  
    - Gynecologist  
    - Neurologist  
    - Orthopaedician  
    - Paediatrician  
    """)

# ===============================
# Session State
# ===============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "booking_state" not in st.session_state:
    st.session_state.booking_state = {"active": False, "doctor": None, "day": None}

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# ===============================
# MAIN CONTAINER
# ===============================
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# ✅ HOSPITAL NAME (ALWAYS VISIBLE)
st.markdown('<div class="hospital-header">PRS Hospital – Chatbot Assistant</div>', unsafe_allow_html=True)

# ===============================
# CHAT DISPLAY
# ===============================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f'<div class="user-msg">{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="bot-msg">{message.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# CHAT INPUT (AUTO CLEAR)
# ===============================
user_input = st.text_input(
    "Type your message here 👇",
    key="chat_input"
)

if user_input and user_input != st.session_state.last_input:
    st.session_state.last_input = user_input
    st.session_state.chat_history.append(("You", user_input))

    if "book appointment" in user_input.lower():
        doctor_name = extract_doctor_name(user_input)
        requested_day = extract_day(user_input)

        if doctor_name:
            st.session_state.booking_state.update({
                "active": True,
                "doctor": doctor_name,
                "day": requested_day
            })
            st.session_state.chat_history.append(
                ("Bot", f"📅 Booking appointment with {doctor_name}. Please enter details below.")
            )
        else:
            st.session_state.chat_history.append(
                ("Bot", "Please specify a doctor name to book an appointment.")
            )
    else:
        response = run_chatbot_query(user_input)
        st.session_state.chat_history.append(("Bot", response))

    # ✅ CLEAR INPUT BOX
    st.session_state.chat_input = ""

# ===============================
# BOOKING FORM
# ===============================
if st.session_state.booking_state["active"]:
    st.markdown("---")
    st.write(f"📅 Booking appointment with **{st.session_state.booking_state['doctor']}**")

    patient_name = st.text_input("Patient Name")
    time_slot = st.text_input("Time Slot (e.g., 10AM to 11AM)")

    if st.button("Confirm Appointment"):
        try:
            start, end = time_slot.split("to")
            start_h = datetime.strptime(start.strip().upper(), "%I%p")
            end_h = datetime.strptime(end.strip().upper(), "%I%p")

            if start_h < datetime.strptime("9AM", "%I%p") or end_h > datetime.strptime("6PM", "%I%p"):
                st.warning("⛔ Appointments allowed only between 9AM and 6PM")
            else:
                result = book_appointment(
                    st.session_state.booking_state["doctor"],
                    patient_name,
                    st.session_state.booking_state["day"]
                    or datetime.now().strftime("%A").lower(),
                    time_slot
                )
                st.session_state.chat_history.append(("Bot", result))
                st.session_state.booking_state = {"active": False, "doctor": None, "day": None}
        except:
            st.warning("⛔ Invalid time format")

st.markdown('</div>', unsafe_allow_html=True)
