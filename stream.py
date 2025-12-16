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
# TITLE (ALWAYS AT TOP)
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
with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    **PRS Hospital, Trivandrum**  
    37+ years of excellence in healthcare with modern facilities.
    """)

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

with st.sidebar.expander("📞 Contact / Locate Us"):
    st.markdown("""
    📍 **Killipalam, Trivandrum**  
    🚑 **Emergency & Ambulance**  
    **+91 9497 247 365**
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
        "day": None,
        "patient": None,
        "time": None
    }

# ===============================
# HELPER: FORMAT DOCTOR LIST
# ===============================
def format_doctor_list(text: str) -> str:
    """
    Ensures each doctor starts on a new line.
    """
    return text.replace(" Dr.", "\nDr.")

# ===============================
# CHAT HISTORY (SCROLLS UP)
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===============================
# INPUT (FIXED AT BOTTOM)
# ===============================
user_input = st.chat_input("Type your message here…")

# ===============================
# CHAT + BOOKING LOGIC
# ===============================
if user_input:
    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    booking = st.session_state.booking

    # ---------- BOOK APPOINTMENT ----------
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)

        if not doctor:
            reply = "👨‍⚕️ Please specify the doctor's name to book an appointment."
        else:
            booking.update({
                "active": True,
                "doctor": doctor,
                "day": day
            })
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease tell your name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "⏰ Please enter preferred time (example: 10AM to 11AM)."

    elif booking["active"] and not booking["time"]:
        try:
            start, end = user_input.upper().split("TO")
            start_t = datetime.strptime(start.strip(), "%I%p")
            end_t = datetime.strptime(end.strip(), "%I%p")

            earliest = datetime.strptime("9AM", "%I%p")
            latest = datetime.strptime("8PM", "%I%p")

            if start_t < earliest or end_t > latest:
                reply = "⛔ Appointments are allowed only between **9AM and 8PM**."
            else:
                booking["time"] = user_input
                reply = book_appointment(
                    booking["doctor"],
                    booking["patient"],
                    booking["day"] or datetime.now().strftime("%A"),
                    booking["time"]
                )

                # Reset booking
                st.session_state.booking = {
                    "active": False,
                    "doctor": None,
                    "day": None,
                    "patient": None,
                    "time": None
                }
        except:
            reply = "❌ Invalid time format. Use **10AM to 11AM**."

    # ---------- NORMAL CHAT ----------
    else:
        reply = run_chatbot_query(user_input)
        reply = format_doctor_list(reply)   # 👈 ONLY CHANGE APPLIED

    # Show bot reply
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    # Rerun to move chat upward
    st.rerun()
