"""
CloudNova Support Agent — Central Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────────
load_dotenv()

# ── Paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
SQLITE_DB_PATH = PROJECT_ROOT / "conversations.db"

# ── LLM Configuration ─────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Embedding Configuration ───────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── RAG Settings ──────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
CHROMA_COLLECTION_NAME = "cloudnova_support"

# ── Escalation Thresholds (configurable) ──────────────────────
RETRIEVAL_CONFIDENCE_THRESHOLD = float(
    os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.35")
)
MAX_FRUSTRATION_TURNS = int(os.getenv("MAX_FRUSTRATION_TURNS", "3"))
MAX_REPETITION_THRESHOLD = int(os.getenv("MAX_REPETITION_THRESHOLD", "3"))

SENSITIVE_TOPICS = [
    "refund",
    "billing dispute",
    "legal",
    "account deletion",
    "cancel subscription",
    "data breach",
    "compliance",
    "lawsuit",
    "terminate account",
    "chargeback",
]

ESCALATION_KEYWORDS = [
    "speak to a human",
    "talk to a person",
    "escalate",
    "transfer me",
    "human agent",
    "real person",
    "manager",
    "supervisor",
]

# ── Persona Definitions ──────────────────────────────────────
PERSONAS = {
    "Technical Expert": {
        "color": "#3B82F6",  # Blue
        "icon": "🔧",
        "description": "Uses technical terminology, requests logs/APIs/configs, wants detailed explanations",
    },
    "Frustrated User": {
        "color": "#EF4444",  # Red
        "icon": "😤",
        "description": "Emotional language, repeated complaints, urgent requests",
    },
    "Business Executive": {
        "color": "#8B5CF6",  # Purple
        "icon": "💼",
        "description": "Outcome-focused, interested in business impact, prefers concise communication",
    },
}
