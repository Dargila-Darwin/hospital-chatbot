# ===============================
# PRS HOSPITAL CHATBOT (FINAL – CORRECT)
# BERT LOGIC UNTOUCHED ✅
# ===============================

import re
import os
import pandas as pd
import torch
import joblib
from datetime import datetime, timedelta
from transformers import BertTokenizer, BertForSequenceClassification
import gdown

# ===============================

# 🔴 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPOINTMENTS_FILE = os.path.join(BASE_DIR, "appointments.csv")

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
    inputs = tokenizer(query, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    pred = torch.argmax(outputs.logits).item()
    return label_encoder.inverse_transform([pred])[0]

# ===============================
# CONSTANTS
# ===============================
SPECIALITY_SYNONYMS = {
    "cardiologist": ["cardio", "heart", "cardiology", "interventional cardiologist", "chief cardiologist", "caardio"],
    "ent": ["ear nose throat", "otolaryngology", "laryngology", "phonosurgery", "vertigo"],
    "gastroenterologist": ["gastro", "digestive", "hepatology", "pediatric gastroenterology"],
    "gynecologist": ["gyn", "obg", "obstetrics", "fertility"],
    "nephrologist": ["kidney"],
    "neurologist": ["neuro", "brain", "neurovascular", "stroke"],
    "urologist": ["urinary", "genito-urinary"],
    "pulmonologist": ["respiratory", "lungs", "tb"],
    "dermatologist": ["skin"],
    "ophthalmologist": ["eye"],
    "orthopaedician": ["ortho", "orthopedic", "arthroscopy"],
    "oncologist": ["cancer", "medical oncology", "surgical oncology", "clinical oncology"],
    "pathologist": ["pathology"],
    "radiologist": ["radiology", "radiodiagnosis", "interventional radiology"],
    "psychiatrist": ["mental health", "psych","Psychiatrist"],
    "psychologist": ["counseling"],
    "endocrinologist": ["endocrine", "hormone"],
    "general surgeon": ["gen surg", "surgery"],
    "paediatrician": ["kids doctor", "paed", "pediatrician", "child doctor"],

}

DAY_SYNONYMS = {
    "monday": ["mon"], "tuesday": ["tue"],
    "wednesday": ["wed"], "thursday": ["thu"],
    "friday": ["fri"], "saturday": ["sat"],
    "sunday": ["sun"]
}

COLUMN_ALIASES = {
    "Professional Degree": ["degree", "qualification"],
    "Contact": ["contact", "phone", "mobile"],
    "Location": ["location", "address"],
    "Consultation Time": ["timing", "time", "hours"],
}

# ===============================
# EXTRACTION HELPERS
# ===============================
def extract_doctor_name(text):
    t = text.lower()
    for name in df["Doctor Name"].unique():
        if name.lower() in t:
            return name
    return None

def extract_day(text):
    t = text.lower()
    if "today" in t:
        return datetime.now().strftime("%A").lower()
    if "tomorrow" in t:
        return (datetime.now() + timedelta(days=1)).strftime("%A").lower()
    for d, syns in DAY_SYNONYMS.items():
        if d in t or any(s in t for s in syns):
            return d
    return None

def match_specialty(text):
    t = text.lower()
    for spec in df["Speciality"].unique():
        if spec.lower() in t:
            return spec
    for k, v in SPECIALITY_SYNONYMS.items():
        if k in t or any(s in t for s in v):
            return k
    return None

def map_field(text):
    t = text.lower()
    for col, aliases in COLUMN_ALIASES.items():
        if any(a in t for a in aliases):
            return col
    return None

# ===============================
# AVAILABILITY LOGIC (CORRECT)
# ===============================
def is_available_on(day, available_text):
    if not day:
        return True
    txt = available_text.lower()
    if "all days" in txt:
        return True
    if "not available" in txt:
        return day not in txt
    return True

# ===============================
# TIME PARSING (ROBUST)
# ===============================
def parse_time(t):
    """
    Converts a string like '9 am', '9:30AM', '10.30AM', '2 PM' into datetime.time
    """
    if not t:
        return None
    t = t.replace(".", ":").strip().lower().replace(" ", "")  # remove spaces and dots
    for fmt in ("%I:%M%p", "%I%p"):
        try:
            return datetime.strptime(t, fmt).time()
        except:
            continue
    return None


#def is_time_within_slot(consult_time, booking_time):
 #   consult_time = consult_time.replace("–", "-")
  #  start, end = consult_time.split("-")
   # return parse_time(start) <= booking_time <= parse_time(end)
##############################################################
def is_time_within_slot(consult_time, booking_time):
    """
    Checks if the booking_time falls within the consult_time slot.
    Handles formats like '9AM-1PM', '10.30AM to 2PM', '9 am to 2 pm'
    """
    if not consult_time or booking_time is None:
        return False

    consult_time = str(consult_time).lower().replace("–", "-").replace(" to ", "-").strip()

    if "-" not in consult_time:
        return False  # invalid format

    start_str, end_str = consult_time.split("-")
    start = parse_time(start_str.strip())
    end = parse_time(end_str.strip())

    if start is None or end is None:
        return False

    return start <= booking_time < end

def is_past_time(day, booking_time):
    today = datetime.now()
    if day.lower() != today.strftime("%A").lower():
        return False
    return booking_time <= today.time()




# ===============================
# APPOINTMENT BOOKING
# ===============================
#appointments_file = "appointments.csv"
if not os.path.exists(APPOINTMENTS_FILE):
    pd.DataFrame(
        columns=["Doctor Name", "Patient Name", "Day", "Time"]
    ).to_csv(APPOINTMENTS_FILE, index=False)


def book_appointment(doctor, patient, day, time_str):
    row = df[df["Doctor Name"].str.lower() == doctor.lower()]

    if row.empty:
        return "❌ Doctor not found."

    row = row.iloc[0]

    if not is_available_on(day, row["Available days"]):
        return f"❌ {doctor} is not available on {day.capitalize()}."

    booking_time = parse_time(time_str)
    if booking_time is None:
        return "❌ Invalid time format (use 10AM, 3PM)."

    # 🔴 NEW CHECK (CRITICAL)
    if is_past_time(day, booking_time):
        return "❌ You cannot book an appointment for a past time today."

    if not is_time_within_slot(row["Consultation Time"], booking_time):
        return f"❌ Outside consultation hours ({row['Consultation Time']})."

    appt_df = pd.read_csv(APPOINTMENTS_FILE)

    appt_df.loc[len(appt_df)] =  {
    "Doctor Name": doctor,
    "Patient Name": patient,
    "Day": day.capitalize(),
    "Time": time_str.upper()
}
    appt_df.to_csv(APPOINTMENTS_FILE, index=False)
    print("Appointments CSV saved at:", APPOINTMENTS_FILE)




    return f"✅ Appointment confirmed with **{doctor}** on **{day.capitalize()}** at **{time_str.upper()}**."

# ===============================
# RESPONSE BUILDERS
# ===============================
def availability_on_day_for_specialty(spec, day):
    rows = df[df["Speciality"].str.lower().str.contains(spec.lower(), na=False)]
    result = []
    for _, r in rows.iterrows():
        if is_available_on(day, r["Available days"]):
            result.append(
                f"👨⚕️ {r['Doctor Name']} ({r['Speciality']}) – {r['Consultation Time']}"
            )
    return "\n".join(result) if result else f"⚠️ No {spec} available on {day.capitalize()}."

# ===============================
# MAIN CHATBOT LOGIC
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
        if field == "Contact":
            return f"📞 {row['Contact']}\n📧 {row['Email']}"
        return f"{doctor} {field.lower()}: {row[field]}"

    if day and specialty:
        return availability_on_day_for_specialty(specialty, day)

    if intent == "find_doctor" and specialty:
        today = datetime.now().strftime("%A").lower()
        return availability_on_day_for_specialty(specialty, today)

       
    if intent == "book_appointment" and doctor and day:
        time_match = re.search(r"\b(\d{1,2}(:\d{2})?\s*(am|pm))\b", query, re.I)
        if not time_match:
            return "❌ Please specify a time (example: 10AM or 4:30PM)"

        time_str = time_match.group(1)
        patient = "Guest"  # you can improve later

        return book_appointment(doctor, patient, day, time_str)

    return (
        "🤖 I can help with:\n"
        "• Doctor availability (today / tomorrow / specific day)\n"
        "• Doctor details & qualifications\n"
        "• Appointment booking\n"
        "• Contact & hospital location"
    )

# ===============================
# STREAMLIT ENTRY
# ===============================
def run_chatbot_query(query):
    return chatbot_response(query)

