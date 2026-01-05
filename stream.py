import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import os

# ===============================
# FILE SETUP
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPOINTMENTS_FILE = os.path.join(BASE_DIR, "appointments.csv")

if not os.path.exists(APPOINTMENTS_FILE):
    pd.DataFrame(
        columns=[
            "Doctor Name",
            "Patient Name",
            "Phone",
            "Date",
            "Time",
            "Reminder Sent"
        ]
    ).to_csv(APPOINTMENTS_FILE, index=False)

# ===============================
# IMPORT CHATBOT & DOCTORS DATA
# ===============================
from chatbot import run_chatbot_query, df, availability_on_day_for_specialty

# Ensure all required columns exist
required_cols = ["Doctor Name", "Speciality", "Professional Degree", "Consultation Time",
                 "Available days", "Contact", "Email", "Location"]
for col in required_cols:
    if col not in df.columns:
        df[col] = "N/A"
    df[col] = df[col].astype(str).str.strip()

# ===============================
# ADMIN AUTH
# ===============================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ===============================
# MOCK SMS
# ===============================
def send_mock_sms(phone, message):
    st.info(f"📩 SMS sent to **{phone}**\n\n{message}")

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Assistant",
    page_icon="🏥",
    layout="wide"
)

# ===============================
# HEADER
# ===============================
st.markdown("""
<h1 style="text-align:center;
background:#0f172a;
color:white;
padding:15px;
border-radius:12px;">
🏥 PRS Hospital Assistant
</h1>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR (NO PATIENT DETAILS)
# ===============================
st.sidebar.title("📌 PRS Hospital")

# Admin Login
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Admin Login")
username = st.sidebar.text_input("Username", key="admin_user")
password = st.sidebar.text_input("Password", type="password", key="admin_pass")
if st.sidebar.button("Login"):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.sidebar.success("Admin logged in")
    else:
        st.sidebar.error("Invalid credentials")
if st.session_state.is_admin:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"is_admin": False}))

# Additional Sidebar Info
with st.sidebar.expander("🩺 Specialities", expanded=False):
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

with st.sidebar.expander("📅 Book Appointment Contacts", expanded=True):
    appointment_numbers = [
        "+91 9876543210",
        "+91 9678547645",
        "+91 9234765840"
    ]
    for num in appointment_numbers:
        st.markdown(f"📞 {num}")
        st.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

with st.sidebar.expander("🚨 Emergency Numbers", expanded=False):
    emergency_numbers = ["+91 9678768843", "+91 9568746574"]
    for num in emergency_numbers:
        st.markdown(f"⚠️ **{num}**")

with st.sidebar.expander("📞 General Contact Numbers", expanded=False):
    general_numbers = ["+91 9448123456", "+91 9448234567"]
    for num in general_numbers:
        st.markdown(f"📱 {num}")

# ===============================
# MAIN MENU
# ===============================
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "ℹ️ About"]
)

# ===============================
# ABOUT PAGE
# ===============================
if menu == "ℹ️ About":
    st.markdown("""
    ### 🏥 About PRS Hospital  
    ✔ Multi-specialty hospital  
    ✔ Consultation: 9 AM – 6 PM  
    ✔ Online appointment booking  
    """)

# ===============================
# CHATBOT PAGE
# ===============================
elif menu == "💬 Chatbot":
    st.subheader("💬 Ask the Hospital Assistant")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Type your question here")
    if st.button("Send") and user_input.strip():
        reply = run_chatbot_query(user_input)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", reply))

    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role}:** {msg}")

# ===============================
# BOOK APPOINTMENT PAGE (PATIENT INPUT INSIDE PAGE)
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    # Patient Details inside booking page
    patient_name = st.text_input("Patient Name")
    phone = st.text_input("Phone Number")

    today = datetime.now().date()
    selected_date = st.date_input("📆 Select Date", min_value=today, max_value=today + timedelta(days=7))
    selected_time = st.time_input("⏰ Select Time", time(9, 0))

    # Default doctor (first in df)
    selected_doctor_name = df.iloc[0]["Doctor Name"]

    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Please enter patient name")
            st.stop()
        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter a valid 10-digit phone number")
            st.stop()

        # Check doctor availability
        doc_row = df[df["Doctor Name"] == selected_doctor_name].iloc[0]
        raw_days = doc_row["Available days"].lower()
        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        day_name = selected_date.strftime("%A").lower()

        allowed_days = []
        for x in raw_days.split(","):
            x = x.strip()
            for d in days:
                if d.startswith(x[:3]):
                    allowed_days.append(d)

        ok = day_name in allowed_days or any(k in raw_days for k in ["all","everyday","daily"])
        if not ok:
            st.error(f"❌ {selected_doctor_name} is not available on {selected_date.strftime('%A')}")
            st.stop()

        # Prevent past date/time
        if selected_date < today or (selected_date == today and selected_time <= datetime.now().time()):
            st.error("❌ Cannot book past date or time")
            st.stop()

        # Load appointments CSV
        appt_df = pd.read_csv(APPOINTMENTS_FILE, parse_dates=["Date"])

        # Max 20 appointments per doctor per day
        if appt_df[(appt_df["Doctor Name"] == selected_doctor_name) & 
                   (appt_df["Date"].dt.date == selected_date)].shape[0] >= 20:
            st.error("❌ Slots full for this doctor on selected day")
            st.stop()

        # Save appointment
        new_appt = {
            "Doctor Name": selected_doctor_name,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": selected_date,
            "Time": selected_time.strftime("%I:%M %p"),
            "Reminder Sent": False
        }
        appt_df = pd.concat([appt_df, pd.DataFrame([new_appt])], ignore_index=True)
        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        # Mock SMS
        send_mock_sms(phone, f"Appointment confirmed with {selected_doctor_name} on {selected_date.strftime('%A, %d %b')} at {selected_time.strftime('%I:%M %p')}")
        st.success(f"✅ Appointment booked successfully with {selected_doctor_name} on {selected_date.strftime('%A, %d %B')} at {selected_time.strftime('%I:%M %p')}")

# ===============================
# AUTOMATIC REMINDERS
# ===============================
appt_df = pd.read_csv(APPOINTMENTS_FILE, parse_dates=["Date"])
tomorrow = (datetime.now() + timedelta(days=1)).date()
reminders_sent = False
for idx, row in appt_df.iterrows():
    appt_date = row["Date"].date()
    if appt_date == tomorrow and not row["Reminder Sent"]:
        send_mock_sms(row["Phone"], f"Reminder: Appointment with {row['Doctor Name']} tomorrow at {row['Time']}")
        appt_df.at[idx, "Reminder Sent"] = True
        reminders_sent = True

if reminders_sent:
    appt_df.to_csv(APPOINTMENTS_FILE, index=False)

# ===============================
# ADMIN VIEW
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))
