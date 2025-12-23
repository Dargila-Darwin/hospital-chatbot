import streamlit as st

import pandas as pd

from datetime import datetime, time, timedelta

import os



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPOINTMENTS_FILE = os.path.join(BASE_DIR, "appointments.csv")

# Fix old CSV if it has 'Day' column
if os.path.exists(APPOINTMENTS_FILE):
    df_existing = pd.read_csv(APPOINTMENTS_FILE)
    if "Day" in df_existing.columns:
        df_existing.rename(columns={"Day": "Date"}, inplace=True)
        df_existing.to_csv(APPOINTMENTS_FILE, index=False)

# Create new CSV if it doesn't exist
if not os.path.exists(APPOINTMENTS_FILE):
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Date", "Time"]
    ).to_csv(APPOINTMENTS_FILE, index=False)








from chatbot import (
    run_chatbot_query,
    book_appointment,
    df,
    availability_on_day_for_specialty
)




# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Assistant",
    page_icon="🏥",
    layout="centered"
)

# ===============================




# ===============================
# BACKGROUND IMAGE FUNCTION
# ===============================



# FIXED HEADER
# ===============================
st.markdown(
    """
    <h1 style="
        text-align:center;
        position:sticky;
        top:0;
        background:#0f172a;
        color:white;
        padding:14px;
        border-radius:10px;
        z-index:999;
    ">
        🏥 PRS Hospital Assistant Chatbot
    </h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("📌 PRS Hospital")
menu = st.sidebar.radio(
    "Navigate",
    ["💬 Chatbot", "📅 Book Appointment", "👨‍⚕️ Doctors", "ℹ️ About"]
)

# ===============================
# ABOUT
# ===============================
if menu == "ℹ️ About":
    st.markdown(
        """
        ### 🏥 About PRS Hospital
        **PRS Hospital, Thiruvananthapuram**

        ✔ Multi-specialty hospital  
        ✔ Experienced doctors  
        ✔ Consultation: 9 AM – 8 PM  
        ✔ Easy online appointment booking  
        """
    )

# ===============================
# DOCTORS TAB (FULL INFO)
# ===============================
elif menu == "👨‍⚕️ Doctors":
    st.markdown(
        """
        <h2 style="
            text-align:center;
            color:#1e3a8a;
            font-weight:800;
            margin-bottom:20px;
        ">
            👨‍⚕️ Our Expert Doctors
        </h2>
        """,
        unsafe_allow_html=True
    )

    for _, r in df.iterrows():
        st.markdown(
            f"""
            <div style="
                width:100%;
                background-color:#f8fafc;
                padding:18px;
                margin-bottom:15px;
                border-left:6px solid #2563eb;
                border-radius:12px;
                box-shadow:0 4px 10px rgba(0,0,0,0.08);
            ">
                <div style="font-size:20px; font-weight:800; color:#0f172a;">
                    🧑‍⚕️ {r['Doctor Name']}
                </div>
                <div style="margin-top:6px;">
                    🩺 <b>Speciality:</b> {r['Speciality']}
                </div>
                <div>
                    ⏰ <b>Consultation Time:</b> {r['Consultation Time']}
                </div>
                <div>
                    📅 <b>Available Days:</b> {r['Available days']}
                </div>
                <div>
                    📍 <b>Location:</b> {r['Location']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ===============================
# CHATBOT TAB
# ===============================
elif menu == "💬 Chatbot":
    st.subheader("💬 Ask the Hospital Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Type your question here")

    if st.button("Send") and user_input.strip():
        reply = run_chatbot_query(user_input)
        # Convert multiline speciality response to line by line
        if "\n" in reply:
            reply = reply.replace("\n", "<br>")
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", reply))

    for role, msg in st.session_state.chat_history:
        if role == "You":
            st.markdown(f"🧑 **You:** {msg}")
        else:
            st.markdown(f"🤖 **Bot:** {msg}", unsafe_allow_html=True)

# ===============================
# BOOK APPOINTMENT TAB
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book an Appointment")

    patient_name = st.text_input("👤 Patient Name")

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

    selected_time = st.time_input(
        "⏰ Select Time",
        value=START_TIME
    )

    if not (START_TIME <= selected_time <= END_TIME):
        st.error("❌ Appointment time must be between 9:00 AM and 6:00 PM")
        st.stop()

    time_str = selected_time.strftime("%I:%M%p").lstrip("0")  # e.g., "9:30AM"

    # ✅ Confirm Appointment button (only once!)
    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Please enter patient name")
            st.stop()

        now = datetime.now()
        if date == now.date() and selected_time <= now.time():
            st.error("❌ Cannot book past time for today")
            st.stop()

        appt_df = pd.read_csv(APPOINTMENTS_FILE)

        appt_df.loc[len(appt_df)] = {
            "Doctor Name": doctor,
            "Patient Name": patient_name,
            "Date": date.isoformat(),
            "Time": time_str
        }

        appt_df.to_csv(APPOINTMENTS_FILE, index=False)

        st.success(
            f"✅ Appointment confirmed with {doctor} on {date.strftime('%d %B')} at {time_str}"
        )

   

# ===============================
# SIDEBAR
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

# Saved Appointments
with st.sidebar.expander("📋 Saved Appointments", expanded=True):
    st.dataframe(pd.read_csv(APPOINTMENTS_FILE))












