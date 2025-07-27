import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from genai_mas.utils.genai_utils import classify_document



def classify_document(file_path):
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
    Classifies all .txt documents in a folder and saves results as JSON.
    """
    os.makedirs(output_folder, exist_ok=True)
    results = []

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".txt"):
            file_path = os.path.join(input_folder, file_name)
            result = classify_document(file_path)
            results.append(result)

    output_path = os.path.join(output_folder, "classification_results.json")
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    print(f" Classification completed! Results saved to {output_path}")


if __name__ == "__main__":
    INPUT_FOLDER = "genai_mas/ingested"
    OUTPUT_FOLDER = "genai_mas/output"


    classify_documents_in_folder(INPUT_FOLDER, OUTPUT_FOLDER)
