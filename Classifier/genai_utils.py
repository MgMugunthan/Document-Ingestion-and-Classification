import os
import joblib
from dotenv import load_dotenv
import google.generativeai as genai
from difflib import SequenceMatcher
import uuid
import sys
from datetime import datetime
import logging
import json
from colorama import Fore, Style, init
# Load environment variables
load_dotenv()

GEMINI_API_KEY ="AIzaSyCAOjqHYGiEQSEzvgywQubfm-pc9Q9YXUc"

KNOWN_TYPES = [ "Address Proof", "Advertisement", "Appointment Letter", "Balance Sheet", "Bank Statement", "Bill", "Boarding Pass", "Bonafide Certificate", "Brochure", "Business Pitch Deck", "Business Proposal", "Degree Certificate", "Event Ticket", "Experience Certificate", "ID Proof", "Income Statement", "Insurance Policy", "Invoice", "Lab Report", "Legal Contract", "Marksheet", "Medical Report", "Meeting Minutes", "Offer Letter", "Passport Copy", "Payslip", "Prescription", "Profit and Loss Statement", "Project Report", "Purchase Order (PO)", "Receipt", "Recommendation Letter", "Relieving Letter", "Rent Agreement", "Research Paper", "Resignation Letter", "Resume", "Sales order", "Tax Document", "Technical", "Train Ticket", "Travel Itinerary", "Visa Copy", "Whitepaper"]

# Load Gemini model
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
    print("✨ Gemini model loaded.")
except Exception as e:
    print(f"❌ Could not initialize Gemini: {e}")
    gemini_model = None

# Load local ML model and vectorizer
try:
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, "document_classifier.pkl")
    vectorizer_path = os.path.join(base_dir, "tfidf_vectorizer.pkl")

    classifier_model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    print("🧠 Local ML model and vectorizer loaded.")

except Exception as e:
    print(f"⚠️ Failed to load local ML model/vectorizer: {e}")
    classifier_model = None
    vectorizer = None
def is_content_trustworthy(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    word_count = len(text.split())
    unique_word_ratio = len(set(text.split())) / (word_count + 1e-6)

    if len(lines) < 5:
        return False  # too few lines
    if word_count < 30:
        return False  # too little content
    if unique_word_ratio < 0.3:
        return False  # spammy / repetitive
    return True

def classify_document(document_text: str):
    """
    Classifies the document using both Gemini and local ML model.
    Returns: dict with document_type, confidence (0.0 to 1.0), and classification_by.
    """
    gemini_label, gemini_similarity = None, 0.0
    local_label, local_confidence = None, 0.0
    classification_by = "Unknown"

    # Step 1: Run Gemini
    if gemini_model:
        try:
            prompt = f"""
You're an expert document classifier. Choose one of:
{', '.join(KNOWN_TYPES)}

Given the document below, classify its type.

Document:
\"\"\"{document_text}\"\"\"

Respond with only one type in lowercase, like: resume
"""
            gemini_response = gemini_model.generate_content(prompt)
            raw_response = gemini_response.text.strip().split("\n")[0]
            gemini_label_clean = raw_response.split(":")[-1].strip().title()

            # Find best match in known types
            best_match, best_ratio = None, 0.0
            for known in KNOWN_TYPES:
                ratio = SequenceMatcher(None, gemini_label_clean.lower(), known.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = known

            gemini_label = best_match
            gemini_similarity = best_ratio

            print(f"[Gemini 🔍] Prediction: {gemini_label} (similarity: {round(gemini_similarity, 3)})")

        except Exception as e:
            print(f"[⚠️ Gemini error] {e}")
            gemini_label = None

    # Step 2: Run local ML model
    if classifier_model and vectorizer:
        try:
            vec = vectorizer.transform([document_text])
            proba = classifier_model.predict_proba(vec)[0]
            idx = proba.argmax()
            local_label = classifier_model.classes_[idx]
            local_confidence = round(proba[idx], 3)
            print(f"[Local ML 🤖] Prediction: {local_label} (confidence: {local_confidence})")

        except Exception as e:
            print(f"[⚠️ Local ML error] {e}")
            local_label, local_confidence = None, 0.0

    # Step 3: Final Decision Logic
    if gemini_label and gemini_similarity >= 0.9:
        return {
            "document_type": gemini_label,
            "confidence": 0.95,
            "classification_by": "Gemini (trusted)"
        }
    elif local_label:
        return {
            "document_type": local_label,
            "confidence": local_confidence,
            "classification_by": "Local ML fallback"
        }
    else:
        return {
            "document_type": "other",
            "confidence": 0.0,
            "classification_by": "Fallback Error"
        }
