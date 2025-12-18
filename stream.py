import streamlit as st
import pandas as pd
from datetime import datetime, time
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
    Killipalam,  
    Thiruvananthapuram,  
    Kerala – 695002
    """)

st.sidebar.subheader("📅 Appointment Booking")
appointment_numbers = ["+91 9876543210", "+91 9678547645", "+91 9234765840"]
for num in appointment_numbers:
    st.sidebar.markdown(f"📞 {num}")

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

APPOINTMENTS_FILE = "appointments.csv"
MAX_SLOTS_PER_DOCTOR = 20
# Initialize appointments file if not exists
if not pd.io.common.file_exists(APPOINTMENTS_FILE):
    pd.DataFrame(columns=["Doctor", "Patient", "Day", "Time"]).to_csv(APPOINTMENTS_FILE, index=False)

def get_available_slots(doctor, day):
    df = pd.read_csv(APPOINTMENTS_FILE)
    return MAX_SLOTS_PER_DOCTOR - len(df[(df["Doctor"] == doctor) & (df["Day"] == day)])

def save_appointment(doctor, patient, day, time_str):
    if get_available_slots(doctor, day) <= 0:
        return f"⛔ All 20 slots booked for {doctor} on {day}."
    df = pd.read_csv(APPOINTMENTS_FILE)
    df = pd.concat([df, pd.DataFrame([{
        "Doctor": doctor,
        "Patient": patient,
        "Day": day,
        "Time": time_str
    }])], ignore_index=True)
    df.to_csv(APPOINTMENTS_FILE, index=False)
    return f"✅ Appointment confirmed with **{doctor}** on **{day}** at **{time_str}**."

# ===============================
# CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'<div style="text-align:right;background-color:#DCF8C6;padding:10px;border-radius:10px;margin:5px;display:inline-block;">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'<div style="text-align:left;background-color:#F1F0F0;padding:10px;border-radius:10px;margin:5px;display:inline-block;white-space:pre-line;">{msg["content"]}</div>', unsafe_allow_html=True)

# ===============================
# INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, timings, availability, or book an appointment…")

def format_doctors_line_by_line(response):
    return "\n".join(f"• {line.strip()}" for line in response.split("\n") if line.strip())

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
            selected_time = datetime.strptime(user_input.strip(), "%I%p")
            if not time(9,0) <= selected_time.time() <= time(20,0):
                reply = "⛔ Appointments allowed only between 9 AM and 8 PM."
            else:
                day_name = booking["day"] or datetime.now().strftime("%A")
                available_slots = get_available_slots(booking["doctor"], day_name)
                if available_slots <= 0:
                    reply = f"⛔ Cannot book. All 20 slots for {booking['doctor']} on {day_name} are full."
                else:
                    booking["time"] = user_input.strip()
                    # Save appointment
                    reply = save_appointment(
                        booking["doctor"],
                        booking["patient"],
                        day_name,
                        booking["time"]
                    )
                    # reset booking
                    st.session_state.booking = {"active": False, "doctor": None, "day": None, "patient": None, "time": None}
        except:
            reply = "❌ Invalid format. Use example: 10am"

    # ---------- NORMAL CHAT ----------
    else:
        response = run_chatbot_query(user_input)
        reply = format_doctors_line_by_line(response)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
