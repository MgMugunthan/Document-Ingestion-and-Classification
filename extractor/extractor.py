import os
import json
import pdfplumber
import pytesseract
from PIL import Image
from docx import Document
import openpyxl
import requests

GOOGLE_API_KEY="#YOUR_GOOGLE_API_KEY#"
GEMINI_MODEL="models/gemini-1.5-flash-latest"

GROQ_API_KEY="#YOUR_GROQ_API_KEY#"
GROQ_MODEL="mixtral-8x7b-32768"

OPENROUTER_API_KEY="#YOUR_OPENROUTER_API_KEY#"
OPENROUTER_MODEL="mistralai/mistral-small-3.2-24b-instruct:free"

def extract_text(file_path):
    ext = file_path.lower().split(".")[-1]
    try:
        if ext == "pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)

        elif ext in ["png", "jpg", "jpeg"]:
            return pytesseract.image_to_string(Image.open(file_path))

        elif ext == "docx":
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        elif ext in ["xlsx", "xls"]:
            wb = openpyxl.load_workbook(file_path)
            text = ""
            for sheet in wb:
                for row in sheet.iter_rows(values_only=True):
                    text += "\t".join([str(cell) if cell else "" for cell in row]) + "\n"
            return text

        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        else:
            return ""
    except Exception as e:
        print(f"[Extractor ❌] Failed to extract from {file_path}: {e}")
        return ""

def fallback_format(text):
    return f"[Formatted]\n{text.strip()}"

def gemini_format(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"Clean this text:\n{text}"}]}]
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        response_json = r.json()
        return response_json["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.RequestException as e:
        print(f"[Extractor ❌] HTTP request failed: {e}")
    except (KeyError, TypeError) as e:
        print(f"[Extractor ❌] Unexpected response structure: {e}")
    return "[Unformatted] " + text

def process_metadata(metadata_file_path):
    try:
        with open(metadata_file_path) as f:
            meta = json.load(f)
    except Exception as e:
        print(f"[Extractor ❌] Failed to load JSON {metadata_file_path}: {e}")
        return

    path = meta.get("file_path") or meta.get("path")  # Support both
    if not path or not os.path.exists(path):
        print(f"[Extractor ⚠️] File not found at path: {path}")
        return

    text = extract_text(path)
    if not text.strip():
        print(f"[Extractor ⚠️] No text extracted from: {path}")
        return

    try:
        formatted = fallback_format(text)
    except:
        try:
            formatted = gemini_format(text)
        except:
            formatted = "[Unformatted] " + text

    file_base = os.path.splitext(os.path.basename(path))[0]
    out_txt = os.path.join("extracted_output", file_base + ".txt")
    out_json = os.path.join("extracted_output", file_base + ".json")

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(formatted)
    with open(out_json, "w") as f:
        json.dump(meta, f, indent=4)

    print(f"[Extractor ✅] Extracted and saved: {out_txt} and {out_json}")

if __name__ == "__main__":
    os.makedirs("extracted_output", exist_ok=True)
    json_files = [f for f in os.listdir("received_docs") if f.endswith(".json")]

    if not json_files:
        print("[Extractor] No metadata files found in received_docs/")
    for file in json_files:
        full_path = os.path.join("received_docs", file)
        process_metadata(full_path)

    print("[Extractor ✅] Done.")
