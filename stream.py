import streamlit as st
from datetime import datetime, time
from chatbot import run_chatbot_query, extract_doctor_name, extract_day, book_appointment

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot Assistant",
    page_icon="🏥",
    layout="centered"
)

# ===============================
# CUSTOM CSS (HOSPITAL THEME + BACKGROUND IMAGE + OVERLAY)
# ===============================
st.markdown(f"""
<style>
/* Background image with overlay */
[data-testid="stAppViewContainer"] {{
    background-image: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url('hos-image.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

/* Header */
.header {{
    position: fixed;
    top: 0;
    width: 100%;
    background-color: rgba(255,255,255,0.95);
    z-index: 9999;
    padding: 15px 0;
    border-bottom: 2px solid #0055AA;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    color: #0055AA;
}}

/* Content spacing */
.content {{
    margin-top: 100px;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: #F5F5F5;
    padding: 20px;
}}

/* Chat bubbles */
.user-bubble {{
    background-color: rgba(220, 248, 198, 0.9);
    color: #000;
    padding: 10px 14px;
    border-radius: 10px;
    margin: 5px;
    max-width: 70%;
    align-self: flex-end;
}}

.assistant-bubble {{
    background-color: rgba(241, 240, 240, 0.9);
    color: #000;
    padding: 10px 14px;
    border-radius: 10px;
    margin: 5px;
    max-width: 70%;
    align-self: flex-start;
    white-space: pre-line;
}}
</style>

<div class="header">🏥 PRS Hospital Chatbot Assistant</div>
<div class="content"></div>
""", unsafe_allow_html=True)

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
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("🏥 PRS Hospital")

    with st.expander("ℹ️ About"):
        st.markdown("""
        **PRS Hospital, Thiruvananthapuram**  
        37+ years of excellence in healthcare with modern facilities.
        """)

    with st.expander("🩺 Specialities"):
        specialities = [
            "Cardiologist", "ENT", "Gastroenterologist", "Gynecologist",
            "Nephrologist", "Neurologist", "Urologist", "Pulmonologist",
            "Dermatologist", "Ophthalmologist", "Orthopaedician", "Oncologist",
            "Pathologist", "Radiologist", "Psychiatrist", "Psychologist",
            "Endocrinologist", "General Surgeon", "Paediatrician"
        ]
        for spec in specialities:
            if st.button(spec, key=spec):
                st.session_state.selected_speciality = spec
                st.rerun()

    with st.expander("📍 Location"):
        st.markdown("""
        **PRS Hospital**  
        Killipalam, Thiruvananthapuram, Kerala – 695002
        """)

    st.markdown("### 📞 Appointment Booking")
    st.markdown("📞 +91 98765 43210")
    st.markdown("📞 +91 96785 47645")

    st.markdown("### 🚨 Emergency")
    st.markdown("🚨 +91 95687 46574")

# ===============================
# HELPERS
# ===============================
def format_doctors_line_by_line(response):
    lines = []
    for line in response.split("\n"):
        line = line.strip()
        if line:
            if not line.startswith("👨‍⚕️"):
                line = f"👨‍⚕️ {line}"
            lines.append(line)
    return "\n".join(lines)

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
# CHAT DISPLAY
# ===============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'<div class="assistant-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

# ===============================
# USER INPUT
# ===============================
user_input = st.chat_input("Ask about doctors, timings, availability, or book an appointment…")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    booking = st.session_state.booking
    reply = ""

    # ---------- BOOK APPOINTMENT ----------
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
            reply = f"📅 Booking appointment with **{doctor}**.\nPlease enter patient name."

    elif booking["active"] and not booking["patient"]:
        booking["patient"] = user_input.strip()
        reply = "⏰ Enter preferred time (example: **10am**)."

    elif booking["active"] and not booking["time"]:
        try:
            selected_time = datetime.strptime(user_input.strip(), "%I%p")
            if not time(9, 0) <= selected_time.time() <= time(20, 0):
                reply = "⛔ Appointments allowed only between 9 AM and 8 PM."
            else:
                booking["time"] = user_input.strip()
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
            reply = "❌ Invalid format. Use example: 10am"

    # ---------- NORMAL CHAT ----------
    else:
        response = run_chatbot_query(user_input)
        reply = format_doctors_line_by_line(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })
    st.rerun()
