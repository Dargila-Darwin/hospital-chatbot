# chatbot.py
import re
import pandas as pd
import torch
import joblib
from datetime import datetime, date, time
from transformers import BertTokenizer, BertForSequenceClassification

# ===============================
# LOAD DATASET
# ===============================
df = pd.read_csv("Hospital_Information124.csv")

def norm(s):
    return str(s).strip()

for col in [
    "Doctor Name", "Speciality", "Professional Degree",
    "Consultation Time", "Available days",
    "Contact", "Email", "Location"
]:
    df[col] = df[col].apply(norm)

# ===============================
# LOAD BERT (UNCHANGED)
# ===============================
model_path = "./bert_doctor_classification"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
label_encoder = joblib.load(model_path + "/label_encoder.pkl")

def detect_intent(text):
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    pred = torch.argmax(outputs.logits).item()
    return label_encoder.inverse_transform([pred])[0]

# ===============================
# HELPERS
# ===============================
def extract_doctor_name(text):
    for name in df["Doctor Name"].unique():
        if name.lower() in text.lower():
            return name
    return None

def extract_day(text):
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for d in days:
        if d in text.lower():
            return d
    if "today" in text.lower():
        return datetime.now().strftime("%A").lower()
    return None

# ===============================
# APPOINTMENT LOGIC (ENHANCED)
# ===============================
appointments_file = "appointments.csv"
MAX_SLOTS_PER_DOCTOR = 5

try:
    appt_df = pd.read_csv(appointments_file)
except FileNotFoundError:
    appt_df = pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Date", "Time"]
    )
    appt_df.to_csv(appointments_file, index=False)

def is_past_datetime(appt_date, appt_time):
    now = datetime.now()
    return datetime.combine(appt_date, appt_time) <= now

def book_appointment(doctor, patient, appt_date, time_slot):
    appt_df = pd.read_csv(appointments_file)

    time_slot = time_slot.lower()
    appt_time = datetime.strptime(time_slot, "%I%p").time()

    # ⛔ Past date/time check
    if is_past_datetime(appt_date, appt_time):
        return "⛔ Cannot book past date or time."

    # 🔒 Slot limit
    existing = appt_df[
        (appt_df["Doctor Name"] == doctor) &
        (appt_df["Date"] == str(appt_date)) &
        (appt_df["Time"] == time_slot)
    ]

    if len(existing) >= MAX_SLOTS_PER_DOCTOR:
        return f"⛔ Slot full for **{doctor}** at **{time_slot}**."

    new_row = pd.DataFrame([[doctor, patient, appt_date, time_slot]],
                           columns=appt_df.columns)
    appt_df = pd.concat([appt_df, new_row], ignore_index=True)
    appt_df.to_csv(appointments_file, index=False)

    return (
        f"✅ Appointment confirmed\n"
        f"👨‍⚕️ Doctor: {doctor}\n"
        f"📅 Date: {appt_date}\n"
        f"⏰ Time: {time_slot}"
    )

# ===============================
# RESPONSES
# ===============================
def list_all_doctors():
    return "\n".join(
        f"{row['Doctor Name']} - {row['Speciality']}"
        for _, row in df.drop_duplicates("Doctor Name").iterrows()
    )

def run_chatbot_query(text):
    intent = detect_intent(text)
    doctor = extract_doctor_name(text)

    if "all doctors" in text.lower():
        return list_all_doctors()

    if doctor and "speciality" in text.lower():
        row = df[df["Doctor Name"] == doctor].iloc[0]
        return f"{doctor} speciality: {row['Speciality']}"

    if doctor and "degree" in text.lower():
        row = df[df["Doctor Name"] == doctor].iloc[0]
        return f"{doctor} degree: {row['Professional Degree']}"

    if "hospital location" in text.lower():
        return "📍 PRS Hospital, Killipalam, Thiruvananthapuram"

    return (
        "I can help you find doctors, availability, degree, "
        "contact details, hospital location, and book appointments."
    )
