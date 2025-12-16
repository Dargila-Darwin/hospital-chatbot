import streamlit as st
import base64
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
    layout="wide"
)

# ===============================
# BACKGROUND IMAGE
# ===============================
def set_bg(image_path):
    with open(image_path, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("data:image/jpg;base64,{img}");
            background-size: cover;
            background-attachment: fixed;
        }}

        /* HEADER */
        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
            background: rgba(255,255,255,0.96);
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            color: #084298;
            padding-top: 15px;
            z-index: 1000;
            border-bottom: 2px solid #ccc;
        }}

        /* CHAT AREA */
        .chat {{
            margin-top: 90px;
            margin-bottom: 90px;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
            padding: 20px;
            background: rgba(255,255,255,0.88);
            border-radius: 20px;
            height: 65vh;
            overflow-y: auto;
        }}

        /* USER MESSAGE */
        .user {{
            background: #0d6efd;
            color: white;
            padding: 12px 18px;
            border-radius: 20px;
            margin-bottom: 10px;
            max-width: 70%;
            margin-left: auto;
        }}

        /* BOT MESSAGE */
        .bot {{
            background: #f1f1f1;
            color: black;
            padding: 12px 18px;
            border-radius: 20px;
            margin-bottom: 10px;
            max-width: 70%;
        }}

        /* INPUT BAR */
        .input {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 15px;
            background: rgba(255,255,255,0.96);
            z-index: 1000;
            border-top: 2px solid #ccc;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("hospital image.jpg")

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.markdown("## 🏥 PRS Hospital")

    with st.expander("ℹ️ About"):
        st.write(
            "PRS Hospital, Trivandrum – 37+ years of excellence in healthcare."
        )

    with st.expander("🩺 Specialities"):
        st.write("""
        Cardiologist, ENT, Gastroenterologist, Gynecologist,
        Neurologist, Orthopaedician, Dermatologist, Psychiatrist,
        Endocrinologist, Paediatrician
        """)

    with st.expander("📞 Contact"):
        st.write("📍 Killipalam, Trivandrum")
        st.write("🚑 Emergency: +91 9497 247 365")

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
# HEADER
# ===============================
st.markdown(
    '<div class="header">PRS Hospital – Chatbot Assistant</div>',
    unsafe_allow_html=True
)

# ===============================
# CHAT DISPLAY
# ===============================
st.markdown('<div class="chat">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="bot">{msg["content"].replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# INPUT (FIXED)
# ===============================
st.markdown('<div class="input">', unsafe_allow_html=True)
user_input = st.chat_input("Type your message here...")
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# CHAT LOGIC + BOOKING
# ===============================
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    booking = st.session_state.booking

    # START BOOKING
    if not booking["active"] and "book appointment" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)

        if not doctor:
            reply = "Please tell me the doctor's name."
        else:
            booking["active"] = True
            booking["doctor"] = doctor
            booking["day"] = day
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease tell me your name."

    # PATIENT NAME
    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input
        reply = "Please tell your preferred time (example: 10AM to 11AM)."

    # TIME
    elif booking["active"] and not booking["time"]:
        try:
            start, end = user_input.upper().split("TO")
            start_t = datetime.strptime(start.strip(), "%I%p")
            end_t = datetime.strptime(end.strip(), "%I%p")

            if start_t < datetime.strptime("9AM", "%I%p") or end_t > datetime.strptime("6PM", "%I%p"):
                reply = "⛔ Appointments are only between 9AM and 6PM."
            else:
                booking["time"] = user_input
                result = book_appointment(
                    booking["doctor"],
                    booking["patient"],
                    booking["day"] or datetime.now().strftime("%A"),
                    booking["time"]
                )
                reply = f"✅ {result}"

                # RESET
                st.session_state.booking = {
                    "active": False,
                    "doctor": None,
                    "day": None,
                    "patient": None,
                    "time": None
                }
        except:
            reply = "❌ Invalid time format. Use: 10AM to 11AM"

    # NORMAL CHAT
    else:
        reply = run_chatbot_query(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })
