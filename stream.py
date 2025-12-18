import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import (
    run_chatbot_query,
    extract_doctor_name,
    extract_day,
    match_specialty,
    book_appointment,
    df,
    is_available_on,
    parse_time,
    is_time_within_slot
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
# TITLE
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
st.sidebar.title("🏥 PRS Hospital")

with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    **PRS Hospital, Trivandrum**  
    37+ years of excellence in healthcare with modern facilities.
    """)

with st.sidebar.expander("📍 Location"):
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram,  
    Kerala – 695002
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

# Appointment Booking Section
st.sidebar.subheader("📅 Appointment Booking")
appointment_numbers = [
    "+91 9876543210",
    "+91 9678547645",
    "+91 9234765840"
]
for num in appointment_numbers:
    st.sidebar.markdown(f"📞 {num}")
    st.sidebar.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

st.sidebar.subheader("🚨 Emergency Numbers")
emergency_numbers = ["+91 9678768843", "+91 9568746574"]
for num in emergency_numbers:
    st.sidebar.markdown(f"⚠️ **{num}**")

st.sidebar.subheader("📞 General Contact Numbers")
general_numbers = ["+91 9448123456", "+91 9448234567"]
for num in general_numbers:
    st.sidebar.markdown(f"📱 {num}")

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "active": False,
        "doctor": None,
        "patient": None,
        "date": None,
        "time": None
    }

# ===============================
# APPOINTMENTS CSV
# ===============================
APPOINTMENTS_FILE = "appointments.csv"
try:
    appointments_df = pd.read_csv(APPOINTMENTS_FILE)
except FileNotFoundError:
    appointments_df = pd.DataFrame(columns=["Doctor", "Patient", "Day", "Time"])

# ===============================
# CHAT HISTORY DISPLAY
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
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, speciality, day, availability, or book an appointment…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    booking = st.session_state.booking
    reply = ""

    # ---------- BOOK APPOINTMENT ----------
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "👨⚕️ Please specify the doctor's name to book an appointment."
        else:
            booking.update({"active": True, "doctor": doctor})
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."
    
    # ---------- PATIENT NAME ----------
    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "📆 Select appointment date (calendar will appear)."

    # ---------- NORMAL CHAT (BERT-based) ----------
    else:
        reply = run_chatbot_query(user_input)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ===============================
# DATE PICKER (after patient name)
# ===============================
booking = st.session_state.booking
if booking["active"] and booking.get("patient") and booking.get("date") is None:
    selected_date = st.date_input(
        "Select appointment date:",
        min_value=date.today()
    )
    if selected_date:
        booking["date"] = selected_date
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⏰ Select appointment time (picker will appear):"
        })

# ===============================
# TIME PICKER (after date)
# ===============================
if booking["active"] and booking.get("date") and booking.get("time") is None:
    selected_time = st.time_input(
        "Select appointment time:",
        value=time(9, 0)  # Default start time
    )

    if selected_time:
        # Ensure time is within allowed slot
        if not time(9, 0) <= selected_time <= time(20, 0):
            st.warning("⛔ Appointments allowed only between 9:00 AM and 8:00 PM.")
        else:
            booking_day_name = booking["date"].strftime("%A").lower()
            doctor_row = df[df["Doctor Name"].str.contains(booking["doctor"], case=False)]
            if doctor_row.empty:
                st.warning(f"❌ Doctor {booking['doctor']} not found.")
            else:
                doctor_row = doctor_row.iloc[0]
                # Check doctor availability on selected day
                if not is_available_on(booking_day_name, doctor_row["Available days"]):
                    st.warning(f"❌ {booking['doctor']} is not available on {booking_day_name.capitalize()}.")
                else:
                    # Check time within consultation hours
                    if not is_time_within_slot(doctor_row["Consultation Time"], selected_time):
                        st.warning(
                            f"❌ {booking['doctor']} is not available at {selected_time.strftime('%I:%M %p')}. "
                            f"Consultation hours: {doctor_row['Consultation Time']}."
                        )
                    else:
                        # Save appointment
                        new_entry = pd.DataFrame([{
                            "Doctor": booking["doctor"],
                            "Patient": booking["patient"],
                            "Day": booking_day_name.capitalize(),
                            "Time": selected_time.strftime("%I:%M %p")
                        }])
                        appointments_df = pd.concat([appointments_df, new_entry], ignore_index=True)
                        appointments_df.to_csv(APPOINTMENTS_FILE, index=False)
                        st.success(
                            f"✅ Appointment confirmed with **{booking['doctor']}** on "
                            f"**{booking['date']}** at **{selected_time.strftime('%I:%M %p')}**."
                        )
                        st.session_state.booking = {
                            "active": False, "doctor": None, "patient": None, "date": None, "time": None
                        }
