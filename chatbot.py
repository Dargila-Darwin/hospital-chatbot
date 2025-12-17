# chatbot.py (enhanced smart queries)
import re
import os
import pandas as pd
import torch
import joblib
from datetime import datetime, timedelta, date, time
from transformers import BertTokenizer, BertForSequenceClassification
import gdown

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
# SPECIALITY & DAY SYNONYMS
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
    "thursday": ["thu"], "friday": ["fri"],
    "saturday": ["sat"], "sunday": ["sun"]
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

# ===============================
# MODEL SETUP
# ===============================
model_path = "./bert_doctor_classification"
os.makedirs(model_path, exist_ok=True)
model_file = os.path.join(model_path, "model.safetensors")

if not os.path.exists(model_file):
    print("⬇️ Downloading BERT model...")
    file_id = "1-eUWEBYaDUoAySlAHkoIyIsIllinlu5Z"
    gdown.download(f"https://drive.google.com/uc?id={file_id}", model_file, quiet=False)

tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
label_encoder = joblib.load(os.path.join(model_path, "label_encoder.pkl"))

def detect_intent(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    pred = torch.argmax(outputs.logits).item()
    return label_encoder.inverse_transform([pred])[0]

# ===============================
# EXTRACTION HELPERS
# ===============================
def extract_doctor_name(text):
    text = text.lower()
    for name in df["Doctor Name"].unique():
        if name.lower() in text:
            return name
    return None

def extract_speciality(text):
    text = text.lower()
    for spec, keywords in SPECIALITY_SYNONYMS.items():
        if spec in text:
            return spec
        for kw in keywords:
            if kw in text:
                return spec
    return None

def extract_day(text):
    text = text.lower()
    for day, shorts in DAY_SYNONYMS.items():
        if day in text:
            return day
        for s in shorts:
            if s in text:
                return day
    if "today" in text:
        return datetime.now().strftime("%A").lower()
    elif "tomorrow" in text:
        return (datetime.now() + timedelta(days=1)).strftime("%A").lower()
    elif "yesterday" in text:
        return (datetime.now() - timedelta(days=1)).strftime("%A").lower()
    return None

def extract_column(text):
    text = text.lower()
    for col, aliases in COLUMN_ALIASES.items():
        for a in aliases:
            if a in text:
                return col
    return None

# ===============================
# SMART QUERY FUNCTION
# ===============================
def run_chatbot_query(text):
    text_lower = text.lower()
    doctor = extract_doctor_name(text)
    speciality = extract_speciality(text)
    day = extract_day(text)
    column = extract_column(text)

    # 1️⃣ Filter by speciality + day
    if speciality:
        matches = df[df["Speciality"].str.lower().str.contains(speciality)]
        if day:
            matches = matches[matches["Available days"].str.lower().str.contains(day)]
        if matches.empty:
            return f"⚠️ No {speciality} available on {day if day else 'any day'}."
        return "\n".join(f"👨‍⚕️ {r['Doctor Name']} ({r['Speciality']}) - {r['Available days']}" 
                         for _, r in matches.iterrows())

    # 2️⃣ Doctor + column query
    if doctor and column:
        value = df[df["Doctor Name"] == doctor].iloc[0][column]
        return f"{doctor} {column.lower()}: {value}"

    # 3️⃣ All doctors
    if "all doctors" in text_lower:
        return "\n".join(f"{r['Doctor Name']} ({r['Speciality']}) - {r['Available days']}" 
                         for _, r in df.drop_duplicates("Doctor Name").iterrows())

    # 4️⃣ Hospital location
    if "hospital location" in text_lower or "location" in text_lower:
        return "📍 PRS Hospital, Killipalam, Thiruvananthapuram"

    # 5️⃣ Default fallback
    return ("🤖 I can help with:\n"
            "• Doctor details by name or speciality\n"
            "• Doctor qualification / degree\n"
            "• Consultation timings & availability\n"
            "• Contact details\n"
            "• Hospital location\n"
            "• Booking appointments")
