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

df["Doctor Name"] = df["Doctor Name"].str.strip()
df["Speciality"] = df["Speciality"].str.strip()
df["Available days"] = df["Available days"].str.strip()

# ===============================
# ADMIN AUTH
# ===============================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ===============================
# MOCK SMS (UI VISIBLE)
# ===============================
def send_mock_sms(phone, message):
    st.info(f"📩 SMS sent to **{phone}**\n\n{message}")

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
# SIDEBAR MENU
# ===============================
st.sidebar.title("📌 PRS Hospital")
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "👨‍⚕️ Doctors", "ℹ️ About"]
)

# ===============================
# SPECIALITY FILTER (FIXED)
# ===============================
specialities = df["Speciality"].dropna().unique()
selected_spec = st.sidebar.selectbox(
    "🩺 Filter by Speciality",
    ["All"] + sorted(specialities)
)

# ===============================
# ADMIN LOGIN
# ===============================
st.sidebar.markdown("---")
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
    display_df = df if selected_spec == "All" else df[df["Speciality"].str.lower() == selected_spec.lower()]

    for _, r in display_df.iterrows():
        st.markdown(f"""
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
        """, unsafe_allow_html=True)

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
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", reply))

    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role}:** {msg}", unsafe_allow_html=True)

# ===============================
# BOOK APPOINTMENT
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")

    doctors_df = df if selected_spec == "All" else df[df["Speciality"].str.lower() == selected_spec.lower()]
    doctor = st.selectbox("👨‍⚕️ Select Doctor", sorted(doctors_df["Doctor Name"].unique()))

    today = datetime.now().date()
    selected_date = st.date_input("📆 Select Date", min_value=today, max_value=today + timedelta(days=7))

    selected_time = st.time_input("⏰ Select Time", time(9, 0))

    # Time range check
    if not time(9, 0) <= selected_time <= time(18, 0):
        st.error("❌ Time must be between 9 AM and 6 PM")
        st.stop()

    # Past time check
    now = datetime.now()
    if selected_date == now.date() and selected_time <= now.time():
        st.error("❌ Cannot book past time today")
        st.stop()

    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Enter patient name")
            st.stop()

        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter valid 10-digit phone number")
            st.stop()

        doc_row = df[df["Doctor Name"] == doctor].iloc[0]
        raw = doc_row["Available days"].lower().replace(" ", "")
        day_name = selected_date.strftime("%A").lower()

        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

        if any(x in raw for x in ["all", "everyday", "daily"]):
            ok = True
        elif "-" in raw:
            s, e = raw.split("-")
            s = next(d for d in days if d.startswith(s[:3]))
            e = next(d for d in days if d.startswith(e[:3]))
            ok = days.index(s) <= days.index(day_name) <= days.index(e)
        else:
            allowed_days = []

            for x in raw.split(","):
                x = x.strip().lower()
                for d in days:
                    if d.startswith(x[:3]):
                        allowed_days.append(d)

ok = day_name in allowed_days


        if not ok:
            st.error(f"❌ {doctor} not available on {selected_date.strftime('%A')}")
            st.stop()

        appt_df = pd.read_csv(APPOINTMENTS_FILE)

        if appt_df[(appt_df["Doctor Name"] == doctor) & (appt_df["Date"] == selected_date.isoformat())].shape[0] >= 20:
            st.error("❌ Slots full for this doctor on this day")
            st.stop()

        appt_df.loc[len(appt_df)] = {
            "Doctor Name": doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": selected_date.isoformat(),
            "Time": selected_time.strftime("%I:%M%p"),
            "Reminder Sent": False
        }

        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        send_mock_sms(phone, f"Appointment confirmed with {doctor} on {selected_date} at {selected_time.strftime('%I:%M%p')}")
        st.success("✅ Appointment booked successfully")

# ===============================
# ADMIN VIEW
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))

