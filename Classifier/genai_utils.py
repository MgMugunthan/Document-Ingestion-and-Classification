import os
from dotenv import load_dotenv

load_dotenv()

provider = os.getenv("USE_PROVIDER", "gemini").lower()

if provider == "gemini":
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("models/gemini-1.5-flash")
elif provider == "groq":
    from groq import Groq
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
else:
    raise ValueError("Invalid provider. Choose 'gemini' or 'groq'.")

def classify_document(document_text):
    try:
        prompt = f"""You are a document classifier. Classify this document into one of the following types: 
        Invoice, Contract, Report, Resume, Email, Notice, Letter, Application, Agreement, Receipt.

        Document Content:
        {document_text}

        Only output the label."""

        if provider == "gemini":
            response = model.generate_content(prompt)
            label = response.text.strip()

        elif provider == "groq":
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a document classifier."},
                    {"role": "user", "content": prompt}
                ],
                model="mixtral-8x7b-32768",  # or `llama3-70b-8192` or `gemma-7b-it`
                temperature=0.3
            )
            label = response.choices[0].message.content.strip()

        return {
            "document_type": label,
            "confidence_score": "high",
            "classification_by": provider.title()
        }

    except Exception as e:
        print(f"{provider.title()} error: {e}")
        return {
            "document_type": "Unknown",
            "error": str(e)
        }
