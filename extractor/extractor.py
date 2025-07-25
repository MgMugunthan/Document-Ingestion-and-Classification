import os
import json
import fitz  # from PyMuPDF
from PIL import Image
import pytesseract
from docx import Document
import openpyxl
from utils.genai_utils import extract_entities_with_fallback
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTED_DIR = os.path.join(BASE_DIR, "ingested")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        print(" PDF Error:", e)
        return ""
def extract_text_from_image(file_path):
    try:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(" OCR Error:", e)
        return ""
def extract_text_from_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(" TXT Error:", e)
        return ""
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(" DOCX Error:", e)
        return ""
def extract_text_from_xlsx(file_path):
    try:
        wb = openpyxl.load_workbook(file_path)
        text = ""
        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value:
                        text += str(cell.value) + "\n"
        return text
    except Exception as e:
        print(" XLSX Error:", e)
        return ""
def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_text_from_image(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".xlsx":
        return extract_text_from_xlsx(file_path)
    else:
        print(" Unsupported file type:", ext)
        return ""
def process_file(file_path):
    print("\n Document Extractor Agent (Gemini Flash + Rule Fallback)")
    print(f" Processing: {os.path.basename(file_path)}")

    text = extract_text_from_file(file_path)
    if not text.strip():
        print(" No text extracted.")
        return

    result = extract_entities_with_fallback(text)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_name = os.path.splitext(os.path.basename(file_path))[0] + "_output.json"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f" Output saved: {output_path}")
if __name__ == "__main__":
    if not os.path.exists(INGESTED_DIR):
        print(" 'ingested/' folder not found.")
    else:
        files = os.listdir(INGESTED_DIR)
        if not files:
            print(" No files found in 'ingested/' folder.")
        else:
            for file_name in files:
                file_path = os.path.join(INGESTED_DIR, file_name)
                if os.path.isfile(file_path):
                    process_file(file_path)
