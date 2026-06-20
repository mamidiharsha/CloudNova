"""
LangGraph workflow orchestration for the Customer Support Agent.
Implements a state machine with typed state and conditional routing.
"""

from __future__ import annotations

from typing import Annotated, TypedDict, Optional

from langgraph.graph import StateGraph, END

from src.agents.persona_detector import detect_persona
from src.agents.response_generator import generate_response
from src.agents.escalation_manager import check_escalation, generate_handoff_summary
from src.knowledge_base.vector_store import VectorStore
from src.models.schemas import (
    PersonaResult,
    PersonaType,
    SentimentType,
    RetrievalResult,
    EscalationDecision,
    HandoffSummary,
    AgentResponse,
    ConversationTurn,
)
from src.utils.conversation_store import ConversationStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── LangGraph State Definition ────────────────────────────────

class AgentState(TypedDict):
    """Typed state for the LangGraph workflow."""
    user_message: str
    conversation_history: list[dict]
    session_id: str
    turn_number: int
    frustration_count: int

    # Outputs from each node
    persona: Optional[PersonaResult]
    retrieval: Optional[RetrievalResult]
    escalation: Optional[EscalationDecision]
    response_text: str
    handoff_summary: Optional[HandoffSummary]
    final_response: Optional[AgentResponse]


# ── Workflow Nodes ────────────────────────────────────────────

def persona_detection_node(state: AgentState) -> dict:
    """Node 1: Detect the customer's persona."""
    logger.info("━━━ Node: Persona Detection ━━━")
    persona = detect_persona(
        user_message=state["user_message"],
        conversation_history=state["conversation_history"],
    )
    return {"persona": persona}


def retrieval_node(state: AgentState) -> dict:
    """Node 2: Retrieve relevant documents from the knowledge base."""
    logger.info("━━━ Node: Knowledge Base Retrieval ━━━")
    vector_store = VectorStore()
    retrieval = vector_store.query(state["user_message"])
    logger.info(
        f"Retrieved {len(retrieval.documents)} docs "
        f"(top_score={retrieval.top_score:.3f}, avg={retrieval.avg_score:.3f})"
    )
    return {"retrieval": retrieval}


def escalation_check_node(state: AgentState) -> dict:
    """Node 3: Check if escalation is needed."""
    logger.info("━━━ Node: Escalation Check ━━━")

    # Update frustration count
    frustration_count = state["frustration_count"]
    if state["persona"] and state["persona"].persona == PersonaType.FRUSTRATED_USER:
        frustration_count += 1
    else:
        frustration_count = 0  # Reset if persona changes

    escalation = check_escalation(
        user_message=state["user_message"],
        persona=state["persona"],
        retrieval=state["retrieval"],
        frustration_count=frustration_count - 1,  # -1 because check_escalation adds 1
        conversation_history=state["conversation_history"],
    )
    return {
        "escalation": escalation,
        "frustration_count": frustration_count,
    }


def response_generation_node(state: AgentState) -> dict:
    """Node 4a: Generate persona-adaptive response (no escalation)."""
    logger.info("━━━ Node: Response Generation ━━━")
    response_text = generate_response(
        user_message=state["user_message"],
        persona=state["persona"],
        retrieval=state["retrieval"],
        conversation_history=state["conversation_history"],
    )
    return {"response_text": response_text}


def handoff_node(state: AgentState) -> dict:
    """Node 4b: Generate handoff summary (escalation path)."""
    logger.info("━━━ Node: Human Handoff ━━━")
    handoff = generate_handoff_summary(
        user_message=state["user_message"],
        persona=state["persona"],
        retrieval=state["retrieval"],
        escalation=state["escalation"],
        conversation_history=state["conversation_history"],
    )

    # Generate an escalation response for the customer
    escalation_response = _build_escalation_message(state["persona"], handoff)

    return {
        "handoff_summary": handoff,
        "response_text": escalation_response,
    }


def output_node(state: AgentState) -> dict:
    """Node 5: Assemble the final response."""
    logger.info("━━━ Node: Output Assembly ━━━")
    final = AgentResponse(
        response_text=state["response_text"],
        persona=state["persona"],
        retrieval=state["retrieval"],
        escalation=state["escalation"],
        handoff_summary=state.get("handoff_summary"),
        turn_number=state["turn_number"],
        session_id=state["session_id"],
    )
    return {"final_response": final}


# ── Conditional Edge ──────────────────────────────────────────

def should_escalate(state: AgentState) -> str:
    """Conditional routing: escalate or respond."""
    if state["escalation"] and state["escalation"].should_escalate:
        logger.info("→ Routing to HANDOFF")
        return "handoff"
    logger.info("→ Routing to RESPONSE")
    return "respond"


# ── Helper ────────────────────────────────────────────────────

def _build_escalation_message(persona: PersonaResult, handoff: HandoffSummary) -> str:
    """Build a customer-facing escalation message."""
    if persona.persona == PersonaType.FRUSTRATED_USER:
        return (
            f"I completely understand your frustration, and I want to make sure you get the best help possible. "
            f"I'm escalating your case to a senior support specialist who will be able to assist you directly.\n\n"
            f"📋 **Escalation Reference**: `{handoff.escalation_id}`\n"
            f"🔴 **Priority**: {handoff.priority}\n\n"
            f"A human agent will review your case and reach out to you shortly. "
            f"Your conversation history and all the details have been forwarded so you won't need to repeat anything. "
            f"We're committed to resolving this for you."
        )
    elif persona.persona == PersonaType.BUSINESS_EXECUTIVE:
        return (
            f"I'm escalating this to a dedicated specialist to ensure you receive a comprehensive resolution.\n\n"
            f"📋 **Escalation Reference**: `{handoff.escalation_id}`\n"
            f"🔴 **Priority**: {handoff.priority}\n\n"
            f"**Next Steps:**\n"
            f"- A specialist will review your case within the timeframe specified by your support tier\n"
            f"- All conversation context has been forwarded\n"
            f"- You'll receive a direct follow-up with resolution details"
        )
    else:
        return (
            f"I'm connecting you with a human support specialist who can provide more detailed assistance.\n\n"
            f"📋 **Escalation Reference**: `{handoff.escalation_id}`\n"
            f"🔴 **Priority**: {handoff.priority}\n\n"
            f"Your conversation history and technical context have been forwarded to the specialist. "
            f"They'll have full visibility into your issue and the documentation we've reviewed."
        )


# ── Build the Workflow Graph ──────────────────────────────────

def build_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("persona_detection", persona_detection_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("escalation_check", escalation_check_node)
    workflow.add_node("response_generation", response_generation_node)
    workflow.add_node("handoff", handoff_node)
    workflow.add_node("output", output_node)

    # Define edges
    workflow.set_entry_point("persona_detection")
    workflow.add_edge("persona_detection", "retrieval")
    workflow.add_edge("retrieval", "escalation_check")

    # Conditional edge: escalate or respond
    workflow.add_conditional_edges(
        "escalation_check",
        should_escalate,
        {
            "handoff": "handoff",
            "respond": "response_generation",
        },
    )

    workflow.add_edge("response_generation", "output")
    workflow.add_edge("handoff", "output")
    workflow.add_edge("output", END)

    return workflow


# ── Main Agent Class ──────────────────────────────────────────

class SupportAgent:
    """
    The main support agent that orchestrates the entire workflow.
    Provides a simple interface for processing user messages.
    """

    def __init__(self):
        self.workflow = build_workflow()
        self.graph = self.workflow.compile()
        self.store = ConversationStore()
        logger.info("Support Agent initialized with LangGraph workflow")

    def create_session(self) -> str:
        """Create a new conversation session."""
        return self.store.create_session()

    def process_message(
        self,
        user_message: str,
        session_id: str,
    ) -> AgentResponse:
        """
        Process a user message through the full workflow.

        Args:
            user_message: The user's input message
            session_id: Active conversation session ID

        Returns:
            AgentResponse with all details
        """
        # Get conversation state
        conversation_history = self.store.get_history(session_id)
        turn_number = self.store.get_turn_count(session_id) + 1
        frustration_count = self.store.get_frustration_count(session_id)

        # Build initial state
        initial_state: AgentState = {
            "user_message": user_message,
            "conversation_history": conversation_history,
            "session_id": session_id,
            "turn_number": turn_number,
            "frustration_count": frustration_count,
            "persona": None,
            "retrieval": None,
            "escalation": None,
            "response_text": "",
            "handoff_summary": None,
            "final_response": None,
        }

        # Execute the workflow
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing message (session={session_id}, turn={turn_number})")
        logger.info(f"User: {user_message[:100]}...")
        logger.info(f"{'='*60}")

        result = self.graph.invoke(initial_state)
        response: AgentResponse = result["final_response"]

        # Persist conversation turns
        user_turn = ConversationTurn(
            role="user",
            content=user_message,
            persona=response.persona.persona,
            sentiment=response.persona.sentiment,
        )
        self.store.add_turn(session_id, user_turn, turn_number * 2 - 1)

        assistant_turn = ConversationTurn(
            role="assistant",
            content=response.response_text,
            sources_used=[d.source for d in response.retrieval.documents],
            was_escalated=response.escalation.should_escalate,
        )
        self.store.add_turn(session_id, assistant_turn, turn_number * 2)

        # Update frustration count
        self.store.update_frustration_count(session_id, result["frustration_count"])

        # Mark as escalated if needed
        if response.escalation.should_escalate:
            self.store.mark_escalated(session_id)

        return response
