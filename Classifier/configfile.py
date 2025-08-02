import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCq_jk2ARXmk2V258LyelQT9bH9QVcJCZI")
GEMINI_MODEL = "models/gemini-1.5-pro-latest"