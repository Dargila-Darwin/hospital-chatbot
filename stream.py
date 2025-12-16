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
def set_bg(image):
    with open(image, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("data:image/jpg;base64,{img}");
            background-size: cover;
            background-attachment: fixed;
        }}

        /* HEADER FIXED */
        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            color: #084298;
            z-index: 1000;
            border-bottom: 2px solid #ccc;
        }}

        /* CHAT AREA */
        .chat-container {{
            margin-top: 90px;
            margin-bottom: 90px;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
            background: rgba(255,255,255,0.88);
            padding: 20px;
            border-radius: 20px;
            height: 65vh;
            overflow-y: auto;
        }}

        /* MESSAGES */
        .user {{
            background: #0d6efd;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            margin-bottom: 10px;
            max-width: 65%;
            margin-left: auto;
        }}

        .bot {{
            background: #f1f1f1;
            color: black;
            padding: 10px 15px;
            border-radius: 20px;
            margin-bottom: 10px;
            max-width: 65%;
        }}

        /* INPUT FIXED */
        .input-box {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            z-index: 1000;
            border-top: 2px solid #ccc;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("hospital image.jpg")

# ===============================
# Sidebar
# ===============================
with st.sidebar:
    st.markdown("## 🏥 PRS Hospital")

    with st.expander("ℹ️ About"):
        st.write(
            "PRS Hospital, Trivandrum – 37+ years of excellence in healthcare with modern facilities."
        )

    with st.expander("🩺 Specialities"):
        st.write("""
        Cardiologist, ENT, Gastroenterologist, Gynecologist,
        Nephrologist, Neurologist, Urologist, Pulmonologist,
        Dermatologist, Ophthalmologist, Orthopaedician,
        Oncologist, Psychiatrist, Endocrinologist, Paediatrician
        """)

    with st.expander("📞 Contact"):
        st.write("📍 Killipalam, Trivandrum")
        st.write("🚑 Emergency: +91 9497 247 365")

# ===============================
# Session State
# ===============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "booking_state" not in st.session_state:
    st.session_state.booking_state = {"active": False, "doctor": None, "day": None}

# ===============================
# HEADER (FIXED)
# ===============================
st.markdown(
    '<div class="header">PRS Hospital – Chatbot Assistant</div>',
    unsafe_allow_html=True
)

# ===============================
# CHAT AREA
# ===============================
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for sender, msg in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f'<div class="user">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="bot">{msg.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# INPUT FIXED AT BOTTOM
# ===============================
st.markdown('<div class="input-box">', unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message here…", label_visibility="collapsed")
    send = st.form_submit_button("Send")

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# PROCESS INPUT
# ===============================
if send and user_input:
    st.session_state.chat_history.append(("You", user_input))

    if "book appointment" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)

        if doctor:
            st.session_state.booking_state.update({
                "active": True,
                "doctor": doctor,
                "day": day
            })
            st.session_state.chat_history.append(
                ("Bot", f"📅 Booking appointment with {doctor}. Please provide details.")
            )
        else:
            st.session_state.chat_history.append(
                ("Bot", "Please specify a valid doctor name.")
            )
    else:
        reply = run_chatbot_query(user_input)
        st.session_state.chat_history.append(("Bot", reply))
