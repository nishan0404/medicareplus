import joblib
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load model and columns at startup
model = joblib.load(os.path.join(BASE_DIR, 'symptom_model.pkl'))
symptom_columns = joblib.load(os.path.join(BASE_DIR, 'symptom_columns.pkl'))

# Disease to specialist mapping
DISEASE_SPECIALIST = {
    'Fungal infection': 'General Practice',
    'Allergy': 'General Practice',
    'GERD': 'General Practice',
    'Chronic cholestasis': 'General Practice',
    'Drug Reaction': 'General Practice',
    'Peptic ulcer diseae': 'General Practice',
    'AIDS': 'General Practice',
    'Diabetes': 'General Practice',
    'Gastroenteritis': 'General Practice',
    'Bronchial Asthma': 'General Practice',
    'Hypertension': 'Cardiology',
    'Migraine': 'Neurology',
    'Cervical spondylosis': 'Orthopaedics',
    'Paralysis (brain hemorrhage)': 'Neurology',
    'Jaundice': 'General Practice',
    'Malaria': 'General Practice',
    'Chicken pox': 'General Practice',
    'Dengue': 'General Practice',
    'Typhoid': 'General Practice',
    'hepatitis A': 'General Practice',
    'Hepatitis B': 'General Practice',
    'Hepatitis C': 'General Practice',
    'Hepatitis D': 'General Practice',
    'Hepatitis E': 'General Practice',
    'Alcoholic hepatitis': 'General Practice',
    'Tuberculosis': 'General Practice',
    'Common Cold': 'General Practice',
    'Pneumonia': 'General Practice',
    'Dimorphic hemmorhoids(piles)': 'General Practice',
    'Heart attack': 'Cardiology',
    'Varicose veins': 'General Practice',
    'Hypothyroidism': 'General Practice',
    'Hyperthyroidism': 'General Practice',
    'Hypoglycemia': 'General Practice',
    'Osteoarthristis': 'Orthopaedics',
    'Arthritis': 'Orthopaedics',
    '(vertigo) Paroymsal  Positional Vertigo': 'Neurology',
    'Acne': 'Dermatology',
    'Urinary tract infection': 'General Practice',
    'Psoriasis': 'Dermatology',
    'Impetigo': 'Dermatology',
}

# Red flag keywords for High urgency
RED_FLAG_KEYWORDS = [
    'chest pain', 'chest_pain', 'difficulty breathing',
    'breathlessness', 'unconscious', 'heart attack',
    'severe bleeding', 'stroke', 'paralysis',
    'loss of consciousness', 'sudden numbness'
]

# Disease urgency mapping
HIGH_URGENCY = [
    'Heart attack', 'Paralysis (brain hemorrhage)',
    'Hepatitis B', 'Tuberculosis', 'AIDS'
]
MEDIUM_URGENCY = [
    'Diabetes', 'Hypertension', 'Pneumonia',
    'Malaria', 'Dengue', 'Typhoid', 'Migraine'
]


def predict_disease(symptoms_list):
    """
    Takes a list of symptom strings and returns predictions.
    symptoms_list: list of symptom names e.g. ['itching', 'skin_rash']
    """
    # Create feature vector
    input_vector = np.zeros(len(symptom_columns))

    matched = 0
    for symptom in symptoms_list:
        symptom_clean = symptom.strip().lower().replace(' ', '_')
        if symptom_clean in symptom_columns:
            idx = symptom_columns.index(symptom_clean)
            input_vector[idx] = 1
            matched += 1

    if matched == 0:
        return None

    # Get predictions with probabilities
    input_vector = input_vector.reshape(1, -1)
    probabilities = model.predict_proba(input_vector)[0]
    classes = model.classes_

    # Get top 5 predictions
    top_indices = np.argsort(probabilities)[::-1][:5]
    predictions = []

    for idx in top_indices:
        prob = probabilities[idx]
        if prob > 0.01:  # Only show if > 1% confidence
            disease = classes[idx]
            predictions.append({
                'condition': disease,
                'confidence': round(float(prob) * 100, 1),
                'specialist': DISEASE_SPECIALIST.get(disease, 'General Practice')
            })

    return predictions


def classify_urgency(predictions, symptoms_list):
    """
    Classifies urgency as Low, Medium, or High.
    """
    # Check red flag symptoms first
    symptoms_text = ' '.join(symptoms_list).lower()
    for red_flag in RED_FLAG_KEYWORDS:
        if red_flag.lower() in symptoms_text:
            return 'High'

    if not predictions:
        return 'Medium'

    top_disease = predictions[0]['condition']

    if top_disease in HIGH_URGENCY:
        return 'High'
    elif top_disease in MEDIUM_URGENCY:
        return 'Medium'
    else:
        return 'Low'


def get_all_symptoms():
    """Returns all available symptoms for the checkbox list."""
    return sorted(symptom_columns)