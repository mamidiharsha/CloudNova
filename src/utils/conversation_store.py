"""
SQLite-backed conversation persistence for multi-turn memory.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from config.settings import SQLITE_DB_PATH
from src.models.schemas import ConversationTurn, FeedbackRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationStore:
    """Manages conversation history in SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or SQLITE_DB_PATH)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    turn_count INTEGER DEFAULT 0,
                    frustration_count INTEGER DEFAULT 0,
                    last_persona TEXT,
                    escalated BOOLEAN DEFAULT FALSE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    persona TEXT,
                    sentiment TEXT,
                    sources_used TEXT,
                    was_escalated BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    feedback TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    comment TEXT,
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
                )
            """)
            conn.commit()

    def create_session(self) -> str:
        """Create a new conversation session and return its ID."""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now, now),
            )
            conn.commit()
        logger.info(f"Created session: {session_id}")
        return session_id

    def add_turn(self, session_id: str, turn: ConversationTurn, turn_number: int):
        """Add a conversation turn."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO turns
                   (session_id, turn_number, role, content, timestamp, persona, sentiment, sources_used, was_escalated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    turn_number,
                    turn.role,
                    turn.content,
                    turn.timestamp,
                    turn.persona.value if turn.persona else None,
                    turn.sentiment.value if turn.sentiment else None,
                    json.dumps(turn.sources_used),
                    turn.was_escalated,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ?, turn_count = ? WHERE session_id = ?",
                (datetime.now().isoformat(), turn_number, session_id),
            )
            conn.commit()

    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT role, content, persona, sentiment FROM turns WHERE session_id = ? ORDER BY turn_number",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_turn_count(self, session_id: str) -> int:
        """Get the number of turns in a session."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT turn_count FROM conversations WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return result[0] if result else 0

    def update_frustration_count(self, session_id: str, count: int):
        """Update the frustration counter for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE conversations SET frustration_count = ? WHERE session_id = ?",
                (count, session_id),
            )
            conn.commit()

    def get_frustration_count(self, session_id: str) -> int:
        """Get the frustration counter for a session."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT frustration_count FROM conversations WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return result[0] if result else 0

    def mark_escalated(self, session_id: str):
        """Mark a session as escalated."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE conversations SET escalated = TRUE WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()

    def add_feedback(self, record: FeedbackRecord):
        """Store user feedback for a turn."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO feedback (session_id, turn_number, feedback, timestamp, comment) VALUES (?, ?, ?, ?, ?)",
                (record.session_id, record.turn_number, record.feedback.value, record.timestamp, record.comment),
            )
            conn.commit()

    def is_escalated(self, session_id: str) -> bool:
        """Check if a session has been escalated."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT escalated FROM conversations WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return bool(result[0]) if result else False
