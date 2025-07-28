import google.generativeai as genai
import json
from config import GOOGLE_API_KEY, GEMINI_MODEL

# 🔐 Configure Gemini with your API key
genai.configure(api_key=GOOGLE_API_KEY)

# 🧠 Smart prompt to extract document type & relevant fields
def build_prompt(text):
    return f"""
You are an intelligent document extraction agent.

Your task is to:
1. Understand what kind of document this is (e.g., resume, invoice, bill, letter, academic paper, etc.)
2. Extract only the relevant fields for that document type.
3. Return a clean and valid JSON with the detected type and all key fields.
4. If unsure about the structure, return a "summary" field.

📄 Document Content:
{text[:4000]}  # You can increase this limit for longer docs
"""

# 🚨 Fallback rule-based extractor (used only when Gemini fails)
def extract_entities_with_rules(text):
    return {
        "document_type": "unknown",
        "summary": text[:1000] + "...",
        "note": "Fallback used. No intelligent fields extracted."
    }

# 🚀 Main function: GenAI with fallback
def extract_entities_with_fallback(text):
    prompt = build_prompt(text)

    try:
        print(f"🤖 Using Gemini model: {GEMINI_MODEL}")
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        raw_output = response.text.strip()
        print("📤 Gemini Raw Output:\n", raw_output)

        # ✂️ Extract JSON portion from the output
        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}") + 1
        cleaned_json = raw_output[json_start:json_end]

        # 🧪 Try parsing the JSON output
        try:
            data = json.loads(cleaned_json)
            if isinstance(data, dict) and data:
                return data
            else:
                print("⚠️ Gemini output was invalid JSON. Using fallback.")
                return extract_entities_with_rules(text)
        except Exception as parse_err:
            print("⚠️ JSON parse failed:", parse_err)
            return extract_entities_with_rules(text)

    except Exception as e:
        print("❌ Gemini failed:", e)
        return extract_entities_with_rules(text)
