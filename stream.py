import streamlit as st
from datetime import datetime, date, time
from chatbot import run_chatbot_query, extract_doctor_name, extract_day, book_appointment

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot Assistant",
    page_icon="🏥",
    layout="wide"
)

# ===============================
# BACKGROUND IMAGE + STYLES
# ===============================
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("hos-image.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: rgba(255,255,255,0.9);
        z-index: 1000;
        padding: 15px 0;
        border-bottom: 1px solid #ddd;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: #084298;
    }}
    .chat-container {{
        margin-top: 80px;
    }}
    </style>
    <div class="header">🏥 PRS Hospital Chatbot Assistant</div>
    """,
    unsafe_allow_html=True
)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("🏥 PRS Hospital")

    with st.expander("ℹ️ About"):
        st.write(
            "PRS Hospital, Thiruvananthapuram, has over 37 years of excellence "
            "in multi-specialty healthcare and advanced medical services."
        )

    with st.expander("🩺 Specialities"):
        specialities = [
            "Cardiologist", "ENT", "Gastroenterologist", "Gynecologist",
            "Nephrologist", "Neurologist", "Urologist", "Pulmonologist",
            "Dermatologist", "Ophthalmologist", "Orthopaedician", "Oncologist",
            "Pathologist", "Radiologist", "Psychiatrist", "Psychologist",
            "Endocrinologist", "General Surgeon", "Paediatrician"
        ]

        for spec in specialities:
            if st.button(spec, key=f"spec_{spec}"):
                st.session_state.selected_speciality = spec
                st.rerun()

    with st.expander("📍 Location"):
        st.markdown(
            "**PRS Hospital**  \n"
            "Killipalam, Thiruvananthapuram, Kerala – 695002"
        )

    st.markdown("### 📞 Appointment Booking")
    st.markdown("📞 +91 98765 43210")
    st.markdown("📞 +91 96785 47645")
    st.markdown("### ☎️ Emergency")
    st.markdown("🚨 +91 95687 46574")

# ===============================
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

if "selected_speciality" not in st.session_state:
    st.session_state.selected_speciality = None

# ===============================
# HELPER FUNCTIONS
# ===============================
def format_doctors_line_by_line(response):
    lines = response.split("\n")
    formatted = ""
    for line in lines:
        line = line.strip()
        if line:
            formatted += f"👨‍⚕️ {line}\n"
    return formatted

def get_day_name(d):
    return d.strftime("%A").lower()

# ===============================
# SPECIALITY CLICK HANDLER
# ===============================
if st.session_state.selected_speciality:
    spec = st.session_state.selected_speciality
    response = run_chatbot_query(f"{spec} doctors today")
    formatted = format_doctors_line_by_line(response)
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"🩺 **{spec} Doctors Available Today:**\n\n{formatted}"
    })
    st.session_state.selected_speciality = None
    st.rerun()

# ===============================
# DISPLAY CHAT
# ===============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, availability, or book an appointment…")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    booking = st.session_state.booking
    reply = ""

    # ---------- BOOKING FLOW ----------
    if not booking["active"] and "book" in user_input.lower():
        doctor = extract_doctor_name(user_input)
        day = extract_day(user_input)
        if not doctor:
            reply = "👨‍⚕️ Please specify the doctor's name to book an appointment."
        else:
            booking.update({
                "active": True,
                "doctor": doctor,
                "day": day
            })
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease tell your name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "⏰ Enter preferred time (example: **10AM**)"

    elif booking["active"] and not booking["time"]:
        try:
            selected_time = datetime.strptime(user_input.strip(), "%I%p").time()
            if not time(9, 0) <= selected_time <= time(20, 0):
                reply = "⛔ Appointments allowed only between 9AM and 8PM."
            else:
                booking["time"] = selected_time.strftime("%I:%M %p")
                reply = book_appointment(
                    booking["doctor"],
                    booking["patient"],
                    booking["day"] or datetime.now().strftime("%A"),
                    booking["time"]
                )
                # reset booking
                st.session_state.booking = {
                    "active": False,
                    "doctor": None,
                    "day": None,
                    "patient": None,
                    "time": None
                }
        except:
            reply = "❌ Invalid format. Use **10AM**."

    else:
        response = run_chatbot_query(user_input)
        reply = format_doctors_line_by_line(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })
    st.rerun()
