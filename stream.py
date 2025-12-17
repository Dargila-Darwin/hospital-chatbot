# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import run_chatbot_query, extract_doctor_name, extract_day

st.set_page_config(page_title="PRS Hospital Chatbot", page_icon="🏥", layout="centered")

st.markdown("<h1 style='text-align:center; color:#084298;'>🏥 PRS Hospital – Chatbot Assistant</h1><hr>", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
st.sidebar.title("🏥 Hospital Dashboard")
st.sidebar.subheader("📅 Appointment Booking")
HOSPITAL_CONTACTS = ["+91 9876543210", "+91 9678547645"]
for num in HOSPITAL_CONTACTS:
    st.sidebar.markdown(f"📞 {num} - [Call](tel:{num.replace(' ', '')})")
st.sidebar.subheader("🚨 Emergency")
st.sidebar.markdown("⚠️ +91 9568746574")

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {"step": None, "doctor": None, "patient": None, "date": None, "time": None}

APPT_FILE = "appointments.csv"
MAX_PATIENTS_PER_DOCTOR = 20

if not pd.io.common.file_exists(APPT_FILE):
    pd.DataFrame(columns=["Doctor", "Patient", "Date", "Time"]).to_csv(APPT_FILE, index=False)

def save_appointment(doc, patient, d, t):
    df = pd.read_csv(APPT_FILE)
    slots = df[(df["Doctor"] == doc) & (df["Date"] == str(d))]
    if len(slots) >= MAX_PATIENTS_PER_DOCTOR:
        return f"⛔ Max patients reached for **{doc}** on {d}."
    df.loc[len(df)] = [doc, patient, str(d), t]
    df.to_csv(APPT_FILE, index=False)
    return f"✅ Appointment confirmed with **{doc}** on {d} at {t}."

# ---------------- Chat Display ----------------
for msg in st.session_state.messages:
    align = "right" if msg["role"] == "user" else "left"
    color = "#DCF8C6" if msg["role"] == "user" else "#F1F0F0"
    with st.chat_message(msg["role"]):
        st.markdown(f"<div style='text-align:{align}; background:{color}; padding:10px; border-radius:10px; display:inline-block; white-space:pre-line;'>{msg['content']}</div>", unsafe_allow_html=True)

# ---------------- User Input ----------------
user_input = st.chat_input("Ask about doctors, speciality, degree, location, or book appointment")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    booking = st.session_state.booking
    reply = ""

    if "book" in user_input.lower() and booking["step"] is None:
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "Please mention doctor name for booking."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📅 Booking appointment with **{doctor}**. Enter patient name."

    elif booking["step"] == "patient":
        booking["patient"] = user_input.strip()
        booking["step"] = "date"
        reply = "📆 Select appointment date."

    elif booking["step"] == "date":
        pass  # handled below

    elif booking["step"] == "time":
        pass  # handled below

    else:
        reply = run_chatbot_query(user_input)

    if reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ---------------- Calendar + Time ----------------
booking = st.session_state.booking

if booking["step"] == "date":
    d = st.date_input("Select date", min_value=date.today())
    if st.button("Confirm Date"):
        booking["date"] = d
        booking["step"] = "time"
        st.rerun()

if booking["step"] == "time":
    t = st.time_input("Select time", value=time(9,0))
    selected_dt = datetime.combine(booking["date"], t)
    now = datetime.now()

    # Validate time within doctor consultation hours
    doc_row = None
    if booking["doctor"]:
        doc_row = pd.read_csv("Hospital_Information124.csv")
        doc_row = doc_row[doc_row["Doctor Name"].str.lower() == booking["doctor"].lower()]
        if not doc_row.empty:
            times = doc_row.iloc[0]["Consultation Time"]
            start_str, end_str = times.split("to")
            start = datetime.strptime(start_str.strip(), "%I%p").time()
            end = datetime.strptime(end_str.strip(), "%I%p").time()
            if t < start or t > end:
                st.error(f"⛔ Doctor available only from {start_str} to {end_str}")
                st.stop()

    if st.button("Confirm Time"):
        if selected_dt < now:
            st.error("⛔ Cannot book past time.")
        else:
            result = save_appointment(booking["doctor"], booking["patient"], booking["date"], t.strftime("%I:%M%p"))
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.session_state.booking = {"step": None, "doctor": None, "patient": None, "date": None, "time": None}
            st.rerun()
