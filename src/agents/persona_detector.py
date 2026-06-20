"""
LLM-based persona detection using Google Gemini.
Classifies user messages into Technical Expert, Frustrated User, or Business Executive.
"""

import json
import re

from google import genai
from google.genai import types

from config.settings import GOOGLE_API_KEY, GEMINI_MODEL
from src.models.schemas import PersonaResult, PersonaType, SentimentType
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-initialized Gemini client
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

PERSONA_DETECTION_PROMPT = """You are an expert customer support analyst. Analyze the customer's message and classify them into one of three personas. Also determine their sentiment.

## Persona Definitions

### Technical Expert
- Uses technical terminology (API, configuration, logs, endpoints, error codes, stack trace)
- Requests specific technical details, root cause analysis, or debugging information
- Asks about system architecture, APIs, integrations, or configurations
- Communication style: precise, detailed, systematic

### Frustrated User
- Uses emotional or urgent language (frustrated, angry, ridiculous, unacceptable, worst)
- Expresses repeated complaints or mentions failed attempts
- Uses exclamation marks, ALL CAPS, or strong negative words
- Demands immediate resolution or threatens to leave
- Communication style: emotional, urgent, impatient

### Business Executive
- Focuses on business impact, operations, revenue, or timelines
- Asks about resolution timelines, SLAs, or service level commitments
- Prefers high-level summaries over technical details
- Mentions team, organization, enterprise, or strategic concerns
- Communication style: concise, outcome-focused, professional

## Sentiment Categories
- positive: Satisfied, grateful, optimistic
- neutral: Informational, no strong emotion
- negative: Dissatisfied, concerned, disappointed
- angry: Very frustrated, hostile, threatening

## Conversation History (for context)
{conversation_history}

## Current User Message
{user_message}

## Response Format
Respond with ONLY a valid JSON object (no markdown, no code blocks):
{{
    "persona": "Technical Expert" | "Frustrated User" | "Business Executive",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of why this persona was detected",
    "sentiment": "positive" | "neutral" | "negative" | "angry"
}}
"""


def detect_persona(
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> PersonaResult:
    """
    Detect the customer persona from their message.

    Args:
        user_message: The current user message
        conversation_history: Previous conversation turns for context

    Returns:
        PersonaResult with detected persona, confidence, reasoning, and sentiment
    """
    # Format conversation history
    history_text = "No previous conversation."
    if conversation_history:
        history_lines = []
        for turn in conversation_history[-6:]:  # Last 6 turns for context
            role = turn.get("role", "unknown")
            content = turn.get("content", "")[:200]  # Truncate long messages
            history_lines.append(f"  {role}: {content}")
        history_text = "\n".join(history_lines)

    prompt = PERSONA_DETECTION_PROMPT.format(
        user_message=user_message,
        conversation_history=history_text,
    )

    try:
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent classification
                max_output_tokens=300,
            ),
        )

        result_text = response.text.strip()

        # Clean up the response — remove markdown code blocks if present
        result_text = re.sub(r"```json\s*", "", result_text)
        result_text = re.sub(r"```\s*", "", result_text)
        result_text = result_text.strip()

        result = json.loads(result_text)

        persona_result = PersonaResult(
            persona=PersonaType(result["persona"]),
            confidence=float(result.get("confidence", 0.8)),
            reasoning=result.get("reasoning", "Classification based on message analysis"),
            sentiment=SentimentType(result.get("sentiment", "neutral")),
        )

        logger.info(
            f"Persona: {persona_result.persona.value} "
            f"(conf={persona_result.confidence:.2f}, "
            f"sentiment={persona_result.sentiment.value})"
        )
        return persona_result

    except Exception as e:
        logger.error(f"Persona detection failed: {e}, using fallback")
        return _fallback_detection(user_message)


def _fallback_detection(user_message: str) -> PersonaResult:
    """Rule-based fallback when LLM detection fails."""
    msg_lower = user_message.lower()

    # Check for frustrated user signals
    frustration_signals = [
        "frustrated", "angry", "ridiculous", "unacceptable", "worst",
        "terrible", "nothing works", "tried everything", "give up",
        "fix this", "broken", "useless", "waste of time", "!!!",
    ]
    frustration_score = sum(1 for signal in frustration_signals if signal in msg_lower)
    has_caps = len(re.findall(r"[A-Z]{3,}", user_message)) > 0
    has_exclamation = user_message.count("!") >= 2

    if frustration_score >= 2 or (frustration_score >= 1 and (has_caps or has_exclamation)):
        return PersonaResult(
            persona=PersonaType.FRUSTRATED_USER,
            confidence=0.7,
            reasoning="Detected emotional language and frustration signals (fallback)",
            sentiment=SentimentType.ANGRY if frustration_score >= 3 else SentimentType.NEGATIVE,
        )

    # Check for technical expert signals
    technical_signals = [
        "api", "endpoint", "configuration", "log", "error code", "debug",
        "stack trace", "authentication", "oauth", "jwt", "sdk", "cli",
        "dns", "tcp", "http", "ssh", "port", "firewall", "query",
        "database", "replication", "latency", "throughput", "iops",
    ]
    technical_score = sum(1 for signal in technical_signals if signal in msg_lower)

    if technical_score >= 2:
        return PersonaResult(
            persona=PersonaType.TECHNICAL_EXPERT,
            confidence=0.7,
            reasoning="Detected technical terminology (fallback)",
            sentiment=SentimentType.NEUTRAL,
        )

    # Check for business executive signals
    business_signals = [
        "business impact", "operations", "revenue", "timeline", "sla",
        "enterprise", "strategic", "budget", "roi", "stakeholder",
        "when will", "how does this affect", "bottom line", "team",
        "organization", "executive", "management", "quarterly",
    ]
    business_score = sum(1 for signal in business_signals if signal in msg_lower)

    if business_score >= 1:
        return PersonaResult(
            persona=PersonaType.BUSINESS_EXECUTIVE,
            confidence=0.6,
            reasoning="Detected business-focused language (fallback)",
            sentiment=SentimentType.NEUTRAL,
        )

    # Default to technical expert with lower confidence
    return PersonaResult(
        persona=PersonaType.TECHNICAL_EXPERT,
        confidence=0.5,
        reasoning="No strong persona signals detected, defaulting to Technical Expert (fallback)",
        sentiment=SentimentType.NEUTRAL,
    )
