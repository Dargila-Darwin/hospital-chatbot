# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from chatbot import run_chatbot_query, extract_doctor_name

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
st.markdown("""
<h1 style="text-align:center; color:#084298;">
🏥 PRS Hospital – Chatbot Assistant
</h1>
<hr>
""", unsafe_allow_html=True)

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("🏥 Hospital Dashboard")

with st.sidebar.expander("ℹ️ About"):
    st.markdown("""
    **PRS Hospital, Trivandrum**  
    37+ years of excellence in healthcare.
    """)

with st.sidebar.expander("🩺 Specialities"):
    st.markdown("""
    - Cardiologist  
    - ENT  
    - Gastroenterologist  
    - Gynecologist  
    - Neurologist  
    - Orthopaedician  
    - Paediatrician  
    """)

with st.sidebar.expander("📍 Location"):
    st.markdown("""
    **PRS Hospital**  
    Killipalam,  
    Thiruvananthapuram, Kerala – 695002
    """)

st.sidebar.subheader("📅 Appointment Booking")
HOSPITAL_CONTACTS = ["+91 9876543210", "+91 9678547645"]
for num in HOSPITAL_CONTACTS:
    st.sidebar.markdown(f"📞 {num}")
    st.sidebar.markdown(f"[Call {num}](tel:{num.replace(' ', '')})")

st.sidebar.subheader("🚨 Emergency")
st.sidebar.markdown("⚠️ **+91 9568746574**")

# ===============================
# SESSION STATE
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = {
        "step": None,
        "doctor": None,
        "patient": None,
        "date": None,
        "time": None
    }

# ===============================
# APPOINTMENT STORAGE
# ===============================
APPT_FILE = "appointments.csv"
MAX_SLOTS_PER_DOCTOR = 5

if not pd.io.common.file_exists(APPT_FILE):
    pd.DataFrame(columns=["Doctor", "Patient", "Date", "Time"]).to_csv(APPT_FILE, index=False)

def save_appointment(doc, patient, d, t):
    df = pd.read_csv(APPT_FILE)
    slots = df[(df["Doctor"] == doc) & (df["Date"] == str(d)) & (df["Time"] == t)]
    if len(slots) >= MAX_SLOTS_PER_DOCTOR:
        return f"⛔ Slot full for **{doc}** on **{d} {t}**."
    df.loc[len(df)] = [doc, patient, str(d), t]
    df.to_csv(APPT_FILE, index=False)
    return (
        f"✅ Appointment confirmed\n\n"
        f"👨‍⚕️ Doctor: **{doc}**\n"
        f"👤 Patient: **{patient}**\n"
        f"📅 Date: **{d}**\n"
        f"⏰ Time: **{t}**"
    )

# ===============================
# CHAT DISPLAY
# ===============================
for msg in st.session_state.messages:
    align = "right" if msg["role"] == "user" else "left"
    color = "#DCF8C6" if msg["role"] == "user" else "#F1F0F0"

    with st.chat_message(msg["role"]):
        st.markdown(f"""
        <div style="
            text-align:{align};
            background:{color};
            padding:10px;
            border-radius:10px;
            display:inline-block;
            white-space:pre-line;
        ">
        {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, speciality, degree, location, or book appointment")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    booking = st.session_state.booking
    reply = ""

    # ---------------- BOOKING FLOW ----------------
    if "book" in user_input.lower() and booking["step"] is None:
        doctor = extract_doctor_name(user_input)
        if not doctor:
            reply = "Please mention doctor name for booking."
        else:
            booking["doctor"] = doctor
            booking["step"] = "patient"
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    elif booking["step"] == "patient":
        booking["patient"] = user_input.strip()
        booking["step"] = "date"
        reply = "📆 Select appointment date from calendar below."

    elif booking["step"] == "date":
        pass  # handled below

    elif booking["step"] == "time":
        pass  # handled below

    else:
        reply = run_chatbot_query(user_input)

    if reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ===============================
# CALENDAR + TIME UI
# ===============================
booking = st.session_state.booking

if booking["step"] == "date":
    d = st.date_input("Select date", min_value=date.today())
    if st.button("Confirm Date"):
        booking["date"] = d
        booking["step"] = "time"
        st.rerun()

if booking["step"] == "time":
    t = st.time_input("Select time", value=time(9, 0))
    selected_dt = datetime.combine(booking["date"], t)
    now = datetime.now()

    if st.button("Confirm Time"):
        if selected_dt < now:
            st.error("⛔ Cannot book past time.")
        elif t < time(9, 0) or t > time(20, 0):
            st.error("⛔ Allowed only between 9am and 8pm.")
        else:
            result = save_appointment(
                booking["doctor"],
                booking["patient"],
                booking["date"],
                t.strftime("%I:%M%p").lower()
            )
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.session_state.booking = {
                "step": None,
                "doctor": None,
                "patient": None,
                "date": None,
                "time": None
            }
            st.rerun()
