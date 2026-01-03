import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import os

# ===============================
# FILE SETUP
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPOINTMENTS_FILE = os.path.join(BASE_DIR, "appointments.csv")

# Fix old CSV
if os.path.exists(APPOINTMENTS_FILE):
    df_old = pd.read_csv(APPOINTMENTS_FILE)
    if "Day" in df_old.columns:
        df_old.rename(columns={"Day": "Date"}, inplace=True)
    if "Reminder Sent" not in df_old.columns:
        df_old["Reminder Sent"] = False
    df_old.to_csv(APPOINTMENTS_FILE, index=False)

# Create CSV if not exists
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
# IMPORT CHATBOT
# ===============================
from chatbot import (
    run_chatbot_query,
    df
)

# ===============================
# ADMIN AUTH
# ===============================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ===============================
# MOCK SMS FUNCTION
# ===============================
def send_mock_sms(phone, message):
    print("📱 SMS SENT")
    print(f"To: {phone}")
    print(f"Message: {message}")

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Assistant",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# HEADER
# ===============================
st.markdown(
    """
    <h1 style="text-align:center;
    background:#0f172a;
    color:white;
    padding:15px;
    border-radius:12px;">
    🏥 PRS Hospital Assistant Chatbot
    </h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# SIDEBAR MENU
# ===============================
st.sidebar.title("📌 PRS Hospital")
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "👨‍⚕️ Doctors", "ℹ️ About"]
)

# ===============================
# ADMIN LOGIN
# ===============================
st.sidebar.markdown("## 🔐 Admin Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.sidebar.success("Admin logged in")
    else:
        st.sidebar.error("Invalid credentials")

if st.session_state.is_admin:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"is_admin": False}))

# ===============================
# SIDEBAR INFO
# ===============================
with st.sidebar.expander("🏥 Hospital Info", expanded=True):
    st.markdown("""
    **PRS Hospital**  
    Thiruvananthapuram, Kerala
    """)

with st.sidebar.expander("📞 Emergency", expanded=False):
    st.markdown("🚨 +91 9678768843")

# ===============================
# Sidebar Specialities (Clickable)
# ===============================
with st.sidebar.expander("🩺 Specialities", expanded=False):
    specialities = df["Speciality"].unique()
    selected_spec = st.selectbox("Choose Speciality", ["All"] + sorted(specialities))

# ===============================
# ABOUT
# ===============================
if menu == "ℹ️ About":
    st.markdown("""
    ### 🏥 About PRS Hospital  
    ✔ Multi-specialty hospital  
    ✔ Consultation: 9 AM – 6 PM  
    ✔ Easy online appointment booking  
    """)

# ===============================
# DOCTORS
# ===============================
elif menu == "👨‍⚕️ Doctors":
    display_df = df.copy()
    if selected_spec != "All":
        display_df = display_df[df["Speciality"] == selected_spec]

    for _, r in display_df.iterrows():
        st.markdown(
            f"""
            <div style="background:#f8fafc;
            padding:15px;
            margin-bottom:10px;
            border-left:5px solid #2563eb;
            border-radius:10px;">
            <b>👨‍⚕️ {r['Doctor Name']}</b><br>
            🩺 {r['Speciality']}<br>
            ⏰ {r['Consultation Time']}<br>
            📅 {r['Available days']}<br>
            📍 {r['Location']}
            </div>
            """,
            unsafe_allow_html=True
        )

# ===============================
# CHATBOT
# ===============================
elif menu == "💬 Chatbot":
    st.subheader("💬 Ask the Hospital Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Type your question")

    if st.button("Send") and user_input.strip():
        reply = run_chatbot_query(user_input)
        reply = reply.replace("\n", "<br>")
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", reply))

    for role, msg in st.session_state.chat_history:
        if role == "You":
            st.markdown(f"🧑 **You:** {msg}")
        else:
            st.markdown(f"🤖 **Bot:** {msg}", unsafe_allow_html=True)

# ===============================
# BOOK APPOINTMENT
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")

    doctor = st.selectbox(
        "👨‍⚕️ Select Doctor",
        sorted(df["Doctor Name"].unique())
    )

    today = datetime.now().date()
    date = st.date_input(
        "📆 Select Date",
        min_value=today,
        max_value=today + timedelta(days=7)
    )

    day = date.strftime("%A").lower()
    START_TIME = time(9, 0)
    END_TIME = time(18, 0)

    selected_time = st.time_input("⏰ Select Time", value=START_TIME)

    if not (START_TIME <= selected_time <= END_TIME):
        st.error("❌ Time must be between 9 AM and 6 PM")
        st.stop()

    time_str = selected_time.strftime("%I:%M%p").lstrip("0")

    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Enter patient name")
            st.stop()

        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter valid 10-digit phone number")
            st.stop()

        now = datetime.now()
        if date == now.date() and selected_time <= now.time():
            st.error("❌ Cannot book past time")
            st.stop()

        appt_df = pd.read_csv(APPOINTMENTS_FILE)

        # Doctor availability
        doc_row = df[df["Doctor Name"] == doctor].iloc[0]
        if day not in doc_row["Available days"].lower():
            st.error(f"❌ {doctor} not available on {date.strftime('%A')}")
            st.stop()

        # Slot limit
        count = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat())
        ].shape[0]
        if count >= 20:
            st.error("❌ Slots full for this doctor")
            st.stop()

        # Save appointment
        appt_df.loc[len(appt_df)] = {
            "Doctor Name": doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": date.isoformat(),
            "Time": time_str,
            "Reminder Sent": False
        }
        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        # Mock confirmation SMS
        sms_message = f"PRS Hospital: Appointment confirmed with {doctor} on {date.strftime('%d %b')} at {time_str}."
        send_mock_sms(phone, sms_message)
        st.success(f"✅ Appointment confirmed with {doctor} on {date.strftime('%d %B')} at {time_str}")
        st.info("📩 Confirmation SMS sent to patient")

# ===============================
# ADMIN DASHBOARD
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("## 📊 Admin Dashboard")
    appt_df = pd.read_csv(APPOINTMENTS_FILE)

    if not appt_df.empty:
        # Convert to datetime
        appt_df["Date"] = pd.to_datetime(appt_df["Date"])

        # Daily appointment count
        today = datetime.now().date()
        today_count = appt_df[appt_df["Date"].dt.date == today].shape[0]
        st.sidebar.metric("📅 Today's Appointments", today_count)

        # Doctor-wise filter
        doctors = ["All"] + sorted(appt_df["Doctor Name"].unique())
        selected_doc = st.sidebar.selectbox("👨‍⚕️ Filter by Doctor", doctors)
        if selected_doc != "All":
            appt_df = appt_df[appt_df["Doctor Name"] == selected_doc]

        st.sidebar.dataframe(appt_df)

        # 1-hour reminder simulation
        now = datetime.now()
        for idx, row in appt_df.iterrows():
            if row["Reminder Sent"]:
                continue
            appt_datetime = datetime.strptime(f"{row['Date'].date()} {row['Time']}", "%Y-%m-%d %I:%M%p")
            diff_minutes = (appt_datetime - now).total_seconds() / 60
            if 0 < diff_minutes <= 60:
                reminder_msg = f"PRS Hospital Reminder: You have an appointment with {row['Doctor Name']} at {row['Time']} today."
                send_mock_sms(row["Phone"], reminder_msg)
                appt_df.at[idx, "Reminder Sent"] = True
        appt_df.to_csv(APPOINTMENTS_FILE, index=False)
        st.sidebar.success("⏰ Reminder check completed")
