import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd

from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day,
    match_specialty,
    book_appointment,
    df
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
# FIXED HEADER
# ===============================
st.markdown(
    """
    <h1 style='text-align:center; position:sticky; top:0; background:#0f172a;
    color:white; padding:12px; border-radius:8px; z-index:999'>
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
    st.info(
        """
        **PRS Hospital – Thiruvananthapuram**

        ✔ Multi-specialty hospital  
        ✔ Expert doctors  
        ✔ 9 AM – 8 PM consultations  
        ✔ Easy appointment booking
        """
    )

# ===============================
# DOCTOR LIST
# ===============================
elif menu == "👨‍⚕️ Doctors":
    st.subheader("👨‍⚕️ Our Doctors")

    for _, r in df.iterrows():
        st.markdown(
            f"""
            **{r['Doctor Name']}**  
            🩺 {r['Speciality']}  
            ⏰ {r['Consultation Time']}  
            📅 {r['Available days']}  
            📍 {r['Location']}
            ---
            """
        )

# ===============================
# CHATBOT
# ===============================
elif menu == "💬 Chatbot":
    st.subheader("💬 Ask me anything")

    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.text_input("Type your question")

    if st.button("Send") and user_input:
        response = run_chatbot_query(user_input)
        st.session_state.history.append(("You", user_input))
        st.session_state.history.append(("Bot", response))

    for role, msg in st.session_state.history:
        if role == "You":
            st.markdown(f"🧑 **You:** {msg}")
        else:
            st.markdown(f"🤖 **Bot:** {msg}")

# ===============================
# APPOINTMENT BOOKING
# ===============================
elif menu == "📅 Book Appointment":
    st.subheader("📅 Book Appointment")

    patient = st.text_input("👤 Patient Name")

    doctor = st.selectbox(
        "👨‍⚕️ Select Doctor",
        sorted(df["Doctor Name"].unique())
    )

    # DATE PICKER
    min_date = datetime.now().date()
    max_date = min_date + timedelta(days=7)
    date = st.date_input(
        "📆 Select Date",
        min_value=min_date,
        max_value=max_date
    )

    day = date.strftime("%A").lower()

    # TIME PICKER
    selected_time = st.time_input(
        "⏰ Select Time",
        value=time(9, 0)
    )

    time_str = selected_time.strftime("%I%p")

    if st.button("✅ Confirm Appointment"):
        if not patient.strip():
            st.error("❌ Enter patient name")
        else:
            result = book_appointment(
                doctor=doctor,
                patient=patient,
                day=day,
                time_str=time_str
            )

            if result.startswith("✅"):
                st.success(result)
            else:
                st.error(result)
