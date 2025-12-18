# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day
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
# STICKY HEADER
# ===============================
st.markdown("""
<style>
.header {
    position: fixed;
    top: 0;
    width: 100%;
    background: white;
    z-index: 999;
    padding: 10px;
    border-bottom: 1px solid #ddd;
    text-align: center;
    font-size: 26px;
    font-weight: bold;
    color: #084298;
}
.content {
    margin-top: 80px;
}
</style>

<div class="header">🏥 PRS Hospital – Chatbot Assistant</div>
<div class="content"></div>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("🏥 PRS Hospital")

    st.markdown("### ℹ️ About")
    st.write(
        "PRS Hospital, Thiruvananthapuram, has over 37 years of excellence "
        "in multi-specialty healthcare and advanced medical services."
    )

    st.markdown("### 🩺 Specialities")
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

    st.markdown("### 📍 Location")
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram, Kerala – 695002
    """)

    st.markdown("### 📞 Appointment Booking")
    st.markdown("📞 +91 98765 43210")
    st.markdown("📞 +91 96785 47645")
    st.markdown("[📲 Call Hospital](tel:+919876543210)")

    st.markdown("### ☎️ Emergency")
    st.markdown("🚨 **+91 95687 46574**")

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "step": None,
        "doctor": None,
        "patient": None,
        "date": None,
        "time": None
    }

# ===============================
# APPOINTMENT STORAGE
# ===============================
APPT_FILE = "appointments.csv"
MAX_SLOTS_PER_DOCTOR = 5

if not pd.io.common.file_exists(APPT_FILE):
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Day", "Time"]
    ).to_csv(APPT_FILE, index=False)

# ===============================
# SAVE APPOINTMENT WITH VALIDATION
# ===============================
def save_appointment(doc, patient, d, t):
    hospital_df = pd.read_csv("Hospital_Information124.csv")  # Doctor info
    appt_df = pd.read_csv(APPT_FILE)

    # Doctor exists?
    doctor_row = hospital_df[hospital_df["Doctor Name"].str.lower() == doc.lower()]
    if doctor_row.empty:
        return f"❌ Doctor **{doc}** not found."
    doctor_row = doctor_row.iloc[0]

    # Check day availability
    day_name = d.strftime("%A").lower()
    available_days = doctor_row["Available days"].lower()
    if available_days != "all days" and day_name not in available_days:
        return f"❌ {doc} is NOT available on {day_name.capitalize()}."

    # Check time within consultation
    consult_time = doctor_row["Consultation Time"]  # "9AM-5PM"
    start, end = consult_time.split("-")
    start_t = datetime.strptime(start.strip(), "%I%p").time()
    end_t = datetime.strptime(end.strip(), "%I%p").time()
    if not start_t <= t <= end_t:
        return f"❌ {doc} is available between {consult_time}. Please choose a valid time."

    # Max slots
    slots = appt_df[(appt_df["Doctor Name"] == doc) & (appt_df["Day"] == str(d))]
    if len(slots) >= MAX_SLOTS_PER_DOCTOR:
        return f"⛔ Slot full for **{doc}** on **{d}**."

    # Save appointment
    appt_df.loc[len(appt_df)] = [doc, patient, str(d), t.strftime("%I:%M %p")]
    appt_df.to_csv(APPT_FILE, index=False)

    return (
        f"✅ **Appointment Confirmed**\n\n"
        f"👨‍⚕️ Doctor: **{doc}**\n"
        f"👤 Patient: **{patient}**\n"
        f"📅 Date: **{d}**\n"
        f"⏰ Time: **{t.strftime('%I:%M %p')}**"
    )

# ===============================
# DISPLAY CHAT
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input(
    "Ask about doctors, availability, degree, location, or book appointment"
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    booking = st.session_state.booking
    reply = None

    # Booking flow
    if booking["step"] is not None:
        if booking["step"] == "patient":
            booking["patient"] = user_input.strip()
            booking["step"] = "date"
            reply = "📆 Please select appointment date below."
        else:
            reply = "⚠️ Please complete the appointment booking steps below."

    elif "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "Please mention the doctor name to book an appointment."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    else:
        # Use chatbot response (lists doctors line by line)
        reply = run_chatbot_query(user_input)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ===============================
# CALENDAR & TIME PICKER
# ===============================
booking = st.session_state.booking

if booking["step"] == "date":
    selected_date = st.date_input("Select Appointment Date", min_value=date.today())
    if st.button("Confirm Date"):
        booking["date"] = selected_date
        booking["step"] = "time"
        st.rerun()

if booking["step"] == "time":
    selected_time = st.time_input("Select Time", value=time(9, 0))
    if st.button("Confirm Time"):
        combined = datetime.combine(booking["date"], selected_time)
        if combined < datetime.now():
            st.error("⛔ Cannot book past time.")
        elif not time(9, 0) <= selected_time <= time(20, 0):
            st.error("⛔ Appointments allowed only between 9 AM and 8 PM.")
        else:
            result = save_appointment(
                booking["doctor"],
                booking["patient"],
                booking["date"],
                selected_time
            )
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.session_state.booking = {"step": None, "doctor": None, "patient": None, "date": None, "time": None}
            st.rerun()
