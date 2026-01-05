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
st.sidebar.title("📌 PRS Hospital")
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "👨‍⚕️ Doctors", "ℹ️ About"]
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

elif menu == "👨‍⚕️ Doctors":
    st.subheader("👨‍⚕️ All Doctors")
    
    display_df = df.copy()

    # Display cards in rows of 3 for neat layout
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
# BOOK APPOINTMENT
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    patient_name = st.text_input("👤 Patient Name")
    phone = st.text_input("📞 Phone Number")

    # List all doctors
    doctor_list = df["Doctor Name"].unique()
    doctor = st.selectbox("👨‍⚕️ Select Doctor", sorted(doctor_list))

    # Get selected doctor's info
    doc_row = df[df["Doctor Name"] == doctor].iloc[0]

    # Parse available days
    raw_days = doc_row["Available days"].lower().replace(" ", "")

    if any(x in raw_days for x in ["all", "every", "daily"]):
        available_days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    elif "-" in raw_days:
        start, end = raw_days.split("-")
        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        available_days = days[days.index(start):days.index(end)+1]
    else:
        available_days = [d.strip() for d in raw_days.split(",")]

    # Parse consultation time
    try:
        time_range = doc_row["Consultation Time"].replace(" ", "").split("-")
        start_time = datetime.strptime(time_range[0], "%I:%M%p").time()
        end_time = datetime.strptime(time_range[1], "%I:%M%p").time()
    except:
        st.error("❌ Invalid consultation time format for this doctor")
        st.stop()

    # Valid dates (next 7 days only)
    today = datetime.now().date()
    valid_dates = [
        today + timedelta(days=i)
        for i in range(7)
        if (today + timedelta(days=i)).strftime("%A").lower() in available_days
    ]

    if not valid_dates:
        st.warning("❌ This doctor has no available days in the next 7 days.")
        st.stop()

    date = st.date_input("📆 Select Date", value=min(valid_dates))
    selected_time = st.time_input("⏰ Select Time")

    # CONFIRM BUTTON (ONLY ONE)
    if st.button("✅ Confirm Appointment"):

        # VALIDATIONS
        if not patient_name.strip():
            st.error("❌ Please enter patient name")
            st.stop()

        if not phone.isdigit() or len(phone) != 10:
            st.error("❌ Enter a valid 10-digit phone number")
            st.stop()

        if date not in valid_dates:
            st.error(f"❌ {doctor} is not available on {date.strftime('%A')}")
            st.stop()

        if selected_time < start_time or selected_time > end_time:
            st.error(
                f"❌ Time must be between "
                f"{start_time.strftime('%I:%M %p')} and {end_time.strftime('%I:%M %p')}"
            )
            st.stop()

        time_str = selected_time.strftime("%I:%M%p").lstrip("0")

        # Load appointments
        appt_df = pd.read_csv(APPOINTMENTS_FILE)

        # Max 20 appointments per doctor per day
        count = appt_df[
            (appt_df["Doctor Name"] == doctor) &
            (appt_df["Date"] == date.isoformat())
        ].shape[0]

        if count >= 20:
            st.error("❌ Slots full for this doctor on selected day")
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

        # SMS + success
        send_mock_sms(
            phone,
            f"PRS Hospital: Appointment confirmed with {doctor} "
            f"on {date.strftime('%d %b')} at {time_str}."
        )

        st.success(
            f"✅ Appointment confirmed with {doctor} "
            f"on {date.strftime('%d %B')} at {time_str}"
        )



# ===============================
# ADMIN VIEW
# ===============================
if st.session_state.is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Saved Appointments")
    st.sidebar.dataframe(pd.read_csv(APPOINTMENTS_FILE))


