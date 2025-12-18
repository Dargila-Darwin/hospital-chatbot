import streamlit as st
from datetime import datetime, time, timedelta

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

    # Date picker (no past dates)
    today = datetime.now().date()
    date = st.date_input(
        "📆 Select Date",
        min_value=today,
        max_value=today + timedelta(days=7)
    )

    day = date.strftime("%A").lower()

    # Time picker
    selected_time = st.time_input(
        "⏰ Select Time",
        value=time(9, 0)
    )

    # Format time for booking
    time_str = selected_time.strftime("%I:%M%p").lstrip("0")  # e.g., "9:30AM"

    if st.button("✅ Confirm Appointment"):
        if not patient_name.strip():
            st.error("❌ Please enter patient name")
        else:
            result = book_appointment(
                doctor=doctor,
                patient=patient_name,
                day=day,
                time_str=time_str
            )

            if result.startswith("✅"):
                st.success(result)
            else:
                st.error(result)
