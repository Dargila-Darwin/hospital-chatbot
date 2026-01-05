import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import os

# ===============================
# FILE SETUP
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPOINTMENTS_FILE = os.path.join(BASE_DIR, "appointments.csv")

if not os.path.exists(APPOINTMENTS_FILE):
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Phone", "Date", "Time", "Reminder Sent"]
    ).to_csv(APPOINTMENTS_FILE, index=False)

# ===============================
# IMPORT CHATBOT & DOCTORS DATA
# ===============================
from chatbot import run_chatbot_query, df

required_cols = ["Doctor Name", "Speciality", "Consultation Time",
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
# SIDEBAR (ORDER FIXED)
# ===============================
st.sidebar.title("📌 PRS Hospital")

# ---------- MAIN MENU FIRST ----------
menu = st.sidebar.radio(
    "Navigate",
    ["ℹ️ About", "💬 Chatbot", "📅 Book Appointment"]
)

# ---------- SPECIALITIES ----------
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

# ---------- LOCATION ----------
with st.sidebar.expander("📍 Location", expanded=False):
    st.markdown("""
    **PRS Hospital**  
    Killipalam  
    Thiruvananthapuram  
    Kerala – 695002
    """)

# ---------- PHONE NUMBERS ----------
with st.sidebar.expander("📞 Phone Numbers", expanded=False):
    st.markdown("""
    📅 **Appointment Booking**  
    +91 9876543210  
    +91 9678547645  
    +91 9234765840  

    🚨 **Emergency**  
    +91 9678768843  
    +91 9568746574  

    ☎️ **General Enquiry**  
    +91 9448123456  
    +91 9448234567
    """)

# ---------- ADMIN (LAST) ----------
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Admin Login")

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

    user_input = st.text_input("Type your question")
    if st.button("Send") and user_input.strip():
        reply = run_chatbot_query(user_input)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", reply))

    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role}:** {msg}")

# ===============================
# BOOK APPOINTMENT PAGE
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    today = datetime.now().date()
    now_time = datetime.now().time().replace(second=0, microsecond=0)


    selected_date = st.date_input(
        "📆 Select Date",
        min_value=today,
        max_value=today + timedelta(days=7)
    )

    day_name = selected_date.strftime("%A").lower()
    days_list = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

    available_doctors = []
    for _, r in df.iterrows():
        raw = r["Available days"].lower().strip()

    # universal keywords
        if any(k in raw for k in ["all", "everyday", "daily"]):
            available_doctors.append(r["Doctor Name"])
            continue
    
        # handle ranges like monday-friday
        if "-" in raw or "to" in raw:
            if day_name[:3] in raw:
                available_doctors.append(r["Doctor Name"])
            continue
    
        # normal comma-separated days
        allowed_days = []
        for x in raw.split(","):
            x = x.strip()
            for d in days_list:
                if d.startswith(x[:3]):
                    allowed_days.append(d)
    
        if day_name in allowed_days:
            available_doctors.append(r["Doctor Name"])


    if not available_doctors:
        st.error("❌ No doctors available on selected day")
        st.stop()

    selected_doctor = st.selectbox("👨‍⚕️ Select Doctor", available_doctors)

    selected_time = st.time_input(
        "⏰ Select Time",
        value=(datetime.now() + timedelta(minutes=10)).time()
        if selected_date == today else time(9, 0)
    )

    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")

    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Enter patient name")
            st.stop()
        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter valid phone number")
            st.stop()
        if selected_date == today and selected_time <= now_time:
            st.error("❌ Cannot book past time")
            st.stop()

        appt_df = pd.read_csv(APPOINTMENTS_FILE)
        appt_df["Date"] = pd.to_datetime(appt_df["Date"], errors="coerce")

        if appt_df[
            (appt_df["Doctor Name"] == selected_doctor) &
            (appt_df["Date"].dt.date == selected_date)
        ].shape[0] >= 20:
            st.error("❌ Slots full")
            st.stop()

        appt_df = pd.concat([appt_df, pd.DataFrame([{
            "Doctor Name": selected_doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": selected_date,
            "Time": selected_time.strftime("%I:%M %p"),
            "Reminder Sent": False
        }])], ignore_index=True)

        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        send_mock_sms(phone, f"Appointment confirmed with {selected_doctor}")
        st.success("✅ Appointment booked successfully")

# ===============================
# ADMIN VIEW
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))


