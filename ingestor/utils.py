import os

def is_valid_document(file_name):
    ext = os.path.splitext(file_name)[1].lower()
    return ext in [".pdf", ".docx", ".txt", ".png", ".jpg"]
