import os
import json
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import requests
from datetime import datetime

# Set API keys and models directly
GOOGLE_API_KEY = "#YOUR_GOOGLE_API_KEY#"
GEMINI_MODEL = "models/gemini-1.5-flash-latest"
GROQ_API_KEY = "#YOUR_GROQ_API_KEY#"
GROQ_MODEL = "llama3-70b-8192"
OPENROUTER_API_KEY = "#YOUR_OPENROUTER_API_KEY#"
OPENROUTER_MODEL = "openchat/openchat-7b:free"

INPUT_DIR = "input_files"
OUTPUT_DIR = "output_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        elif ext in [".png", ".jpg", ".jpeg"]:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
    except Exception as e:
        return f"❌ Failed to extract: {e}"
    return ""


def format_with_prompt(raw_text):
    return f"""
Clean and structure the following document content into readable bullet points or organized sections for a human reader.
Avoid JSON format. Use plain English in a structured, clear .txt layout:

---
{raw_text}
---
"""


def def_format_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    res = requests.post(url, headers=headers, json=data)
    if res.ok:
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise Exception(res.text)


def def_format_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post(url, headers=headers, json=data)
    if res.ok:
        return res.json()["choices"][0]["message"]["content"]
    raise Exception(res.text)


def def_format_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post(url, headers=headers, json=data)
    if res.ok:
        return res.json()["choices"][0]["message"]["content"]
    raise Exception(res.text)


def get_metadata_priority(file_name):
    meta_path = os.path.join(INPUT_DIR, os.path.splitext(file_name)[0] + ".json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                metadata = json.load(f)
            return metadata.get("priority", "low")
        except:
            return "low"
    return "low"


def process_files():
    all_files = os.listdir(INPUT_DIR)
    doc_files = [f for f in all_files if os.path.splitext(f)[1].lower() in [".pdf", ".docx", ".jpg", ".jpeg", ".png"]]

    # Sort based on priority in metadata
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_docs = sorted(doc_files, key=lambda f: priority_order.get(get_metadata_priority(f), 2))

    for file in sorted_docs:
        file_path = os.path.join(INPUT_DIR, file)
        print(f"🔍 Processing: {file}")
        raw_text = extract_text(file_path)

        if not raw_text.strip():
            print(f"⚠️ Skipped empty or unsupported file: {file}")
            continue

        prompt = format_with_prompt(raw_text)
        output_text = None

        try:
            output_text = def_format_gemini(prompt)
        except Exception as e1:
            print(f"⚠️ Gemini failed: {e1}")
            try:
                output_text = def_format_groq(prompt)
            except Exception as e2:
                print(f"⚠️ Groq failed: {e2}")
                try:
                    output_text = def_format_openrouter(prompt)
                except Exception as e3:
                    print(f"⚠️ OpenRouter failed: {e3}")
                    print(f"❌ All APIs failed for {file}")
                    continue

        # Save structured output to .txt file
        txt_path = os.path.join(OUTPUT_DIR, os.path.splitext(file)[0] + ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(output_text or "Unable to extract content")
        print(f"✅ Saved to: {txt_path}\n")


if __name__ == "__main__":
    process_files()
