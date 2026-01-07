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

def parse_available_days(text):
    text = text.lower().strip()

    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    day_map = {
        "mon": "monday", "tue": "tuesday", "wed": "wednesday",
        "thu": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"
    }

    for k, v in day_map.items():
        text = re.sub(rf"\b{k}\b", v, text)

    if "all" in text:
        return days

    if "except" in text or "not available" in text:
        excluded = re.findall("|".join(days), text)
        return [d for d in days if d not in excluded]

    if "to" in text or "-" in text:
        match = re.findall("|".join(days), text)
        if len(match) == 2:
            start = days.index(match[0])
            end = days.index(match[1])
            return days[start:end+1] if start <= end else days[start:] + days[:end+1]

    found = re.findall("|".join(days), text)
    return list(dict.fromkeys(found))

def generate_slots(date, consultation_ranges):
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(tz)
    slots = []

    for start, end in consultation_ranges:
        current = datetime.combine(date, start).replace(tzinfo=tz)
        end_dt = datetime.combine(date, end).replace(tzinfo=tz)

        BUFFER = timedelta(minutes=30)
        while current <= end_dt:
            # Block past time only for today
            if date != now.date() or current >= now + BUFFER:
                slots.append(current.time())
            current += timedelta(minutes=15)

    return slots

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
#About
#================================
elif menu == "ℹ️ About":   
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


#================================
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


# BOOK APPOINTMENT PAGE
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
    available_days = parse_available_days(doc_row["Available days"])

    if not available_days:
        st.error("❌ Doctor availability not set correctly")
        st.stop()

    # Parse consultation time ranges
    consultation_ranges = parse_consultation_ranges(doc_row["Consultation Time"])

    # Calendar for date selection (next 7 days)
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    valid_dates = [today + timedelta(days=i) for i in range(0, 7)]
    valid_dates = [d for d in valid_dates if d.strftime("%A").lower() in available_days]

    if not valid_dates:
        st.warning("❌ This doctor has no available days in the next 7 days.")
        st.stop()
    date = st.selectbox(
        "📆 Select Date",
        valid_dates,
        format_func=lambda d: d.strftime("%A, %d %b %Y")
    )

    # TIME SELECTION
    # TIME SELECTION (SINGLE SOURCE OF TRUTH)

    slots = generate_slots(date, consultation_ranges)
    if date == today and not slots:
        st.warning("⚠️ Doctor session is over for today. Please select another date.")
        st.stop()


    if not slots:
        st.warning("❌ No available slots for this day")
        st.stop()

    selected_time = st.selectbox(
        "⏰ Select Time",
        slots,
        format_func=lambda t: t.strftime("%I:%M %p")
    )

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
        # 🚫 BLOCK SAME PATIENT MULTIPLE BOOKINGS (per doctor per day)
        already_booked = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat()) &
            (
                (appt_df["Phone"] == phone) |
                (appt_df["Patient Name"].str.lower() == patient_name.lower())
            )
        ]

        if not already_booked.empty:
            st.error("❌ You have already booked an appointment with this doctor for this day")
            st.stop()


        # 🚫 BLOCK SAME TIME SLOT
        existing = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat()) &
            (appt_df["Time"] == time_str)
        ]

        if not existing.empty:
            st.error("❌ This time slot is already booked")
            st.stop()

        # 🚫 DAILY LIMIT (20)
        count = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat())
        ].shape[0]

        if count >= 20:
            st.error("❌ Slots full for this doctor on selected day")
            st.stop()

        # ✅ SAVE APPOINTMENT
        appt_df.loc[len(appt_df)] = {
            "Doctor Name": doctor,
            "Patient Name": patient_name,
            "Phone": phone,
            "Date": date.isoformat(),
            "Time": time_str,
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
        
        st.rerun()
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














