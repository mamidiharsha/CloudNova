"""
Pydantic models for all data structures used across the support agent.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────

class PersonaType(str, Enum):
    TECHNICAL_EXPERT = "Technical Expert"
    FRUSTRATED_USER = "Frustrated User"
    BUSINESS_EXECUTIVE = "Business Executive"


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "Low retrieval confidence"
    NO_RELEVANT_DOCS = "No relevant documents found"
    PERSISTENT_FRUSTRATION = "User remains frustrated after multiple interactions"
    SENSITIVE_TOPIC = "Billing, legal, or account-sensitive issue detected"
    EXPLICIT_REQUEST = "User explicitly requested human agent"
    UNRESOLVED_ISSUE = "Issue reported multiple times without resolution"
    CANNOT_RESOLVE = "Issue cannot be resolved using available documentation"


class FeedbackType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


# ── Core Models ────────────────────────────────────────────────

class PersonaResult(BaseModel):
    """Result of persona detection."""
    persona: PersonaType
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence 0-1")
    reasoning: str = Field(description="Why this persona was detected")
    sentiment: SentimentType = Field(description="Detected sentiment")


class RetrievedDocument(BaseModel):
    """A document chunk retrieved from the vector store."""
    content: str
    source: str = Field(description="Source filename")
    page: Optional[int] = Field(default=None, description="Page number if applicable")
    section: Optional[str] = Field(default=None, description="Section name")
    chunk_index: int = Field(default=0, description="Chunk index in source doc")
    similarity_score: float = Field(ge=0.0, le=1.0, description="Cosine similarity")


class RetrievalResult(BaseModel):
    """Aggregated retrieval results."""
    documents: list[RetrievedDocument] = Field(default_factory=list)
    top_score: float = Field(default=0.0, description="Highest similarity score")
    avg_score: float = Field(default=0.0, description="Average similarity score")
    query: str = Field(default="", description="The original query")


class EscalationDecision(BaseModel):
    """Whether the conversation should be escalated."""
    should_escalate: bool = False
    reasons: list[EscalationReason] = Field(default_factory=list)
    details: str = Field(default="", description="Human-readable explanation")


class HandoffSummary(BaseModel):
    """Structured summary for human agent handoff."""
    escalation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    persona: PersonaType
    sentiment: SentimentType
    issue_summary: str
    conversation_history: list[dict] = Field(default_factory=list)
    documents_used: list[str] = Field(default_factory=list)
    retrieval_scores: list[float] = Field(default_factory=list)
    attempted_steps: list[str] = Field(default_factory=list)
    escalation_reasons: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    priority: str = "MEDIUM"


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    role: str = Field(description="'user' or 'assistant'")
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    persona: Optional[PersonaType] = None
    sentiment: Optional[SentimentType] = None
    sources_used: list[str] = Field(default_factory=list)
    was_escalated: bool = False


class AgentResponse(BaseModel):
    """Complete response from the support agent."""
    response_text: str
    persona: PersonaResult
    retrieval: RetrievalResult
    escalation: EscalationDecision
    handoff_summary: Optional[HandoffSummary] = None
    turn_number: int = 1
    session_id: str = ""


class FeedbackRecord(BaseModel):
    """User feedback on a response."""
    session_id: str
    turn_number: int
    feedback: FeedbackType
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    comment: Optional[str] = None
