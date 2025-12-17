import streamlit as st
from datetime import datetime
import re
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
# TITLE (FIXED AT TOP)
# ===============================
st.markdown(
    """
    <h1 style="text-align:center; color:#084298;">🏥 PRS Hospital – Chatbot Assistant</h1>
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
    37+ years of excellence in healthcare.
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

with st.sidebar.expander("📍 Location / Contact"):
    st.markdown("""
    📍 Killipalam, Trivandrum  
    🚑 Emergency: **+91 9497 247 365**
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
# HELPER: FORMAT DOCTORS (LINE BY LINE)
# ===============================
def format_doctor_list(text: str) -> str:
    """
    Converts doctor listings into line-by-line format
    """
    # Extract pattern like: Dr. Name - 10am to 11am
    doctors = re.findall(r"Dr\. [A-Za-z\s\.]+ - [0-9:\samPMto]+", text, re.IGNORECASE)
    if doctors:
        return "\n".join([d.replace("AM","am").replace("PM","pm") for d in doctors])
    return text

# ===============================
# DISPLAY CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].replace("\n", "<br>"), unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, timings, availability, or booking…")

# ===============================
# CHAT + BOOKING LOGIC
# ===============================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    booking = st.session_state.booking

    # ---- BOOK APPOINTMENT FLOW ----
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)

        if not doctor:
            reply = "👨‍⚕️ Please specify the doctor's name to book an appointment."
        else:
            booking.update({"active": True, "doctor": doctor, "day": day})
            reply = f"📅 Booking appointment with **{doctor}**. Please tell your name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "⏰ Enter preferred time (example: **10am to 11am**)."

    elif booking["active"] and not booking["time"]:
        try:
            start, end = user_input.lower().split("to")
            start_t = datetime.strptime(start.strip(), "%I%p")
            end_t = datetime.strptime(end.strip(), "%I%p")

            if start_t < datetime.strptime("9am", "%I%p") or end_t > datetime.strptime("8pm", "%I%p"):
                reply = "⛔ Appointments allowed only between **9am and 8pm**."
            else:
                booking["time"] = user_input.lower()
                reply = book_appointment(
                    booking["doctor"],
                    booking["patient"],
                    booking["day"] or datetime.now().strftime("%A"),
                    booking["time"]
                )
                st.session_state.booking = {"active": False, "doctor": None, "day": None, "patient": None, "time": None}
        except:
            reply = "❌ Invalid format. Use **10am to 11am**."

    # ---- NORMAL CHAT ----
    else:
        reply = run_chatbot_query(user_input)
        reply = format_doctor_list(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
