import os
import sys
import joblib
from dotenv import load_dotenv
import google.generativeai as genai
from difflib import SequenceMatcher

# Add backend root for logger access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

log = logger.get_agent_logger("Classifier")

# Load environment variables
load_dotenv()
# Set your Gemini API key here
GEMINI_API_KEY = ""  # Replace with your actual API key
# Alternatively, you can still use environment variable as fallback
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY_HERE"

KNOWN_TYPES = [
    "Address Proof", "Advertisement", "Appointment Letter", "Balance Sheet", "Bank Statement", "Bill", "Boarding Pass",
    "Bonafide Certificate", "Brochure", "Business Pitch Deck", "Business Proposal", "Degree Certificate", "Event Ticket",
    "Experience Certificate", "ID Proof", "Income Statement", "Insurance Policy", "Invoice", "Lab Report", "Legal Contract",
    "Marksheet", "Medical Report", "Meeting Minutes", "Offer Letter", "Passport Copy", "Payslip", "Prescription",
    "Profit and Loss Statement", "Project Report", "Purchase Order (PO)", "Receipt", "Recommendation Letter",
    "Relieving Letter", "Rent Agreement", "Research Paper", "Resignation Letter", "Resume", "Sales order",
    "Tax Document", "Technical", "Train Ticket", "Travel Itinerary", "Visa Copy", "Whitepaper"
]

# Load Gemini
try:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
    log.info("✨ Gemini model loaded successfully.")
except Exception as e:
    log.error(f" Could not initialize Gemini: {e}")
    gemini_model = None

# Load local ML model and vectorizer
try:
    base_dir = os.path.dirname(__file__)
    classifier_model = joblib.load(os.path.join(base_dir, "document_classifier.pkl"))
    vectorizer = joblib.load(os.path.join(base_dir, "tfidf_vectorizer.pkl"))
    log.info(" Local ML model and vectorizer loaded successfully.")
except Exception as e:
    log.warning(f" Failed to load local ML model/vectorizer: {e}")
    classifier_model, vectorizer = None, None

def classify_document(document_text: str):
    gemini_label, gemini_similarity = None, 0.0
    local_label, local_confidence = None, 0.0

    # --- Gemini Classification ---
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

            # Match Gemini output to known labels
            best_match, best_ratio = None, 0.0
            for known in KNOWN_TYPES:
                ratio = SequenceMatcher(None, gemini_label_clean.lower(), known.lower()).ratio()
                if ratio > best_ratio:
                    best_match = known
                    best_ratio = ratio

            gemini_label = best_match
            gemini_similarity = best_ratio
            log.info(f"[Gemini ] Prediction: {gemini_label} (similarity: {round(gemini_similarity, 3)})")

        except Exception as e:
            log.error("[ Gemini error]", exc_info=True)
            gemini_label = None

    # --- Local ML Classification ---
    if classifier_model and vectorizer:
        try:
            vec = vectorizer.transform([document_text])
            
            # Check if model supports probability prediction
            if hasattr(classifier_model, 'predict_proba'):
                proba = classifier_model.predict_proba(vec)[0]
                idx = proba.argmax()
                local_label = classifier_model.classes_[idx]
                local_confidence = round(proba[idx], 3)
            else:
                # For LinearSVC, use decision_function for confidence
                prediction = classifier_model.predict(vec)[0]
                local_label = prediction
                
                # Get decision function scores for confidence approximation
                decision_scores = classifier_model.decision_function(vec)[0]
                if len(classifier_model.classes_) == 2:
                    # Binary classification
                    local_confidence = round(abs(decision_scores), 3)
                else:
                    # Multi-class classification - use max score
                    max_score = max(decision_scores)
                    # Normalize to 0-1 range (rough approximation)
                    local_confidence = round(min(1.0, max(0.0, (max_score + 1) / 2)), 3)
            
            log.info(f"[Local ML ] Prediction: {local_label} (confidence: {local_confidence})")
        except Exception as e:
            log.error("[ Local ML error]", exc_info=True)

    # --- Final Decision Logic ---
    if gemini_label and gemini_similarity >= 0.9:
        return {
            "document_type": gemini_label,
            "confidence": 0.95,
            "classification_by": "Gemini (trusted)"
        }
    elif local_label:
        boosted_confidence = max(0.7, round(local_confidence * 1, 2))
        return {
            "document_type": local_label,
            "confidence": boosted_confidence,
            "classification_by": "Local ML boosted"
        }
    else:
        return {
            "document_type": "other",
            "confidence": 0.0,
            "classification_by": "Fallback Error"
        }