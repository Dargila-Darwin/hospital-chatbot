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
# SIDEBAR
# ===============================
st.sidebar.title("📌 PRS Hospital")

# ---------- MAIN MENU ----------
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

# ---------- DOCTORS DETAILS ----------
with st.sidebar.expander("👨‍⚕️ Doctors Details", expanded=False):
    for _, row in df.iterrows():
        st.markdown(
            f"""
            <div style="
                background-color:#f8fafc;
                border:1px solid #cbd5e1;
                border-radius:12px;
                padding:12px;
                margin-bottom:12px;
                box-shadow:0 2px 6px rgba(0,0,0,0.1);
            ">
                <h4 style="color:#2563eb;margin-bottom:6px;">
                    👨‍⚕️ {row['Doctor Name']}
                </h4>
                <p style="margin:2px 0;">
                    🩺 <b>Speciality:</b> {row['Speciality']}
                </p>
                <p style="margin:2px 0;">
                    📅 <b>Available Days:</b> {row['Available days']}
                </p>
                <p style="margin:2px 0;">
                    ⏰ <b>Consultation Time:</b> {row['Consultation Time']}
                </p>
                <p style="margin:2px 0;">
                    📍 <b>Location:</b> {row['Location']}
                </p>
                <p style="margin:2px 0;">
                    📞 <b>Contact:</b> {row['Contact']}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

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

    # ---------- SHOW ALL DOCTORS ----------
    selected_doctor = st.selectbox(
        "👨‍⚕️ Select Doctor",
        df["Doctor Name"].tolist()
    )

    # ---------- TIME INPUT ----------
    selected_time = st.time_input(
        "⏰ Select Time",
        value=time(9, 0)
    )

    # ---------- PATIENT DETAILS ----------
    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")

    if st.button("✅ Confirm Appointment"):

        # ---------- VALIDATIONS ----------
        if not patient_name.strip():
            st.error("❌ Enter patient name")
            st.stop()
        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter valid phone number")
            st.stop()

        # Past time today
        if selected_date == today and selected_time <= now_time:
            st.error("❌ Cannot book past time")
            st.stop()

        # Time window 9:00 AM to 5:45 PM
        if selected_time < time(9, 0) or selected_time > time(17, 45):
            st.error("❌ Appointments allowed only between 9:00 AM and 5:45 PM")
            st.stop()

        # ---------- DOCTOR AVAILABILITY & CONSULTATION HOURS ----------
        doc_row = df[df["Doctor Name"] == selected_doctor].iloc[0]

        # Check day availability
        day_name = selected_date.strftime("%A").lower()
        raw_days = doc_row["Available days"].lower()
        allowed = False
        if any(k in raw_days for k in ["all","everyday","daily"]):
            allowed = True
        else:
            # handle comma-separated or ranges
            days_list = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
            allowed_days = []
            for x in raw_days.replace("to","-").split(","):
                x = x.strip()
                for d in days_list:
                    if d.startswith(x[:3]):
                        allowed_days.append(d)
            allowed = day_name in allowed_days
        if not allowed:
            st.error(f"❌ {selected_doctor} is not available on {day_name.capitalize()}")
            st.stop()

        # Check consultation hours
        consult_time = doc_row["Consultation Time"].replace(" ", "")
        try:
            start_str, end_str = consult_time.split("-")
            start_hour, start_min = map(int, start_str.replace("AM","").replace("PM","").split(":"))
            end_hour, end_min = map(int, end_str.replace("AM","").replace("PM","").split(":"))
            if "PM" in start_str.upper() and start_hour != 12:
                start_hour += 12
            if "PM" in end_str.upper() and end_hour != 12:
                end_hour += 12
            start_time = time(start_hour, start_min)
            end_time = time(end_hour, end_min)
            if selected_time < start_time or selected_time > end_time:
                st.error(f"❌ Appointment outside {selected_doctor}'s consultation hours ({doc_row['Consultation Time']})")
                st.stop()
        except:
            pass  # if parsing fails, ignore

        # ---------- SLOT LIMIT ----------
        appt_df = pd.read_csv(APPOINTMENTS_FILE)
        appt_df["Date"] = pd.to_datetime(appt_df["Date"], errors="coerce")
        if appt_df[
            (appt_df["Doctor Name"] == selected_doctor) &
            (appt_df["Date"].dt.date == selected_date)
        ].shape[0] >= 20:
            st.error("❌ Slots full for this doctor on selected day")
            st.stop()

        # ---------- SAVE APPOINTMENT ----------
        appt_df = pd.concat([appt_df, pd.DataFrame([{
            "Doctor Name": selected_doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": selected_date,
            "Time": selected_time.strftime("%I:%M %p"),
            "Reminder Sent": False
        }])], ignore_index=True)

        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        # SEND MOCK SMS
        send_mock_sms(
            phone,
            f"Appointment confirmed with {selected_doctor} on "
            f"{selected_date.strftime('%A, %d %b')} at {selected_time.strftime('%I:%M %p')}"
        )
        st.success("✅ Appointment booked successfully")

# ===============================
# ADMIN VIEW
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))
