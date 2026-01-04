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
# IMPORT CHATBOT & DOCTORS DF
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
st.markdown("""
<h1 style="text-align:center;background:#0f172a;color:white;padding:15px;border-radius:12px;">
🏥 PRS Hospital Assistant Chatbot
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
# SIDEBAR INFO
# ===============================
with st.sidebar.expander("🏥 Hospital Info", expanded=True):
    st.markdown("**PRS Hospital**  \nThiruvananthapuram, Kerala")

with st.sidebar.expander("📞 Emergency", expanded=False):
    st.markdown("🚨 +91 9678768843")
    st.markdown("🚨 +91 9568746574")

with st.sidebar.expander("📞 General Contact Numbers", expanded=False):
    st.markdown("📱 +91 9448123456")
    st.markdown("📱 +91 9448234567")

with st.sidebar.expander("📅 Book Appointment Contacts", expanded=True):
    for num in ["+91 9876543210", "+91 9678547645", "+91 9234765840"]:
        st.markdown(f"📞 {num}")
        st.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

# ===============================
# SIDEBAR SPECIALITIES
# ===============================
with st.sidebar.expander("🩺 Specialities", expanded=False):
    specialities = df["Speciality"].dropna().unique()
    selected_spec = st.selectbox("Choose Speciality", ["All"] + sorted(specialities))

# ===============================
# ADMIN LOGIN (BOTTOM)
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
# DOCTORS
# ===============================
elif menu == "👨‍⚕️ Doctors":
    view_df = df.copy()
    if selected_spec != "All":
        view_df = view_df[view_df["Speciality"].str.lower() == selected_spec.lower()]

    for _, r in view_df.iterrows():
        st.markdown(f"""
        <div style="background:#f8fafc;padding:15px;margin-bottom:10px;
        border-left:5px solid #2563eb;border-radius:10px;">
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
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask your question")

    if st.button("Send") and user_input.strip():
        reply = run_chatbot_query(user_input).replace("\n", "<br>")
        st.session_state.chat_history += [("You", user_input), ("Bot", reply)]

    for role, msg in st.session_state.chat_history:
        st.markdown(f"🧑 **You:** {msg}" if role == "You" else f"🤖 **Bot:** {msg}", unsafe_allow_html=True)

# ===============================
# BOOK APPOINTMENT
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")

    doctors = df if selected_spec == "All" else df[df["Speciality"].str.lower() == selected_spec.lower()]
    doctor = st.selectbox("👨‍⚕️ Select Doctor", sorted(doctors["Doctor Name"].unique()))

    today = datetime.now().date()
    date = st.date_input("📆 Select Date", min_value=today, max_value=today + timedelta(days=7))

    START_TIME, END_TIME = time(9, 0), time(18, 0)
    selected_time = st.time_input("⏰ Select Time", value=START_TIME)

    if not (START_TIME <= selected_time <= END_TIME):
        st.error("❌ Appointment time must be between 9 AM and 6 PM")
        st.stop()

    # ✅ ADDED: Prevent past-time booking
    now = datetime.now()
    if date == now.date() and selected_time <= now.time():
        st.error("❌ Cannot book a past time for today")
        st.stop()

    time_str = selected_time.strftime("%I:%M%p").lstrip("0")

    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Enter patient name")
            st.stop()
        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter valid 10-digit phone number")
            st.stop()

        doc_row = df[df["Doctor Name"] == doctor].iloc[0]
        raw_days = doc_row["Available days"].lower()
        day_name = date.strftime("%A").lower()

        if raw_days not in ["all", "all days", "everyday", "daily"]:
            if day_name not in [d.strip() for d in raw_days.split(",")]:
                st.error(f"❌ {doctor} not available on {date.strftime('%A')}")
                st.stop()

        appt_df = pd.read_csv(APPOINTMENTS_FILE)

        # ✅ ADDED: Prevent duplicate slot
        duplicate = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat()) &
            (appt_df["Time"] == time_str)
        ]
        if not duplicate.empty:
            st.error("❌ This time slot is already booked")
            st.stop()

        count = appt_df[(appt_df["Doctor Name"] == doctor) & (appt_df["Date"] == date.isoformat())].shape[0]
        if count >= 20:
            st.error("❌ Slots full for this doctor")
            st.stop()

        appt_df.loc[len(appt_df)] = {
            "Doctor Name": doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": date.isoformat(),
            "Time": time_str,
            "Reminder Sent": False
        }
        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        send_mock_sms(phone, f"Appointment confirmed with {doctor} on {date} at {time_str}")
        st.success("✅ Appointment booked successfully")
        st.info("📩 SMS sent (simulated)")

# ===============================
# ADMIN VIEW
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))
