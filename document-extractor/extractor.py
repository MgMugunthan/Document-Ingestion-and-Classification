import os
import json
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
import requests
from datetime import datetime

GOOGLE_API_KEY="#YOUR_GOOGLE_API_KEY#"
GEMINI_MODEL="models/gemini-1.5-flash-latest"

GROQ_API_KEY=" #YOUR_GROQ_API_KEY#"
GROQ_MODEL="mixtral-8x7b-32768"

OPENROUTER_API_KEY="#YOUR_OPENROUTER_API_KEY#"
OPENROUTER_MODEL="mistralai/mistral-small-3.2-24b-instruct:free"

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
        return f" Failed to extract: {e}"
    return ""


def format_with_prompt(raw_text):
    return f"""
Clean and structure the following document content into readable bullet points or organized sections for a human reader.
Avoid JSON format. Use plain English in a structured, clear .txt layout:

---
{raw_text}
---
"""
def fallback_text_cleaning(raw_text):
    lines = raw_text.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(f"- {line.capitalize()}")
    return "\n".join(cleaned_lines) if cleaned_lines else "No meaningful content extracted."

def def_format_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
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
        "messages": [{"role": "user", "content": prompt}]
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
        "messages": [{"role": "user", "content": prompt}]
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
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_docs = sorted(doc_files, key=lambda f: priority_order.get(get_metadata_priority(f), 2))

    for file in sorted_docs:
        file_path = os.path.join(INPUT_DIR, file)
        print(f" Processing: {file}....")
        raw_text = extract_text(file_path)

        if not raw_text.strip():
            print(f" No text extracted from {file}")
            output_text = " Text extraction failed or unsupported file format."
        else:
            prompt = f"""You are an expert document extraction system. Extract and cleanly format the important content from the following raw text:

{raw_text}

Return only clean, readable content suitable for saving as .txt file."""
            try:
                print(" Formatting with Fallback...")
                output_text = fallback_text_cleaning(raw_text)
            except Exception as e1:
                print(f" Fallback failed: {e1}")
                try:
                    output_text = def_format_gemini(prompt)
                except Exception as e2:
                    print(" Gemini failed: {e2}")
                    try:
                        output_text = def_format_openrouter(prompt)
                    except Exception as e3:
                        print(f" Openrouter failed: {e3}")
                        output_text = def_format_groq(prompt)

        base_filename = os.path.splitext(file)[0]
        output_path = os.path.join(OUTPUT_DIR, base_filename + ".txt")
        with open(output_path, "w", encoding="utf-8") as out_f:
            out_f.write(output_text.strip())
        print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    process_files()
