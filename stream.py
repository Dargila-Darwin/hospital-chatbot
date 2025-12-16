import streamlit as st
from chatbot import run_chatbot_query
import base64

# ===============================
# Page Config
# ===============================
st.set_page_config(
    page_title="PRS Hospital Chatbot",
    page_icon="🏥",
    layout="wide"
)

# ===============================
# Background Image
# ===============================
def set_bg(image):
    with open(image, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("data:image/jpg;base64,{img}");
            background-size: cover;
            background-attachment: fixed;
        }}

        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            text-align: center;
            font-size: 26px;
            font-weight: bold;
            color: #084298;
            z-index: 1000;
            border-bottom: 2px solid #ccc;
        }}

        .chat-area {{
            margin-top: 100px;
            margin-bottom: 120px;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
            background: rgba(255,255,255,0.9);
            padding: 20px;
            border-radius: 20px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("hospital image.jpg")

# ===============================
# Sidebar
# ===============================
with st.sidebar:
    st.title("🏥 PRS Hospital")

    with st.expander("ℹ️ About"):
        st.write(
            "PRS Hospital, Trivandrum – 37+ years of excellence with modern healthcare facilities."
        )

    with st.expander("📞 Contact"):
        st.write("📍 Killipalam, Trivandrum")
        st.write("🚑 Emergency: +91 9497 247 365")

# ===============================
# Session State
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===============================
# Fixed Header
# ===============================
st.markdown(
    '<div class="header">🏥 PRS Hospital – Chatbot Assistant</div>',
    unsafe_allow_html=True
)

# ===============================
# Chat Messages (Scrollable)
# ===============================
st.markdown('<div class="chat-area">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# Chat Input (ALWAYS FIXED & STABLE)
# ===============================
user_input = st.chat_input("Type your message here...")

if user_input:
    # User message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Bot response
    reply = run_chatbot_query(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })
