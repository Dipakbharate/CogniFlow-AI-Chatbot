import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# SQLite Database Path
DATABASE_URL = "chatbot.db"
