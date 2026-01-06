import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import os
import re  # <-- new import for time parsing

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
# TIME PARSING FUNCTION (NEW)
# ===============================
def parse_time_range(time_str):
    time_str = time_str.strip().lower().replace(" ", "").replace("to", "-")

    if "-" not in time_str:
        raise ValueError("Invalid consultation time format")

    start_str, end_str = time_str.split("-")

    def parse_single(t):
        t = t.replace(".", ":")  # 10.30am → 10:30am

        if re.match(r"^\d{1,2}(am|pm)$", t):
            t = t[:-2] + ":00" + t[-2:]

        return datetime.strptime(t, "%I:%M%p").time()

    start_time = parse_single(start_str)
    end_time = parse_single(end_str)

    # Hospital working hours
    HOSPITAL_START = time(9, 0)   # 9:00 AM
    HOSPITAL_END   = time(18, 0)  # 6:00 PM

    # Final allowed range = doctor ∩ hospital
    start_time = max(start_time, HOSPITAL_START)
    end_time = min(end_time, HOSPITAL_END)

    if start_time >= end_time:
        raise ValueError("Doctor not available during hospital hours")

    return start_time, end_time


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
# ---------- ADMIN LOGIN ----------
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Admin Login")

if not st.session_state.is_admin:
    username = st.sidebar.text_input("Username", key="admin_user")
    password = st.sidebar.text_input("Password", type="password", key="admin_pass")
    if st.sidebar.button("Login"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.sidebar.success("Admin logged in")
        else:
            st.sidebar.error("Invalid credentials")
else:
    st.sidebar.success("Admin logged in")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False

    # Show appointments CSV only if logged in
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Saved Appointments")
    try:
        appt_df = pd.read_csv(APPOINTMENTS_FILE)
        st.sidebar.dataframe(appt_df)
    except Exception as e:
        st.sidebar.error(f"Could not load appointments: {e}")
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "👨‍⚕️ Doctors", "ℹ️ About"]
)

# Sidebar content (specialities, location, phone numbers, admin login)...
# [UNCHANGED]

# ===============================
# CHATBOT PAGE
# ===============================
if menu == "💬 Chatbot":
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
# DOCTORS PAGE
# ===============================
elif menu == "👨‍⚕️ Doctors":
    st.subheader("👨‍⚕️ All Doctors")
    display_df = df.copy()
    for i in range(0, len(display_df), 3):
        cols = st.columns(3)
        for j, (_, r) in enumerate(display_df.iloc[i:i+3].iterrows()):
            with cols[j]:
                st.markdown(
                    f"""
                    <div style="
                        background:#f8fafc;
                        padding:15px;
                        margin-bottom:15px;
                        border-left:5px solid #2563eb;
                        border-radius:12px;
                        box-shadow: 2px 2px 12px rgba(0,0,0,0.08);
                        text-align:center;
                    ">
                    <h4 style="margin-bottom:5px;">👨‍⚕️ {r['Doctor Name']}</h4>
                    <p style="margin:0;">🩺 {r['Speciality']}</p>
                    <p style="margin:0;">⏰ {r['Consultation Time']}</p>
                    <p style="margin:0;">📅 {r['Available days']}</p>
                    <p style="margin:0;">📍 {r['Location']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ===============================

# ===============================



# BOOK APPOINTMENT PAGE
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")
    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")
    doctor_list = df["Doctor Name"].unique()
    doctor = st.selectbox("👨‍⚕️ Select Doctor", sorted(doctor_list))
    doc_row = df[df["Doctor Name"] == doctor].iloc[0]

    # Parse available days (UNCHANGED)
    raw_days = doc_row["Available days"].lower().strip()
    if any(x in raw_days for x in ["all", "every", "daily"]):
        available_days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    elif "-" in raw_days:
        start, end = raw_days.split("-")
        days_full = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        abbr_map = {"mon":"monday","tue":"tuesday","wed":"wednesday","thu":"thursday",
                    "fri":"friday","sat":"saturday","sun":"sunday"}
        start = abbr_map.get(start[:3], start)
        end = abbr_map.get(end[:3], end)
        available_days = days_full[days_full.index(start):days_full.index(end)+1]
    else:
        available_days = [d.strip() for d in raw_days.split(",")]

    # ===============================
    # FIXED TIME PARSING
    # ===============================
    start_time, end_time = parse_time_range(doc_row["Consultation Time"])

    # Calendar for date selection
    today = datetime.now().date()
    valid_dates = [today + timedelta(days=i) for i in range(0, 7)]
    valid_dates = [d for d in valid_dates if d.strftime("%A").lower() in available_days]

    if not valid_dates:
        st.warning("❌ This doctor has no available days in the next 7 days.")
    else:
        date = st.date_input("📆 Select Date", min_value=min(valid_dates), max_value=max(valid_dates), value=min(valid_dates))
        selected_time = st.time_input("⏰ Select Time", value=start_time)
        if not (start_time <= selected_time <= end_time):
            st.error(f"❌ Time must be between {start_time.strftime('%I:%M %p')} and {end_time.strftime('%I:%M %p')}")
            st.stop()
        time_str = selected_time.strftime("%I:%M%p").lstrip("0")

        if st.button("✅ Confirm Appointment"):
            if not patient_name.strip():
                st.error("❌ Please enter patient name")
                st.stop()
            if not phone.isdigit() or len(phone) != 10:
                st.error("❌ Enter a valid 10-digit phone number")
                st.stop()

            appt_df = pd.read_csv(APPOINTMENTS_FILE)
            count = appt_df[(appt_df["Doctor Name"] == doctor) & (appt_df["Date"] == date.isoformat())].shape[0]
            if count >= 20:
                st.error("❌ Slots full for this doctor on selected day")
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
            send_mock_sms(phone, f"PRS Hospital: Appointment confirmed with {doctor} on {date.strftime('%d %b')} at {time_str}.")
            st.success(f"✅ Appointment confirmed with {doctor} on {date.strftime('%d %B')} at {time_str}")
            st.info("📩 Confirmation SMS sent (simulated)")

# ===============================


# Hospital Info
with st.sidebar.expander("🏥 Hospital Info", expanded=True):
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram,  
    Kerala – 695002
    """)

# Specialities
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

# Appointment Booking Contacts
with st.sidebar.expander("📅 Book Appointment Contacts", expanded=True):
    appointment_numbers = [
        "+91 9876543210",
        "+91 9678547645",
        "+91 9234765840"
    ]
    for num in appointment_numbers:
        st.markdown(f"📞 {num}")
        st.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

# Emergency Numbers
with st.sidebar.expander("🚨 Emergency Numbers", expanded=False):
    emergency_numbers = [
        "+91 9678768843",
        "+91 9568746574"
    ]
    for num in emergency_numbers:
        st.markdown(f"⚠️ **{num}**")

# General Contact Numbers
with st.sidebar.expander("📞 General Contact Numbers", expanded=False):
    general_numbers = [
        "+91 9448123456",
        "+91 9448234567"
    ]
    for num in general_numbers:
        st.markdown(f"📱 {num}")





