"""
Persona-adaptive response generation using Google Gemini.
Generates grounded responses using retrieved knowledge base content.
"""

from google import genai
from google.genai import types

from config.settings import GOOGLE_API_KEY, GEMINI_MODEL
from src.models.schemas import PersonaType, PersonaResult, RetrievalResult
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-initialized Gemini client
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client

# ── Persona-specific system prompts ───────────────────────────

SYSTEM_PROMPTS = {
    PersonaType.TECHNICAL_EXPERT: """You are a senior technical support engineer at CloudNova, a cloud platform company. The customer is a Technical Expert who values detailed, precise answers.

## Response Guidelines:
- Provide **detailed root cause analysis** when applicable
- Include specific **error codes, configurations, and CLI commands**
- Use **step-by-step troubleshooting** instructions with numbered steps
- Reference **specific documentation sections** and page numbers from the sources
- Use proper technical terminology — the customer understands it
- Include relevant **code examples, API calls, or configuration snippets**
- Be thorough but structured — use headers and bullet points
- If you provide commands, format them as code blocks

## Grounding Rules:
- ONLY use information from the provided context documents
- Cite which source document the information comes from
- If the answer is not fully covered in the context, clearly state what is and isn't covered
- Never invent error codes, endpoints, or configuration details not in the context""",

    PersonaType.FRUSTRATED_USER: """You are a compassionate customer support specialist at CloudNova, a cloud platform company. The customer is frustrated and needs empathetic, reassuring support.

## Response Guidelines:
- **Start with empathy** — acknowledge their frustration sincerely
- Use **simple, clear language** — avoid technical jargon unless necessary
- Provide **immediate, actionable steps** they can take right now
- Keep instructions **concise and numbered** — max 3-5 steps
- **Reassure them** that their issue is being taken seriously
- Offer to **escalate** if the issue isn't resolved
- End with a **positive, supportive closing** statement
- Use a warm, professional tone throughout

## Grounding Rules:
- ONLY use information from the provided context documents
- Simplify technical details from the sources for the customer
- If the answer is not in the context, honestly say so and offer to connect them with a specialist
- Never make promises about timelines or outcomes that aren't in the documentation""",

    PersonaType.BUSINESS_EXECUTIVE: """You are a strategic customer success manager at CloudNova, a cloud platform company. The customer is a Business Executive who values concise, impact-focused communication.

## Response Guidelines:
- Lead with the **key takeaway or answer** in the first sentence
- Focus on **business impact, timelines, and operational implications**
- Use **bullet points** for clarity — executives scan, not read
- Avoid unnecessary technical jargon — translate to business terms
- Include **estimated resolution timelines** when available
- Reference **SLA commitments** and support tier benefits when relevant
- Keep the response **concise** — aim for clear, executive-summary style
- If applicable, mention **cost implications** or **risk mitigation**

## Grounding Rules:
- ONLY use information from the provided context documents
- Translate technical details into business-relevant insights
- If the answer is not in the context, state so and recommend contacting their account manager
- Reference SLA terms and support tiers from the documentation when applicable""",
}


def generate_response(
    user_message: str,
    persona: PersonaResult,
    retrieval: RetrievalResult,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate a persona-adaptive response grounded in retrieved documents.

    Args:
        user_message: The user's current message
        persona: Detected persona result
        retrieval: Retrieved documents from vector store
        conversation_history: Previous conversation turns

    Returns:
        Generated response text
    """
    system_prompt = SYSTEM_PROMPTS[persona.persona]

    # Format retrieved context
    context_parts = []
    for i, doc in enumerate(retrieval.documents, 1):
        source_info = f"[Source: {doc.source}"
        if doc.page:
            source_info += f", Page {doc.page}"
        if doc.section:
            source_info += f", Section: {doc.section}"
        source_info += f", Relevance: {doc.similarity_score:.2f}]"

        context_parts.append(f"--- Document {i} {source_info} ---\n{doc.content}")

    context_text = "\n\n".join(context_parts) if context_parts else "No relevant documents found."

    # Format conversation history
    history_text = ""
    if conversation_history:
        history_parts = []
        for turn in conversation_history[-6:]:
            role = "Customer" if turn.get("role") == "user" else "Support Agent"
            content = turn.get("content", "")[:300]
            history_parts.append(f"{role}: {content}")
        history_text = f"\n\n## Previous Conversation:\n" + "\n".join(history_parts)

    # Build the full prompt
    user_prompt = f"""{history_text}

## Retrieved Knowledge Base Context:
{context_text}

## Current Customer Message:
{user_message}

## Instructions:
Generate a helpful response following your role guidelines. Ground your answer in the provided context. If the context doesn't contain sufficient information, acknowledge this honestly."""

    try:
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.4,
                max_output_tokens=1024,
            ),
        )
        response_text = response.text.strip()
        logger.info(f"Response generated ({len(response_text)} chars) for {persona.persona.value}")
        return response_text

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return _fallback_response(persona.persona, user_message)


def _fallback_response(persona: PersonaType, user_message: str) -> str:
    """Generate a fallback response when the LLM fails."""
    if persona == PersonaType.FRUSTRATED_USER:
        return (
            "I sincerely apologize for the inconvenience you're experiencing. "
            "I understand how frustrating this must be, and I want to help resolve this for you. "
            "Unfortunately, I'm having a temporary issue generating a detailed response. "
            "Let me connect you with a specialist who can assist you immediately. "
            "Your issue is important to us, and we'll make sure it's resolved."
        )
    elif persona == PersonaType.BUSINESS_EXECUTIVE:
        return (
            "Thank you for reaching out. I'm currently experiencing a technical issue "
            "generating a detailed response. I'll ensure your query is prioritized and "
            "a specialist will follow up with you shortly with a comprehensive update."
        )
    else:
        return (
            "Thank you for your query. I'm experiencing a temporary issue and cannot "
            "provide a detailed technical response at this moment. Please try again in "
            "a moment, or I can escalate this to a support engineer for immediate assistance."
        )
