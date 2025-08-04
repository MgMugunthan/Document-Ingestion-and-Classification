import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "folder")  # new folder path

os.makedirs(FILES_DIR, exist_ok=True)
