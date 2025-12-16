import streamlit as st
from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day,
    book_appointment
)
from datetime import datetime

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# FIXED TITLE (ALWAYS ON TOP)
# ===============================
st.markdown(
    """
    <h1 style="
        text-align:center;
        color:#084298;
        border-bottom:2px solid #ddd;
        padding-bottom:10px;
        margin-bottom:20px;">
        🏥 PRS Hospital – Chatbot Assistant
    </h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    Our mission is to provide quality health care at competitive cost.  
    **37+ years of excellence** with modern facilities in Trivandrum.
    """)

with st.sidebar.expander("🩺 Specialities"):
    st.markdown("""
    - Cardiologist  
    - ENT  
    - Gastroenterologist  
    - Gynecologist  
    - Neurologist  
    - Orthopaedician  
    - Dermatologist  
    - Psychiatrist  
    - Endocrinologist  
    - Paediatrician  
    """)

with st.sidebar.expander("📞 Contact / Locate Us"):
    st.markdown("""
    📍 Killipalam, Trivandrum  
    🚑 **Emergency:** +91 9497 247 365
    """)

# ===============================
# SESSION STATE
# ===============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "booking_state" not in st.session_state:
    st.session_state.booking_state = {
        "active": False,
        "doctor": None,
        "day": None,
        "patient": None,
        "time": None
    }

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# ===============================
# CHAT INPUT
# ===============================
st.subheader("💬 Ask me anything")
user_input = st.text_input("Type your message and press Enter")

# ===============================
# HANDLE USER INPUT (NO DUPLICATES)
# ===============================
if user_input and user_input != st.session_state.last_input:
    st.session_state.last_input = user_input
    st.session_state.chat_history.append(("You", user_input))

    booking = st.session_state.booking_state

    # ---------- BOOKING START ----------
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
                st.session_state.booking_state = {
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

    st.session_state.chat_history.append(("Bot", reply))

# ===============================
# CHAT HISTORY DISPLAY
# ===============================
st.markdown("---")
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(
            f"""
            <div style="background:#f1f1f1;
                        padding:10px;
                        border-radius:10px;
                        margin-bottom:10px;">
                <strong>Bot:</strong><br>
                {message.replace(chr(10), "<br>")}
            </div>
            """,
            unsafe_allow_html=True
        )
