import streamlit as st
from datetime import datetime
from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day,
    book_appointment
)

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# TITLE (FIXED AT TOP)
# ===============================
st.markdown(
    """
    <h1 style="text-align:center; color:#084298;">
        🏥 PRS Hospital – Chatbot Assistant
    </h1>
    <hr>
    """,
    unsafe_allow_html=True
)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    **PRS Hospital, Trivandrum**  
    37+ years of excellence in healthcare with modern facilities.
    """)

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

with st.sidebar.expander("📍 Location"):
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

# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "active": False,
        "doctor": None,
        "day": None,
        "patient": None,
        "time": None
    }

# ===============================

# CHAT HISTORY
# ===============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'''
                <div style="
                    text-align: right;
                    background-color: #DCF8C6;
                    padding: 10px;
                    border-radius: 10px;
                    margin: 5px;
                    display: inline-block;
                ">{msg["content"]}</div>
            ''', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'''
                <div style="
                    text-align: left;
                    background-color: #F1F0F0;
                    padding: 10px;
                    border-radius: 10px;
                    margin: 5px;
                    display: inline-block;
                    white-space: pre-line;
                ">{msg["content"]}</div>
            ''', unsafe_allow_html=True)

# ===============================
# INPUT
# ===============================
user_input = st.chat_input(
    "Ask about doctors, timings, availability, or book an appointment…"
)


