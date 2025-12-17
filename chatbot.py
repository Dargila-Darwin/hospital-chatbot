# ===============================
# PRS HOSPITAL CHATBOT (BERT LOGIC UNTOUCHED)
# ===============================

import re
import pandas as pd
import torch
import joblib
from datetime import datetime
from transformers import BertTokenizer, BertForSequenceClassification
import gdown

# ===============================
# MODEL DOWNLOAD
# ===============================
file_id = "1-eUWEBYaDUoAySlAHkoIyIsIllinlu5Z"
url = f"https://drive.google.com/uc?id={file_id}"
output = "bert_doctor_classification/model.safetensors"
gdown.download(url, output, quiet=False)

# ===============================
# LOAD DATASET
# ===============================
df = pd.read_csv("Hospital_Information124.csv")

# Normalize text
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

def detect_intent(user_query):
    inputs = tokenizer(user_query, return_tensors="pt")
    outputs = model(**inputs)
    predicted_id = torch.argmax(outputs.logits).item()
    return label_encoder.inverse_transform([predicted_id])[0]

# ===============================
# HELPERS
# ===============================
SPECIALITY_SYNONYMS = {
    "cardiologist": ["cardio", "heart"],
    "ent": ["ear nose throat"],
    "neurologist": ["neuro", "brain"],
    "orthopaedician": ["ortho"],
}

DAY_SYNONYMS = {
    "monday": ["mon"], "tuesday": ["tue"], "wednesday": ["wed"],
    "thursday": ["thu"], "friday": ["fri"], "saturday": ["sat"], "sunday": ["sun"]
}
WEEKDAYS = list(DAY_SYNONYMS.keys())

# ===============================
# EXTRACTION
# ===============================
def extract_doctor_name(user_query):
    q = user_query.lower()
    for name in df["Doctor Name"].unique():
        if name.lower() in q:
            return name
    return None

def extract_day(user_query):
    q = user_query.lower()
    if "today" in q:
        return datetime.now().strftime("%A").lower()
    for day, syns in DAY_SYNONYMS.items():
        if day in q or any(s in q for s in syns):
            return day
    return None

def match_specialty(user_query):
    q = user_query.lower()
    for spec in df["Speciality"].unique():
        if spec.lower() in q:
            return spec
    for k, v in SPECIALITY_SYNONYMS.items():
        if k in q or any(s in q for s in v):
            return k
    return None

# ===============================
# AVAILABILITY
# ===============================
def is_available_on(day, txt):
    if not day:
        return True
    txt = txt.lower()
    if "all days" in txt:
        return True
    if "not available" in txt:
        return day not in txt
    return True

# ===============================
# RESPONSE BUILDERS (FIXED)
# ===============================
def list_all_doctors():
    seen = {}
    for _, row in df.iterrows():
        seen[row["Doctor Name"]] = row["Speciality"]
    return "\n".join([f"{k} - {v}" for k, v in seen.items()])


def list_doctors_by_specialty(specialty):
    rows = df[df["Speciality"].str.contains(specialty, case=False, na=False)]
    if rows.empty:
        return f"No {specialty} doctors found."

    doctors = {}
    for _, row in rows.iterrows():
        doctors[row["Doctor Name"]] = row["Consultation Time"]

    return "\n".join([f"{doc} - {time}" for doc, time in doctors.items()])


def availability_on_day_for_specialty(specialty, day):
    rows = df[df["Speciality"].str.contains(specialty, case=False, na=False)]
    lines = {}
    for _, row in rows.iterrows():
        if is_available_on(day, row["Available days"]):
            lines[row["Doctor Name"]] = row["Consultation Time"]
    if not lines:
        return f"No {specialty} doctors available on {day.capitalize()}."
    return "\n".join([f"{k} - {v}" for k, v in lines.items()])


def availability_on_day_for_doctor(name, day):
    row = df[df["Doctor Name"].str.contains(re.escape(name), case=False)]
    if row.empty:
        return "Doctor not found."
    ok = is_available_on(day, row.iloc[0]["Available days"])
    return f"{name} is {'available' if ok else 'not available'} on {day.capitalize()}."


def get_contact_block(name):
    row = df[df["Doctor Name"].str.contains(re.escape(name), case=False)]
    if row.empty:
        return "Doctor not found."
    r = row.iloc[0]
    return f"Contact: {r['Contact']} | Email: {r['Email']}"

# ===============================
# MAIN CHATBOT
# ===============================
def chatbot_response(user_query):
    intent = detect_intent(user_query)
    q = user_query.lower()

    doctor = extract_doctor_name(user_query)
    day = extract_day(user_query)
    specialty = match_specialty(user_query)

    if "all doctors" in q or "list doctors" in q:
        return list_all_doctors()

    if day and specialty:
        return availability_on_day_for_specialty(specialty, day)

    if day and doctor:
        return availability_on_day_for_doctor(doctor, day)

    if "contact" in q and doctor:
        return get_contact_block(doctor)

    if intent == "find_doctor" and specialty:
        return list_doctors_by_specialty(specialty)

    if intent == "doctor_availability" and doctor:
        row = df[df["Doctor Name"].str.contains(re.escape(doctor), case=False)]
        return f"{doctor} - {row.iloc[0]['Consultation Time']}"

    return "I can help you find doctors, timings, availability, and contact details."

# ===============================
# STREAMLIT HELPER
# ===============================
def run_chatbot_query(query):
    return chatbot_response(query)
