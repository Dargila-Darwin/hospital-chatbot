import streamlit as st
import pandas as pd
from datetime import datetime, time
from chatbot import run_chatbot_query, extract_doctor_name, extract_day, book_appointment

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
    37+ years of excellence in healthcare with modern facilities.
    """)

with st.sidebar.expander("🩺 Specialities"):
    specialities = [
        "Cardiologist", "ENT", "Gastroenterologist", "Gynecologist", 
        "Nephrologist", "Neurologist", "Urologist", "Pulmonologist",
        "Dermatologist", "Ophthalmologist", "Orthopaedician", "Oncologist",
        "Pathologist", "Radiologist", "Psychiatrist", "Psychologist",
        "Endocrinologist", "General Surgeon", "Paediatrician"
    ]
    for spec in specialities:
        st.markdown(f"- {spec}")

with st.sidebar.expander("📍 Location"):
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram,  
    Kerala – 695002
    """)

# Contact Numbers
st.sidebar.subheader("📅 Appointment Booking")
appointment_numbers = ["+91 9876543210", "+91 9678547645", "+91 9234765840"]
for num in appointment_numbers:
    st.sidebar.markdown(f"[📞 Call {num}](tel:{num.replace(' ', '')})")

st.sidebar.subheader("🚨 Emergency Numbers")
emergency_numbers = ["+91 9678768843", "+91 9568746574"]
for num in emergency_numbers:
    st.sidebar.markdown(f"⚠️ **{num}**")

st.sidebar.subheader("📞 General Contact Numbers")
general_numbers = ["+91 9448123456", "+91 9448234567"]
for num in general_numbers:
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
# APPOINTMENTS CSV
# ===============================
APPOINTMENTS_FILE = "appointments.csv"
try:
    appointments_df = pd.read_csv(APPOINTMENTS_FILE)
except FileNotFoundError:
    appointments_df = pd.DataFrame(columns=["Doctor Name", "Patient Name", "Day", "Time"])

# ===============================
# CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'''
                <div style="
                    text-align: right;
                    background-color: #DCF8C6;
                    padding: 10px;
                    border-radius: 10px;
                    margin: 5px;
                    display: inline-block;
                ">{msg["content"]}</div>
            ''', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'''
                <div style="
                    text-align: left;
                    background-color: #F1F0F0;
                    padding: 10px;
                    border-radius: 10px;
                    margin: 5px;
                    display: inline-block;
                    white-space: pre-line;
                ">{msg["content"]}</div>
            ''', unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, timings, availability, or book an appointment…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    booking = st.session_state.booking
    reply = ""

    # ---------- BOOK APPOINTMENT ----------
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)
        if not doctor:
            reply = "👨⚕️ Please specify the doctor's name to book an appointment."
        else:
            booking.update({"active": True, "doctor": doctor, "day": day})
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "⏰ Enter preferred time (example: **10am**)."

    elif booking["active"] and not booking["time"]:
        try:
            selected_time = datetime.strptime(user_input.strip().lower(), "%I%p").time()

            # Prevent past times if day is today
            booking_day = booking["day"] or datetime.now().strftime("%A")
            if booking_day == datetime.now().strftime("%A") and selected_time < datetime.now().time():
                reply = "⛔ Cannot book a past time."
            else:
                # Check max 20 appointments per doctor per day
                daily_appointments = appointments_df[
                    (appointments_df["Doctor Name"] == booking["doctor"]) &
                    (appointments_df["Day"] == booking_day)
                ]
                if len(daily_appointments) >= 20:
                    reply = "⚠️ Maximum 20 appointments reached for this doctor on this day."
                else:
                    booking["time"] = user_input.strip()
                    # Log appointment to CSV
                    new_entry = pd.DataFrame([{
                        "Doctor Name": booking["doctor"],
                        "Patient Name": booking["patient"],
                        "Day": booking_day,
                        "Time": booking["time"]
                    }])
                    appointments_df = pd.concat([appointments_df, new_entry], ignore_index=True)
                    appointments_df.to_csv(APPOINTMENTS_FILE, index=False)
                    reply = f"✅ Appointment confirmed with **{booking['doctor']}** on **{booking_day}** at **{booking['time']}**."
                    # Reset booking
                    st.session_state.booking = {"active": False, "doctor": None, "day": None, "patient": None, "time": None}

        except ValueError:
            reply = "❌ Invalid time format. Use example: 10am"

    # ---------- NORMAL CHAT ----------
    else:
        reply = run_chatbot_query(user_input)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.experimental_rerun()
