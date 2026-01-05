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
from chatbot import run_chatbot_query, df

# Strip whitespace and ensure all columns exist
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
# SIDEBAR
# ===============================
st.sidebar.title("📌 PRS Hospital")

# Patient Info in Sidebar
st.sidebar.subheader("👤 Patient Details")
patient_name = st.sidebar.text_input("Patient Name")
phone = st.sidebar.text_input("Phone Number")

# ===============================
# DOCTOR SELECTION IN SIDEBAR
# ===============================
st.sidebar.subheader("👨‍⚕️ Select Doctor")
selected_doctor_name = st.sidebar.selectbox("Choose Doctor", sorted(df["Doctor Name"].unique()))

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

# ===============================
# MAIN MENU
# ===============================
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "👨‍⚕️ Doctors", "ℹ️ About"]
)

# ===============================
# ABOUT
# ===============================
if menu == "ℹ️ About":
    st.markdown("""
    ### 🏥 About PRS Hospital  
    ✔ Multi-specialty hospital  
    ✔ Consultation: 9 AM – 6 PM  
    ✔ Online appointment booking  
    """)

# ===============================
# DOCTORS PAGE
# ===============================
elif menu == "👨‍⚕️ Doctors":
    st.subheader("👨‍⚕️ Doctor Details")

    # Ensure selected doctor exists
    doc_row = df[df["Doctor Name"] == selected_doctor_name]

    if not doc_row.empty:
        doc_row = doc_row.iloc[0]  # safe to get first row

        st.markdown(f"""
        <div style="background:#f8fafc;
        padding:20px;
        margin-bottom:15px;
        border-left:5px solid #2563eb;
        border-radius:12px;
        box-shadow: 1px 1px 5px #ccc;">
        <h3>👨‍⚕️ {doc_row['Doctor Name']}</h3>
        <b>Speciality:</b> {doc_row['Speciality']}<br>
        <b>Degree:</b> {doc_row.get('Professional Degree', 'N/A')}<br>
        <b>Consultation Time:</b> {doc_row.get('Consultation Time', 'N/A')}<br>
        <b>Available Days:</b> {doc_row.get('Available days', 'N/A')}<br>
        <b>Phone:</b> {doc_row.get('Contact', 'N/A')}<br>
        <b>Email:</b> {doc_row.get('Email', 'N/A')}<br>
        <b>Location:</b> {doc_row.get('Location', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Doctor details not found. Please check the name in the CSV.")


# ===============================
# CHATBOT
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
# BOOK APPOINTMENT
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    today = datetime.now().date()
    selected_date = st.date_input("📆 Select Date", min_value=today, max_value=today + timedelta(days=7))
    selected_time = st.time_input("⏰ Select Time", time(9, 0))

    if st.button("✅ Confirm Appointment"):
        # Validate patient info
        if not patient_name.strip():
            st.error("❌ Please enter patient name")
            st.stop()
        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter a valid 10-digit phone number")
            st.stop()

        # Check doctor availability
        doc_row = df[df["Doctor Name"] == selected_doctor_name].iloc[0]
        raw = doc_row["Available days"].lower()
        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        day_name = selected_date.strftime("%A").lower()

        allowed_days = []
        for x in raw.split(","):
            x = x.strip()
            for d in days:
                if d.startswith(x[:3]):
                    allowed_days.append(d)
        if any(keyword in raw for keyword in ["all", "everyday", "daily"]):
            ok = True
        else:
            ok = day_name in allowed_days

        if not ok:
            st.error(f"❌ {selected_doctor_name} is not available on {selected_date.strftime('%A')}")
            st.stop()

        # Prevent past date/time
        if selected_date < today or (selected_date == today and selected_time <= datetime.now().time()):
            st.error("❌ Cannot book past date or time")
            st.stop()

        # Load appointments CSV
        appt_df = pd.read_csv(APPOINTMENTS_FILE)

        # Max 20 appointments per doctor per day
        if appt_df[(appt_df["Doctor Name"] == selected_doctor_name) & (appt_df["Date"] == selected_date.isoformat())].shape[0] >= 20:
            st.error("❌ Slots full for this doctor on selected day")
            st.stop()

        # Save appointment
        appt_df.loc[len(appt_df)] = {
            "Doctor Name": selected_doctor_name,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": selected_date.isoformat(),
            "Time": selected_time.strftime("%I:%M%p"),
            "Reminder Sent": False
        }
        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        # Mock SMS
        send_mock_sms(phone, f"Appointment confirmed with {selected_doctor_name} on {selected_date.strftime('%A, %d %b')} at {selected_time.strftime('%I:%M%p')}")
        st.success(f"✅ Appointment booked successfully with {selected_doctor_name} on {selected_date.strftime('%A, %d %B')} at {selected_time.strftime('%I:%M%p')}")

# ===============================
# AUTOMATIC REMINDERS
# ===============================
appt_df = pd.read_csv(APPOINTMENTS_FILE)
tomorrow = (datetime.now() + timedelta(days=1)).date()
reminders_sent = False
for idx, row in appt_df.iterrows():
    appt_date = datetime.fromisoformat(row["Date"]).date()
    if appt_date == tomorrow and not row["Reminder Sent"]:
        send_mock_sms(row["Phone"], f"Reminder: Appointment with {row['Doctor Name']} tomorrow at {row['Time']}")
        appt_df.at[idx, "Reminder Sent"] = True
        reminders_sent = True

if reminders_sent:
    appt_df.to_csv(APPOINTMENTS_FILE, index=False)

# ===============================
# ADMIN VIEW
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))

