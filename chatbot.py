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

def norm(s):
    return str(s).strip()

for col in [
    "Doctor Name", "Speciality", "Professional Degree",
    "Consultation Time", "Available days",
    "Contact", "Email", "Location"
]:
    df[col] = df[col].apply(norm)

# ===============================
# LOAD BERT (UNCHANGED ✅)
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
    "cardiologist": ["cardio", "heart", "cardiology"],
    "ent": ["ear nose throat", "otolaryngology"],
    "gastroenterologist": ["gastro", "digestive", "hepatology"],
    "gynecologist": ["gyn", "obg", "obstetrics", "fertility"],
    "nephrologist": ["kidney"],
    "neurologist": ["neuro", "brain", "stroke"],
    "urologist": ["urinary", "genito-urinary"],
    "pulmonologist": ["respiratory", "lungs", "tb"],
    "dermatologist": ["skin"],
    "ophthalmologist": ["eye"],
    "orthopaedician": ["ortho", "orthopedic"],
    "oncologist": ["cancer", "oncology"],
    "pathologist": ["pathology"],
    "radiologist": ["radiology"],
    "psychiatrist": ["mental health", "psych"],
    "psychologist": ["counseling"],
    "endocrinologist": ["endocrine", "hormone"],
    "general surgeon": ["surgery"],
    "paediatrician": ["paed", "child doctor"],
}

DAY_SYNONYMS = {
    "monday": ["mon"], "tuesday": ["tue"], "wednesday": ["wed"],
    "thursday": ["thu"], "friday": ["fri"], "saturday": ["sat"], "sunday": ["sun"]
}

COLUMN_ALIASES = {
    "Doctor Name": ["doctor name", "name"],
    "Speciality": ["speciality", "specialty", "specialisation", "specialization"],
    "Consultation Time": ["consultation time", "timings", "hours", "availability", "time"],
    "Available days": ["consultation days", "days", "available days", "availability days", "day"],
    "Contact": ["contact", "phone", "mobile", "number", "appointment", "book appointment", "contact details"],
    "Email": ["email", "mail"],
    "Location": ["location", "address", "hospital location"],
    "Professional Degree": ["degree", "qualification", "qualifications"],
}

def map_field_alias(user_query):
    q = user_query.lower()
    for col, aliases in COLUMN_ALIASES.items():
        if any(alias in q for alias in aliases):
            return col
    return None

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
# APPOINTMENT BOOKING
# ===============================
appointments_file = "appointments.csv"

try:
    pd.read_csv(appointments_file)
except FileNotFoundError:
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Day", "Time"]
    ).to_csv(appointments_file, index=False)

def book_appointment(doctor_name, patient_name, day, time_slot):
    row = df[df["Doctor Name"].str.contains(re.escape(doctor_name), case=False)]
    if row.empty:
        return "Doctor not found."

    # convert AM/PM → am/pm
    time_slot = time_slot.replace("AM","am").replace("PM","pm")

    new_row = pd.DataFrame([[doctor_name, patient_name, day.capitalize(), time_slot]],
                           columns=["Doctor Name", "Patient Name", "Day", "Time"])
    appt_df = pd.read_csv(appointments_file)
    appt_df = pd.concat([appt_df, new_row], ignore_index=True)
    appt_df.to_csv(appointments_file, index=False)
    return f"✅ Appointment confirmed with **{doctor_name}** on **{day.capitalize()}** at **{time_slot}**."

# ===============================
# RESPONSE BUILDERS
# ===============================
def list_all_doctors():
    seen = {}
    for _, row in df.iterrows():
        seen[row["Doctor Name"]] = row["Speciality"]
    return "\n".join(f"{k} - {v}" for k, v in seen.items())

def list_doctors_by_specialty(specialty):
    rows = df[df["Speciality"].str.contains(specialty, case=False, na=False)]
    doctors = {}
    for _, row in rows.iterrows():
        doctors[row["Doctor Name"]] = row["Consultation Time"].replace("AM","am").replace("PM","pm")
    return "\n".join(f"{k} - {v}" for k, v in doctors.items())

def availability_on_day_for_specialty(specialty, day):
    rows = df[df["Speciality"].str.contains(specialty, case=False)]
    doctors = {}
    for _, row in rows.iterrows():
        if is_available_on(day, row["Available days"]):
            doctors[row["Doctor Name"]] = row["Consultation Time"].replace("AM","am").replace("PM","pm")
    return "\n".join(f"{k} - {v}" for k, v in doctors.items())

def availability_on_day_for_doctor(name, day):
    row = df[df["Doctor Name"].str.contains(re.escape(name), case=False)]
    ok = is_available_on(day, row.iloc[0]["Available days"])
    return f"{name} is {'available' if ok else 'not available'} on {day.capitalize()}."

def get_contact_block(name):
    row = df[df["Doctor Name"].str.contains(re.escape(name), case=False)]
    r = row.iloc[0]
    return f"Contact: {r['Contact']} | Email: {r['Email']}"

# ===============================
# MAIN CHATBOT
# ===============================
def chatbot_response(user_query):
    intent = detect_intent(user_query)

    doctor = extract_doctor_name(user_query)
    day = extract_day(user_query)
    specialty = match_specialty(user_query)
    requested_field = map_field_alias(user_query)

    # Hospital location query
    if requested_field == "Location":
        return "📍 PRS Hospital, Killipalam, Trivandrum"

    # Doctor-specific field queries
    if doctor and requested_field:
        row = df[df["Doctor Name"]==doctor].iloc[0]
        if requested_field == "Speciality":
            return f"{doctor} speciality: {row['Speciality']}"
        elif requested_field == "Professional Degree":
            return f"{doctor} degree: {row['Professional Degree']}"
        elif requested_field == "Contact":
            return f"Contact: {row['Contact']} | Email: {row['Email']}"
        elif requested_field == "Consultation Time":
            return f"{doctor} timings: {row['Consultation Time'].replace('AM','am').replace('PM','pm')}"
        elif requested_field == "Available days":
            return f"{doctor} available days: {row['Available days']}"

    # Day + Specialty / Doctor availability
    if day and specialty:
        return availability_on_day_for_specialty(specialty, day)
    if day and doctor:
        return availability_on_day_for_doctor(doctor, day)

    # List all doctors
    if "all doctors" in user_query.lower():
        return list_all_doctors()

    # Find doctor by specialty
    if intent == "find_doctor" and specialty:
        return list_doctors_by_specialty(specialty)

    # Doctor availability intent
    if intent == "doctor_availability" and doctor:
        row = df[df["Doctor Name"]==doctor].iloc[0]
        return f"{doctor} - {row['Consultation Time'].replace('AM','am').replace('PM','pm')}"

    return "I can help you find doctors, availability, contact details, degree, timings, hospital location, and book appointments."

# ===============================
# STREAMLIT HELPER
# ===============================
def run_chatbot_query(query):
    return chatbot_response(query)
