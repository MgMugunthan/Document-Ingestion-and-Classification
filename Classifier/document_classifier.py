import sys
import os
import json
import uuid
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from genai_mas.utils.genai_utils import classify_document


def classify_single_document(file_path):
    """
    Classify a single document using LLM.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        classification_result = classify_document(content)
        return {
            "file_name": os.path.basename(file_path),
            "classification": classification_result
        }

    except Exception as e:
        return {
            "file_name": os.path.basename(file_path),
            "error": str(e)
        }


def classify_documents_in_folder(input_folder, output_folder):
    """
    Classifies all .txt documents in a folder and saves results as individual JSON files.
    Now outputs MAS-compatible metadata format.
    """
    os.makedirs(output_folder, exist_ok=True)
    summary = []

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".txt"):
            file_path = os.path.join(input_folder, file_name)

            print(f"\nProcessing: {file_name}")
            result = classify_single_document(file_path)

            if "classification" in result:
                category = result["classification"].get("document_type", "Unknown")
                print(f"Classified as: {category}")
            else:
                print(f"Error: {result['error']}")
                category = "Error"

            mas_result = {
                "document_id": str(uuid.uuid4()),
                "type": category.lower() if category != "Unknown" else "unknown",
                "path": file_path.replace("genai_mas\\ingested\\", "samples/").replace("\\", "/").replace(".txt", ".pdf"),
                "size": os.path.getsize(file_path),
                "file_extension": "application/pdf", 
                "upload_timestamp": datetime.now().isoformat(timespec='seconds')
            }

            out_filename = f"{os.path.splitext(file_name)[0]}.json"
            output_path = os.path.join(output_folder, out_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(mas_result, f, indent=4)

            raw_debug_path = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}.meta.json")
            with open(raw_debug_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)

            print(f"Saved: {output_path}")
            summary.append(mas_result)

    summary_path = os.path.join(output_folder, "classification_results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    print(f"\n Classification completed! Summary saved to {summary_path}")


if __name__ == "__main__":
    INPUT_FOLDER = "genai_mas/ingested"
    OUTPUT_FOLDER = "genai_mas/output"
    classify_documents_in_folder(INPUT_FOLDER, OUTPUT_FOLDER)

