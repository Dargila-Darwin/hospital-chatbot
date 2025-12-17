# ===============================
# PRS HOSPITAL CHATBOT (BERT UNTOUCHED)
# ===============================

import re
import pandas as pd
import torch
import joblib
from datetime import datetime, date
from transformers import BertTokenizer, BertForSequenceClassification

# ===============================
# LOAD DATA
# ===============================
df = pd.read_csv("Hospital_Information124.csv")

def norm(s):
    return str(s).strip()

for col in df.columns:
    df[col] = df[col].apply(norm)

# ===============================
# LOAD BERT
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
def extract_doctor_name(q):
    for d in df["Doctor Name"].unique():
        if d.lower() in q.lower():
            return d
    return None

def extract_day(q):
    if "today" in q.lower():
        return datetime.now().strftime("%A")
    for d in ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]:
        if d in q.lower():
            return d.capitalize()
    return None

# ===============================
# APPOINTMENT BOOKING
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

def book_appointment(doctor, patient, appt_date, time_slot):
    appt_df = pd.read_csv(appointments_file)

    time_slot = time_slot.lower()

    # 🔒 Slot limit
    existing = appt_df[
        (appt_df["Doctor Name"] == doctor) &
        (appt_df["Date"] == appt_date) &
        (appt_df["Time"] == time_slot)
    ]

    if len(existing) >= MAX_SLOTS_PER_DOCTOR:
        return f"⛔ Slot full for **{doctor}** on **{appt_date} {time_slot}**."

    new_row = pd.DataFrame([[doctor, patient, appt_date, time_slot]],
        columns=appt_df.columns)

    appt_df = pd.concat([appt_df, new_row], ignore_index=True)
    appt_df.to_csv(appointments_file, index=False)

    return (
        f"✅ Appointment confirmed\n"
        f"Doctor: {doctor}\n"
        f"Date: {appt_date}\n"
        f"Time: {time_slot}"
    )

# ===============================
# RESPONSE LOGIC
# ===============================
def run_chatbot_query(q):
    doctor = extract_doctor_name(q)
    day = extract_day(q)

    if "hospital location" in q.lower():
        return "📍 PRS Hospital, Killipalam, Thiruvananthapuram"

    if doctor and "speciality" in q.lower():
        row = df[df["Doctor Name"] == doctor].iloc[0]
        return f"{doctor} speciality: {row['Speciality']}"

    if doctor and "degree" in q.lower():
        row = df[df["Doctor Name"] == doctor].iloc[0]
        return f"{doctor} degree: {row['Professional Degree']}"

    if doctor and "timing" in q.lower():
        row = df[df["Doctor Name"] == doctor].iloc[0]
        return f"{doctor} - {row['Consultation Time'].replace('AM','am').replace('PM','pm')}"

    if "all doctors" in q.lower():
        return "\n".join(
            f"{r['Doctor Name']} - {r['Speciality']}"
            for _, r in df.iterrows()
        )

    return (
        "I can help you find doctors, availability, contact details, "
        "degree, timings, hospital location, and book appointments."
    )
