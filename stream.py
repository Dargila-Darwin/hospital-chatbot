import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

import os
import re  

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
def parse_consultation_ranges(text):
    """
    Supports:
    9.30AM to 1.30 PM
    4PM - 7PM
    9 AM to 4 PM
    10.30AM to 2PM
    9am to 2pm
    """

    text = text.lower().replace("–", "-").replace("—", "-")

    # Split multiple sessions (newline or comma)
    parts = re.split(r"\n|,", text)

    ranges = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        part = part.replace("to", "-").replace(" ", "")

        if "-" not in part:
            continue

        start_raw, end_raw = part.split("-")

        def fix(t):
            t = t.replace(".", ":")
            if re.match(r"^\d{1,2}(am|pm)$", t):
                t = t[:-2] + ":00" + t[-2:]
            return datetime.strptime(t, "%I:%M%p").time()

        start = fix(start_raw)
        end = fix(end_raw)

        # Enforce hospital timing
        HOSPITAL_START = time(9, 0)
        HOSPITAL_END = time(18, 0)

        start = max(start, HOSPITAL_START)
        end = min(end, HOSPITAL_END)

        if start < end:
            ranges.append((start, end))

    if not ranges:
        raise ValueError("Invalid consultation time")

    return ranges


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
    ["💬 Chatbot", "📅 Book Appointment", "👨⚕️ Doctors", "ℹ️ About"]
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

elif elif "About" in menu: 
    st.markdown(
        """
        ### 🏥 About PRS Hospital
        **PRS Hospital, Thiruvananthapuram**

        ✔ Multi-specialty hospital  
        ✔ Experienced doctors  
        ✔ Consultation: 9 AM – 6 PM  
        ✔ Easy online appointment booking  
        """
    )
# DOCTORS PAGE
# ===============================
elif menu == "👨⚕️ Doctors":
    st.subheader("👨⚕️ All Doctors")
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
                    <h4 style="margin-bottom:5px;">👨⚕️ {r['Doctor Name']}</h4>
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



# ===============================
# BOOK APPOINTMENT PAGE
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")
    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")
    
    doctor_list = df["Doctor Name"].unique()
    doctor = st.selectbox("👨⚕️ Select Doctor", sorted(doctor_list))
    doc_row = df[df["Doctor Name"] == doctor].iloc[0]

    # Parse available days
    raw_days = doc_row["Available days"].lower().strip()
    all_days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    available_days = []

    if "available all days" in raw_days:
        available_days = all_days
    elif "not available on" in raw_days:
        excluded = re.findall(r"monday|tuesday|wednesday|thursday|friday|saturday|sunday", raw_days)
        available_days = [d for d in all_days if d not in excluded]
    else:
        days = [d.strip() for d in re.split(r",|;", raw_days)]
        available_days = [d for d in days if d in all_days]

    # Parse consultation time ranges
    consultation_ranges = parse_consultation_ranges(doc_row["Consultation Time"])

    # Calendar for date selection (next 7 days)
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    valid_dates = [today + timedelta(days=i) for i in range(0, 7)]
    valid_dates = [d for d in valid_dates if d.strftime("%A").lower() in available_days]

    if not valid_dates:
        st.warning("❌ This doctor has no available days in the next 7 days.")
        st.stop()

    date = st.date_input(
        "📆 Select Date",
        min_value=min(valid_dates),
        max_value=max(valid_dates),
        value=min(valid_dates)
    )

    # TIME SELECTION
    # TIME SELECTION (SINGLE SOURCE OF TRUTH)
    default_time = consultation_ranges[0][0]

    selected_time = st.time_input("⏰ Select Time", value=default_time)

   

    # Validate selected time against consultation hours
    if not any(start <= selected_time <= end for start, end in consultation_ranges):
        allowed = ", ".join(
            f"{s.strftime('%I:%M %p')}–{e.strftime('%I:%M %p')}" for s, e in consultation_ranges
        )
        st.error(f"❌ Allowed time: {allowed}")
        st.stop()

    time_str = selected_time.strftime("%I:%M%p").lstrip("0")

    if st.button("✅ Confirm Appointment"):

    # 🔐 HARD BLOCK — FINAL AUTHORITY CHECK
        now = datetime.now(ZoneInfo("Asia/Kolkata")).replace(second=0, microsecond=0)

        selected_datetime = datetime.combine(date, selected_time).replace(
            tzinfo=ZoneInfo("Asia/Kolkata")
        )
        st.write("🕒 DEBUG NOW:", now)
        st.write("📅 DEBUG SELECTED:", selected_datetime)

        if selected_datetime < now:
            st.error("❌ Cannot book a past date or time")
            st.stop()

        if not patient_name.strip():
            st.error("❌ Please enter patient name")
            st.stop()

        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter a valid 10-digit phone number")
            st.stop()

        appt_df = pd.read_csv(APPOINTMENTS_FILE)
        count = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat())
        ].shape[0]

        if count >= 20:
            st.error("❌ Slots full for this doctor on selected day")
            st.stop()

        appt_df.loc[len(appt_df)] = {
            "Doctor Name": doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": date.isoformat(),
            "Time": selected_time.strftime("%I:%M%p").lstrip("0"),
            "Reminder Sent": False
        }

        appt_df.to_csv(APPOINTMENTS_FILE, index=False)
        send_mock_sms(
            phone,
            f"PRS Hospital: Appointment confirmed with {doctor} on "
            f"{date.strftime('%d %b')} at "
            f"{selected_time.strftime('%I:%M%p').lstrip('0')}."
        )
        st.success("✅ Appointment confirmed")

        

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































