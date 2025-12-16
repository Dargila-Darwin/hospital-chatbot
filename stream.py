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
# Page config
# ===============================
st.set_page_config(page_title="PRS Hospital Chatbot", page_icon="🏥", layout="wide")

# ===============================
# Full background image
# ===============================
def set_full_background(image_path):
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
        .block-container {{
            background-color: rgba(255, 255, 255, 0.88);
            padding: 1.5rem;
            border-radius: 15px;
        }}
        section[data-testid="stSidebar"] {{
            background-color: rgba(255, 255, 255, 0.92);
        }}
        .chat-box {{
            height: 60vh;
            overflow-y: auto;
            padding: 10px;
        }}
        .user-msg {{
            background-color: rgba(0, 123, 255, 0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 60%;
            margin-left: auto;
            margin-bottom: 10px;
            word-wrap: break-word;
        }}
        .bot-msg {{
            background-color: rgba(220, 220, 220, 0.8);
            color: black;
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 60%;
            margin-bottom: 10px;
            word-wrap: break-word;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_full_background("hospital image.jpg")

# ===============================
# Sidebar
# ===============================
with st.sidebar.expander("About"):
    st.markdown("""
        <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; border:1px solid #ddd;">
            <h3>About</h3>
            <p>Our mission is to provide quality health care at competitive cost.</p>
            <p>37 years of excellence with modern facilities for 300 beds in Trivandrum.</p>
        </div>
    """, unsafe_allow_html=True)

with st.sidebar.expander("Specialities"):
    st.markdown("""
        <ul>
            <li>Cardiologist</li>
            <li>ENT</li>
            <li>Gastroenterologist</li>
            <li>Gynecologist</li>
            <li>Nephrologist</li>
            <li>Neurologist</li>
            <li>Urologist</li>
            <li>Pulmonologist</li>
            <li>Dermatologist</li>
            <li>Ophthalmologist</li>
            <li>Orthopaedician</li>
            <li>Oncologist</li>
            <li>Pathologist</li>
            <li>Radiologist</li>
            <li>Psychiatrist</li>
            <li>Psychologist</li>
            <li>Endocrinologist</li>
            <li>General Surgeon</li>
            <li>Paediatrician</li>
        </ul>
    """, unsafe_allow_html=True)

with st.sidebar.expander("Contact / Locate Us"):
    st.markdown("""
        <div style="text-align:center;">
            <b>📍 Killipalam, Trivandrum</b><br><br>
            🚑 Emergency & Ambulance<br>
            <span style="color:red; font-weight:bold;">+91 9497 247 365</span>
        </div>
    """, unsafe_allow_html=True)

# ===============================
# Session State
# ===============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "booking_state" not in st.session_state:
    st.session_state.booking_state = {"active": False, "doctor": None, "day": None}

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# ===============================
# Display Chat History in a scrollable box
# ===============================
st.subheader("💬 Hospital Chatbot Assistant")
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(
            f'<div class="user-msg">{message}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="bot-msg">{message.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# Chat input fixed at bottom
# ===============================
user_input = st.text_input("Type your message here:")

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
                ("Bot", f"📅 Booking appointment with {doctor_name}. Please fill the details below.")
            )
        else:
            st.session_state.chat_history.append(
                ("Bot", "Please specify a valid doctor to book an appointment.")
            )
    else:
        response = run_chatbot_query(user_input)
        st.session_state.chat_history.append(("Bot", response))

# ===============================
# Booking Form
# ===============================
if st.session_state.booking_state["active"]:
    st.markdown("---")
    st.write(f"📅 Booking appointment with **{st.session_state.booking_state['doctor']}**")

    patient_name = st.text_input("Enter your name")
    time_slot = st.text_input("Enter time slot (e.g., 10AM to 11AM)")

    if st.button("Confirm Appointment"):
        try:
            start_str, end_str = time_slot.split("to")
            start_hour = datetime.strptime(start_str.strip().upper(), "%I%p")
            end_hour = datetime.strptime(end_str.strip().upper(), "%I%p")

            earliest = datetime.strptime("9AM", "%I%p")
            latest = datetime.strptime("6PM", "%I%p")

            if start_hour < earliest or end_hour > latest:
                st.warning("⛔ Appointments only between 9AM and 6PM.")
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
            st.warning("⛔ Invalid time format. Use '10AM to 11AM'.")
