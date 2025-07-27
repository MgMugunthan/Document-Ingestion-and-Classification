import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def classify_document(document_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a document classifier. You label documents as Invoice, Contract, Report, Resume, Email, etc."},
                {"role": "user", "content": f"Classify this document:\n\n{document_text}"}
            ],
            temperature=0.3
        )

        label = response['choices'][0]['message']['content'].strip()

        return {
            "document_type": label,
            "confidence_score": "high",
            "classification_by": "OpenAI GPT"
        }

    except Exception as e:
        print(f" Error during classification: {e}")
        return {
            "document_type": "Unknown",
            "error": str(e)
        }
