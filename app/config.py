# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM (Groq) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# --- MusicBrainz ---
MUSICBRAINZ_USER_AGENT = os.getenv(
    "MUSICBRAINZ_USER_AGENT",
    "MusicAI/1.0 (contact@example.com)",
)

# --- Data directory ---
BASE_DATA_DIR = os.getenv("BASE_DATA_DIR", "data")
