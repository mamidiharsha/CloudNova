"""
Escalation logic and human handoff summary generation.
Configurable triggers for determining when to escalate to a human agent.
"""

import json
import re
import uuid
from datetime import datetime

from google import genai
from google.genai import types

from config.settings import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    RETRIEVAL_CONFIDENCE_THRESHOLD,
    MAX_FRUSTRATION_TURNS,
    SENSITIVE_TOPICS,
    ESCALATION_KEYWORDS,
)
from src.models.schemas import (
    PersonaResult,
    PersonaType,
    SentimentType,
    RetrievalResult,
    EscalationDecision,
    EscalationReason,
    HandoffSummary,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-initialized Gemini client
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def check_escalation(
    user_message: str,
    persona: PersonaResult,
    retrieval: RetrievalResult,
    frustration_count: int = 0,
    conversation_history: list[dict] | None = None,
) -> EscalationDecision:
    """
    Evaluate whether the conversation should be escalated to a human agent.

    Checks multiple configurable triggers and returns a decision.
    """
    reasons: list[EscalationReason] = []
    details_parts: list[str] = []

    msg_lower = user_message.lower()

    # ── Trigger 1: Explicit escalation request ─────────────
    for keyword in ESCALATION_KEYWORDS:
        if keyword in msg_lower:
            reasons.append(EscalationReason.EXPLICIT_REQUEST)
            details_parts.append(f"User explicitly requested escalation (matched: '{keyword}')")
            break

    # ── Trigger 2: No relevant documents found ─────────────
    if not retrieval.documents or len(retrieval.documents) == 0:
        reasons.append(EscalationReason.NO_RELEVANT_DOCS)
        details_parts.append("No documents were retrieved from the knowledge base")

    # ── Trigger 3: Low retrieval confidence ────────────────
    elif retrieval.top_score < RETRIEVAL_CONFIDENCE_THRESHOLD:
        reasons.append(EscalationReason.LOW_CONFIDENCE)
        details_parts.append(
            f"Top retrieval score ({retrieval.top_score:.3f}) "
            f"is below threshold ({RETRIEVAL_CONFIDENCE_THRESHOLD})"
        )

    # ── Trigger 4: Persistent frustration ──────────────────
    if persona.persona == PersonaType.FRUSTRATED_USER:
        current_frustration = frustration_count + 1
        if current_frustration >= MAX_FRUSTRATION_TURNS:
            reasons.append(EscalationReason.PERSISTENT_FRUSTRATION)
            details_parts.append(
                f"Frustrated user for {current_frustration} consecutive turns "
                f"(threshold: {MAX_FRUSTRATION_TURNS})"
            )

    # ── Trigger 5: Sensitive topics ────────────────────────
    for topic in SENSITIVE_TOPICS:
        if topic in msg_lower:
            reasons.append(EscalationReason.SENSITIVE_TOPIC)
            details_parts.append(f"Sensitive topic detected: '{topic}'")
            break

    # ── Trigger 6: Angry sentiment with high confidence ────
    if persona.sentiment == SentimentType.ANGRY and persona.confidence >= 0.7:
        if EscalationReason.PERSISTENT_FRUSTRATION not in reasons:
            # Only add if not already captured by frustration trigger
            if frustration_count >= MAX_FRUSTRATION_TURNS - 1:
                reasons.append(EscalationReason.PERSISTENT_FRUSTRATION)
                details_parts.append("Highly angry sentiment detected with high confidence")

    should_escalate = len(reasons) > 0
    details = " | ".join(details_parts) if details_parts else "No escalation triggers matched"

    if should_escalate:
        logger.warning(f"ESCALATION TRIGGERED: {details}")
    else:
        logger.info("No escalation needed")

    return EscalationDecision(
        should_escalate=should_escalate,
        reasons=reasons,
        details=details,
    )


def generate_handoff_summary(
    user_message: str,
    persona: PersonaResult,
    retrieval: RetrievalResult,
    escalation: EscalationDecision,
    conversation_history: list[dict] | None = None,
) -> HandoffSummary:
    """
    Generate a structured summary for human agent handoff.
    Uses the LLM to create a meaningful summary from conversation context.
    """
    escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Use LLM to generate issue summary and recommended steps
    history_text = ""
    if conversation_history:
        for turn in conversation_history[-8:]:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")[:300]
            history_text += f"\n{role}: {content}"

    documents_used = list({doc.source for doc in retrieval.documents})
    retrieval_scores = [doc.similarity_score for doc in retrieval.documents]

    try:
        summary_prompt = f"""Analyze this customer support conversation and generate a structured handoff summary for the human support agent.

Customer's latest message: {user_message}

Conversation history: {history_text}

Detected persona: {persona.persona.value}
Detected sentiment: {persona.sentiment.value}
Escalation reasons: {[r.value for r in escalation.reasons]}
Documents retrieved: {documents_used}

Respond with ONLY a valid JSON object (no markdown):
{{
    "issue_summary": "Brief 1-2 sentence summary of the customer's issue",
    "attempted_steps": ["List of steps already attempted or discussed"],
    "recommended_next_steps": ["Specific actions the human agent should take"]
}}"""

        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=summary_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=500,
            ),
        )

        result_text = response.text.strip()
        result_text = re.sub(r"```json\s*", "", result_text)
        result_text = re.sub(r"```\s*", "", result_text)
        summary_data = json.loads(result_text)

    except Exception as e:
        logger.error(f"LLM summary generation failed: {e}")
        summary_data = {
            "issue_summary": f"Customer issue requiring human attention: {user_message[:200]}",
            "attempted_steps": ["Automated support attempted", "Knowledge base searched"],
            "recommended_next_steps": ["Review conversation history", "Contact customer directly"],
        }

    # Determine priority
    priority = "MEDIUM"
    if persona.sentiment == SentimentType.ANGRY:
        priority = "HIGH"
    if EscalationReason.SENSITIVE_TOPIC in escalation.reasons:
        priority = "HIGH"
    if EscalationReason.EXPLICIT_REQUEST in escalation.reasons:
        priority = "HIGH"

    # Build conversation history for the summary
    conv_history = []
    if conversation_history:
        for turn in conversation_history[-10:]:
            conv_history.append({
                "role": turn.get("role", "unknown"),
                "content": turn.get("content", "")[:500],
            })
    conv_history.append({"role": "user", "content": user_message})

    handoff = HandoffSummary(
        escalation_id=escalation_id,
        persona=persona.persona,
        sentiment=persona.sentiment,
        issue_summary=summary_data.get("issue_summary", user_message[:200]),
        conversation_history=conv_history,
        documents_used=documents_used,
        retrieval_scores=retrieval_scores,
        attempted_steps=summary_data.get("attempted_steps", []),
        escalation_reasons=[r.value for r in escalation.reasons],
        recommended_next_steps=summary_data.get("recommended_next_steps", []),
        priority=priority,
    )

    logger.info(f"Handoff summary generated: {escalation_id} (priority={priority})")
    return handoff
