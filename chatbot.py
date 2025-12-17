# ===============================
# PRS HOSPITAL CHATBOT (FINAL)
# BERT LOGIC UNTOUCHED ✅
# ===============================

import re
import pandas as pd
import torch
import joblib
from datetime import datetime, time
from transformers import BertTokenizer, BertForSequenceClassification
import gdown
import os

# ===============================
# MODEL DOWNLOAD
# ===============================
model_path = "./bert_doctor_classification"
os.makedirs(model_path, exist_ok=True)

model_file = os.path.join(model_path, "model.safetensors")
if not os.path.exists(model_file):
    file_id = "1-eUWEBYaDUoAySlAHkoIyIsIllinlu5Z"
    gdown.download(f"https://drive.google.com/uc?id={file_id}", model_file, quiet=False)

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
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
label_encoder = joblib.load(os.path.join(model_path, "label_encoder.pkl"))

def detect_intent(query):
    inputs = tokenizer(query, return_tensors="pt")
    outputs = model(**inputs)
    pred = torch.argmax(outputs.logits).item()
    return label_encoder.inverse_transform([pred])[0]

# ===============================
# CONSTANTS
# ===============================
SPECIALITY_SYNONYMS = {
    "cardiologist": ["heart", "cardio", "cardiology"],
    "ent": ["ear nose throat"],
    "neurologist": ["brain", "neuro"],
}

DAY_SYNONYMS = {
    "monday": ["mon"], "tuesday": ["tue"], "wednesday": ["wed"],
    "thursday": ["thu"], "friday": ["fri"],
    "saturday": ["sat"], "sunday": ["sun"]
}

COLUMN_ALIASES = {
    "Professional Degree": ["degree", "qualification"],
    "Contact": ["contact", "phone"],
    "Location": ["location", "address"],
    "Consultation Time": ["timing", "time"],
}

# ===============================
# EXTRACTION HELPERS
# ===============================
def extract_doctor_name(text):
    text = text.lower()
    for name in df["Doctor Name"].unique():
        if name.lower() in text:
            return name
    return None

def extract_day(text):
    text = text.lower()
    if "today" in text:
        return datetime.now().strftime("%A").lower()
    if "tomorrow" in text:
        return (datetime.now().replace(day=datetime.now().day + 1)).strftime("%A").lower()
    for d, syn in DAY_SYNONYMS.items():
        if d in text or any(s in text for s in syn):
            return d
    return None

def match_specialty(text):
    text = text.lower()
    for spec in df["Speciality"].unique():
        if spec.lower() in text:
            return spec
    for k, v in SPECIALITY_SYNONYMS.items():
        if k in text or any(s in text for s in v):
            return k
    return None

def map_field(text):
    text = text.lower()
    for col, aliases in COLUMN_ALIASES.items():
        if any(a in text for a in aliases):
            return col
    return None

# ===============================
# AVAILABILITY CHECK
# ===============================
def is_available_on(day, available_text):
    if not day:
        return True
    available_text = available_text.lower()
    if "all days" in available_text:
        return True
    if "not available" in available_text:
        return day not in available_text
    return True

# ===============================
# TIME PARSING
# ===============================
def parse_time(t):
    return datetime.strptime(t.strip(), "%I%p").time()

def is_time_within_slot(consult_time, booking_time):
    start, end = consult_time.split("-")
    start_t = parse_time(start.replace(" ", ""))
    end_t = parse_time(end.replace(" ", ""))
    return start_t <= booking_time <= end_t

# ===============================
# APPOINTMENT BOOKING (VALIDATED)
# ===============================
appointments_file = "appointments.csv"

if not os.path.exists(appointments_file):
    pd.DataFrame(columns=["Doctor", "Patient", "Day", "Time"]).to_csv(appointments_file, index=False)

def book_appointment(doctor, patient, day, time_str):
    row = df[df["Doctor Name"].str.contains(re.escape(doctor), case=False)]

    if row.empty:
        return "❌ Doctor not found."

    row = row.iloc[0]

    # Day validation
    if not is_available_on(day, row["Available days"]):
        return f"❌ {doctor} is NOT available on {day.capitalize()}."

    # Time validation
    try:
        booking_time = datetime.strptime(time_str.lower(), "%I%p").time()
    except:
        return "❌ Invalid time format. Use 10AM, 3PM, etc."

    if not is_time_within_slot(row["Consultation Time"], booking_time):
        return f"❌ Booking time outside consultation hours ({row['Consultation Time']})."

    # Save appointment
    appt_df = pd.read_csv(appointments_file)
    appt_df.loc[len(appt_df)] = [doctor, patient, day.capitalize(), time_str.upper()]
    appt_df.to_csv(appointments_file, index=False)

    return f"✅ Appointment confirmed with **{doctor}** on **{day.capitalize()}** at **{time_str.upper()}**."

# ===============================
# RESPONSE BUILDERS
# ===============================
def availability_on_day_for_specialty(spec, day):
    rows = df[df["Speciality"].str.contains(spec, case=False)]
    result = []
    for _, r in rows.iterrows():
        if is_available_on(day, r["Available days"]):
            result.append(
                f"👨‍⚕️ {r['Doctor Name']} ({r['Speciality']}) - {r['Consultation Time']}"
            )
    return "\n".join(result) if result else f"⚠️ No {spec} available on {day.capitalize()}."

# ===============================
# MAIN CHATBOT
# ===============================
def chatbot_response(query):
    intent = detect_intent(query)

    doctor = extract_doctor_name(query)
    day = extract_day(query)
    specialty = match_specialty(query)
    field = map_field(query)

    if field == "Location":
        return "📍 PRS Hospital, Killipalam, Thiruvananthapuram"

    if doctor and field:
        row = df[df["Doctor Name"] == doctor].iloc[0]
        return f"{doctor} {field.lower()}: {row[field]}"

    if day and specialty:
        return availability_on_day_for_specialty(specialty, day)

    if intent == "find_doctor" and specialty:
        return availability_on_day_for_specialty(specialty, datetime.now().strftime("%A").lower())

    return "🤖 I can help with doctors, availability, booking, degree, contact, and hospital location."

# ===============================
# STREAMLIT ENTRY
# ===============================
def run_chatbot_query(query):
    return chatbot_response(query)
