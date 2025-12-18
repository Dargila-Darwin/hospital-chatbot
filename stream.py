import streamlit as st
from datetime import datetime, date, time
from collections import defaultdict
import pandas as pd
import csv
import os
from chatbot import run_chatbot_query, extract_doctor_name

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# HEADER
# ===============================
st.markdown(
    """
    <h1 style="text-align:center; color:#084298; margin-bottom:0;">
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
    37+ years of excellence in healthcare.
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
    Killipalam,  
    Thiruvananthapuram,  
    Kerala – 695002
    """)

st.sidebar.subheader("📞 Appointment Booking")
st.sidebar.markdown("📞 +91 9876543210")
st.sidebar.markdown("📞 +91 9678547645")

st.sidebar.subheader("🚨 Emergency")
st.sidebar.markdown("⚠️ **+91 9568746574**")

# ===============================
# CSV FILES
# ===============================
APPOINTMENT_FILE = "appointment.csv"
DOCTOR_SCHEDULE_FILE = "doctor_schedule.csv"
CSV_HEADERS = ["Doctor Name", "Patient Name", "Day", "Time"]

# Create appointment file if not exists
if not os.path.exists(APPOINTMENT_FILE):
    with open(APPOINTMENT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)

# ===============================
# LOAD DOCTOR SCHEDULE
# ===============================
if os.path.exists(DOCTOR_SCHEDULE_FILE):
    df_schedule = pd.read_csv(DOCTOR_SCHEDULE_FILE)
    DOCTOR_SCHEDULE = {}
    for _, row in df_schedule.iterrows():
        days = [d.strip() for d in row["Days Available"].split(",")]
        start_h, start_m = map(int, row["Start Time"].split(":"))
        end_h, end_m = map(int, row["End Time"].split(":"))
        DOCTOR_SCHEDULE[row["Doctor Name"]] = {
            "days": days,
            "start": time(start_h, start_m),
            "end": time(end_h, end_m)
        }
else:
    st.error("Doctor schedule file not found! Please create 'doctor_schedule.csv'.")
    st.stop()

# ===============================
# HELPER FUNCTIONS
# ===============================
def doctor_available(doctor, selected_date, selected_time):
    schedule = DOCTOR_SCHEDULE.get(doctor)
    if not schedule:
        return False, f"{doctor} schedule not found."
    weekday = selected_date.strftime("%A")
    if weekday not in schedule["days"]:
        return False, f"{doctor} is not available on {weekday}."
    if not (schedule["start"] <= selected_time <= schedule["end"]):
        return False, f"{doctor} is available only between {schedule['start'].strftime('%I:%M %p')} and {schedule['end'].strftime('%I:%M %p')}."
    return True, None

def save_appointment(doctor, patient, selected_date, selected_time):
    with open(APPOINTMENT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([doctor, patient, selected_date.strftime("%A"), selected_time.strftime("%I:%M %p")])

def format_doctors_line_by_line(response):
    lines = [f"👨‍⚕️ {d.strip()}" for d in response.replace("•","\n").split("\n") if d.strip()]
    return "\n".join(lines)

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "active": False,
        "doctor": None,
        "patient": None
    }

if "booking_count" not in st.session_state:
    st.session_state.booking_count = defaultdict(lambda: defaultdict(int))

# ===============================
# CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<div style='white-space:pre-line'>{msg['content']}</div>", unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, availability, or book appointment…")

# ===============================
# CHAT LOGIC
# ===============================
if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})
    booking = st.session_state.booking
    reply = ""

    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "👨‍⚕️ Please mention the doctor's name."
        elif doctor not in DOCTOR_SCHEDULE:
            reply = f"❌ {doctor} schedule not found."
        else:
            booking["active"] = True
            booking["doctor"] = doctor
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "📅 Please select appointment date and time below."

    else:
        response = run_chatbot_query(user_input)
        reply = format_doctors_line_by_line(response)

    st.session_state.messages.append({"role":"assistant","content":reply})
    st.rerun()

# ===============================
# BOOKING UI
# ===============================
booking = st.session_state.booking
if booking["active"] and booking["patient"]:
    selected_date = st.date_input("📅 Appointment Date", min_value=date.today())
    selected_time = st.time_input("⏰ Appointment Time", value=time(10,0))

    if st.button("✅ Confirm Appointment"):
        weekday = selected_date.strftime("%A")
        if not (time(9,0) <= selected_time <= time(20,0)):
            st.error("⛔ Appointments allowed only between 9 AM and 8 PM.")
        elif selected_date == date.today() and selected_time <= datetime.now().time():
            st.error("⛔ Cannot book a past time.")
        else:
            ok, err = doctor_available(booking["doctor"], selected_date, selected_time)
            if not ok:
                st.error(f"❌ {err}")
            elif st.session_state.booking_count[booking["doctor"]][selected_date] >= 20:
                st.error("❌ All 20 slots are full for this doctor today.")
            else:
                st.session_state.booking_count[booking["doctor"]][selected_date] += 1
                save_appointment(booking["doctor"], booking["patient"], selected_date, selected_time)
                st.success(f"""
✅ **Appointment Confirmed**

👨‍⚕️ Doctor: {booking['doctor']}
👤 Patient: {booking['patient']}
📅 Day: {selected_date.strftime('%A')}
⏰ Time: {selected_time.strftime('%I:%M %p')}
""")
                st.session_state.booking = {"active":False,"doctor":None,"patient":None}
