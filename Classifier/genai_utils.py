import os
import re
from dotenv import load_dotenv

load_dotenv()

KNOWN_TYPES = [
    "invoice", "contract", "report", "resume", "email",
    "notice", "letter", "application", "agreement", "receipt"
]


GEMINI_API_KEY = "AIzaSyCq_jk2ARXmk2V258LyelQT9bH9QVcJCZI"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
except Exception as e:
    print(f"Could not initialize Gemini: {e}")
    gemini_model = None


def local_fallback_classifier(text):
    text_lower = text.lower()
    if "invoice" in text_lower or "total amount" in text_lower:
        return "invoice"
    elif "resume" in text_lower or "curriculum vitae" in text_lower:
        return "resume"
    elif "agreement" in text_lower:
        return "agreement"
    elif "contract" in text_lower:
        return "contract"
    elif "report" in text_lower:
        return "report"
    elif "dear" in text_lower and "sincerely" in text_lower:
        return "letter"
    else:
        return "unknown"


def classify_document(document_text):
    prompt = f"""You are a document classifier. Classify this document into one of the following types:
Invoice, Contract, Report, Resume, Email, Notice, Letter, Application, Agreement, Receipt.

Document Content:
{document_text}

Only output the label."""


    if gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            label = response.text.strip().lower()
            if label in KNOWN_TYPES:
                return {
                    "document_type": label,
                    "confidence_score": "high",
                    "classification_by": "Gemini API"
                }
        except Exception as e:
            print(f" Gemini failed: {e}")

    # 2. Try Groq
    try:
        import openai
        openai.api_key = GROQ_API_KEY
        openai.base_url = "https://api.groq.com/openai/v1"

        chat_completion = openai.ChatCompletion.create(
            model="mixtral-8x7b-32768", 
            messages=[
                {"role": "system", "content": "You are a document classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        label = chat_completion.choices[0].message["content"].strip().lower()
        if label in KNOWN_TYPES:
            return {
                "document_type": label,
                "confidence_score": "medium",
                "classification_by": "Groq API"
            }
    except Exception as e:
        print(f"Groq failed: {e}")

   
    try:
        label = local_fallback_classifier(document_text)
        return {
            "document_type": label,
            "confidence_score": "low",
            "classification_by": "Local Fallback Classifier"
        }
    except Exception as e:
        return {
            "document_type": "unknown",
            "error": f"Local fallback failed: {e}"
        }

