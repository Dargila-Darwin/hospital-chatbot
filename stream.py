import streamlit as st
from datetime import datetime, time, timedelta

import base64
import os

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
def set_background(image_path):
    """
    Sets a background image in Streamlit.
    Accepts either a file in the same folder or a subfolder.
    """
    if not os.path.exists(image_path):
        st.warning(f"Background image not found: {image_path}")
        return

    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Optional light overlay to increase brightness */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.45);
            z-index: -1;
        }}

        /* Main content container */
        .block-container {{
            background-color: rgba(255,255,255,0.95);
            padding: 2rem;
            border-radius: 16px;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: rgba(255,255,255,0.97);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ===============================
# CALL THE FUNCTION
# ===============================
# Replace with your folder/filename if different
set_background("assets/hos-image.jpg")


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
            # 🔒 REAL-TIME CHECK FOR TODAY
            now = datetime.now()

            if date == now.date():
                if selected_time <= now.time():
                    st.error("❌ Cannot book past time for today")
                    st.stop()

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




with st.sidebar.expander("🩺 Specialities"):
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

with st.sidebar.expander("🏥 Location"):
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram,  
    Kerala – 695002
    """)

# Appointment Booking Section (clickable)
st.sidebar.subheader("📅 Appointment Booking")
appointment_numbers = [
    "+91 9876543210",
    "+91 9678547645",
    "+91 9234765840"
]
for num in appointment_numbers:
    st.sidebar.markdown(f"📞 {num}")
    st.sidebar.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

# Emergency Contact Section (non-clickable)
st.sidebar.subheader("🚨 Emergency Numbers")
emergency_numbers = [
    "+91 9678768843",
    "+91 9568746574"
]
for num in emergency_numbers:
    st.sidebar.markdown(f"⚠️ **{num}**")

# General Contact Numbers (non-clickable)
st.sidebar.subheader("📞 General Contact Numbers")
general_numbers = [
    "+91 9448123456",
    "+91 9448234567"
]
for num in general_numbers:
    st.sidebar.markdown(f"📱 {num}")





