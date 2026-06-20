"""
CloudNova Support Agent — Streamlit Web UI
Premium chat-style interface with persona detection, source citations, and escalation alerts.

Usage:
    streamlit run app.py
"""

import json
import streamlit as st

from src.agents.workflow import SupportAgent
from src.models.schemas import PersonaType, SentimentType, FeedbackType, FeedbackRecord
from src.utils.conversation_store import ConversationStore


# ── Page Configuration ────────────────────────────────────────

st.set_page_config(
    page_title="CloudNova Support Agent",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for premium look ───────────────────────────────

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* Chat messages */
    .stChatMessage {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* Input styling */
    .stChatInput > div {
        border-color: rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
    }

    /* Persona badges */
    .persona-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .persona-technical {
        background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.1));
        color: #60a5fa;
        border: 1px solid rgba(59,130,246,0.3);
    }
    .persona-frustrated {
        background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.1));
        color: #f87171;
        border: 1px solid rgba(239,68,68,0.3);
    }
    .persona-executive {
        background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(139,92,246,0.1));
        color: #a78bfa;
        border: 1px solid rgba(139,92,246,0.3);
    }

    /* Confidence meter */
    .confidence-bar {
        height: 6px;
        border-radius: 3px;
        background: rgba(255,255,255,0.1);
        margin: 8px 0;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }

    /* Source cards */
    .source-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 10px 14px;
        margin: 4px 0;
        font-size: 0.85rem;
    }
    .source-score {
        float: right;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .score-high { color: #34d399; }
    .score-medium { color: #fbbf24; }
    .score-low { color: #f87171; }

    /* Escalation banner */
    .escalation-banner {
        background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 10px;
        padding: 16px;
        margin: 10px 0;
    }

    /* Title styling */
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .main-subtitle {
        color: rgba(255,255,255,0.5);
        font-size: 0.9rem;
        margin-top: 0;
    }

    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #60a5fa;
    }
    .metric-label {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Hide default header and footer */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        background: rgba(99, 102, 241, 0.1) !important;
        color: #a5b4fc !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: rgba(99, 102, 241, 0.25) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
        color: rgba(255,255,255,0.7) !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Initialize Session State ──────────────────────────────────

def init_session_state():
    if "agent" not in st.session_state:
        st.session_state.agent = SupportAgent()
    if "session_id" not in st.session_state:
        st.session_state.session_id = st.session_state.agent.create_session()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "responses" not in st.session_state:
        st.session_state.responses = []
    if "current_persona" not in st.session_state:
        st.session_state.current_persona = None
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "escalated" not in st.session_state:
        st.session_state.escalated = False
    if "latest_response" not in st.session_state:
        st.session_state.latest_response = None


init_session_state()


# ── Persona Badge Helper ─────────────────────────────────────

def get_persona_badge_html(persona_type: PersonaType) -> str:
    icons = {
        PersonaType.TECHNICAL_EXPERT: "🔧",
        PersonaType.FRUSTRATED_USER: "😤",
        PersonaType.BUSINESS_EXECUTIVE: "💼",
    }
    css_classes = {
        PersonaType.TECHNICAL_EXPERT: "persona-technical",
        PersonaType.FRUSTRATED_USER: "persona-frustrated",
        PersonaType.BUSINESS_EXECUTIVE: "persona-executive",
    }
    icon = icons.get(persona_type, "🤖")
    css = css_classes.get(persona_type, "persona-technical")
    return f'<span class="persona-badge {css}">{icon} {persona_type.value}</span>'


def get_score_class(score: float) -> str:
    if score > 0.5:
        return "score-high"
    elif score > 0.3:
        return "score-medium"
    return "score-low"


# ── Sidebar ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<p class="main-title">☁️ CloudNova</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">AI Support Agent</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Session controls
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.session_id = st.session_state.agent.create_session()
        st.session_state.messages = []
        st.session_state.responses = []
        st.session_state.current_persona = None
        st.session_state.turn_count = 0
        st.session_state.escalated = False
        st.session_state.latest_response = None
        st.rerun()

    st.markdown(f"**Session:** `{st.session_state.session_id}`")
    st.markdown(f"**Turns:** {st.session_state.turn_count}")

    st.markdown("---")

    # Current persona display
    st.markdown("### 🎭 Detected Persona")
    if st.session_state.current_persona:
        persona = st.session_state.current_persona
        st.markdown(get_persona_badge_html(persona.persona), unsafe_allow_html=True)

        # Confidence bar
        conf_color = "#34d399" if persona.confidence > 0.7 else "#fbbf24" if persona.confidence > 0.5 else "#f87171"
        st.markdown(f"""
            <div style="margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span style="color: rgba(255,255,255,0.5);">Confidence</span>
                    <span style="color: {conf_color}; font-weight: 600;">{persona.confidence:.0%}</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {persona.confidence*100}%; background: {conf_color};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Sentiment
        sentiment_icons = {
            SentimentType.POSITIVE: "😊",
            SentimentType.NEUTRAL: "😐",
            SentimentType.NEGATIVE: "😟",
            SentimentType.ANGRY: "😡",
        }
        sent_icon = sentiment_icons.get(persona.sentiment, "😐")
        st.markdown(f"**Sentiment:** {sent_icon} {persona.sentiment.value}")
        st.markdown(f"*{persona.reasoning}*")
    else:
        st.markdown("*No messages yet*")

    st.markdown("---")

    # Escalation status
    st.markdown("### 🚨 Escalation Status")
    if st.session_state.escalated:
        st.markdown("🔴 **ESCALATED** — Transferred to human agent")
    else:
        st.markdown("🟢 **Normal** — AI handling")

    st.markdown("---")

    # Retrieved sources (latest)
    st.markdown("### 📚 Retrieved Sources")
    if st.session_state.latest_response and st.session_state.latest_response.retrieval.documents:
        for doc in st.session_state.latest_response.retrieval.documents[:5]:
            score_class = get_score_class(doc.similarity_score)
            st.markdown(f"""
                <div class="source-card">
                    <span class="source-score {score_class}">{doc.similarity_score:.3f}</span>
                    📄 {doc.source}
                    <br><span style="color: rgba(255,255,255,0.4); font-size: 0.8rem;">{(doc.section or '')[:35]}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("*No sources retrieved yet*")

    st.markdown("---")

    # Settings expander
    with st.expander("⚙️ Settings"):
        st.markdown("**Escalation Thresholds**")
        st.slider("Retrieval Confidence", 0.0, 1.0, 0.35, 0.05, key="conf_threshold", disabled=True)
        st.slider("Max Frustration Turns", 1, 10, 3, 1, key="max_frust", disabled=True)
        st.markdown("*Configure in `.env` file*")


# ── Main Chat Area ────────────────────────────────────────────

# Header
col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="font-size: 1.8rem; font-weight: 700;
                       background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       margin-bottom: 4px;">
                CloudNova Support Agent
            </h1>
            <p style="color: rgba(255,255,255,0.4); font-size: 0.9rem;">
                Persona-adaptive AI support powered by RAG
            </p>
        </div>
    """, unsafe_allow_html=True)

# Metrics row
if st.session_state.turn_count > 0:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.turn_count}</div>
                <div class="metric-label">Turns</div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        persona_val = st.session_state.current_persona.persona.value.split()[0] if st.session_state.current_persona else "—"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{persona_val}</div>
                <div class="metric-label">Persona</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        conf = f"{st.session_state.current_persona.confidence:.0%}" if st.session_state.current_persona else "—"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{conf}</div>
                <div class="metric-label">Confidence</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        status = "🔴 Escalated" if st.session_state.escalated else "🟢 Active"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1rem;">{status}</div>
                <div class="metric-label">Status</div>
            </div>
        """, unsafe_allow_html=True)

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and i // 2 < len(st.session_state.responses):
            resp_idx = i // 2
            resp = st.session_state.responses[resp_idx]

            # Persona badge
            st.markdown(get_persona_badge_html(resp.persona.persona), unsafe_allow_html=True)

            # Response text
            st.markdown(msg["content"])

            # Sources expander
            if resp.retrieval.documents:
                with st.expander(f"📚 Sources ({len(resp.retrieval.documents)} documents)"):
                    for doc in resp.retrieval.documents[:5]:
                        score_class = get_score_class(doc.similarity_score)
                        st.markdown(f"""
                            <div class="source-card">
                                <span class="source-score {score_class}">{doc.similarity_score:.3f}</span>
                                📄 **{doc.source}**
                                {f' · Page {doc.page}' if doc.page else ''}
                                {f' · {doc.section[:50]}' if doc.section else ''}
                            </div>
                        """, unsafe_allow_html=True)

            # Escalation alert
            if resp.escalation.should_escalate:
                st.markdown(f"""
                    <div class="escalation-banner">
                        <strong>🚨 Escalated to Human Agent</strong><br>
                        <span style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">
                            {resp.escalation.details}
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                if resp.handoff_summary:
                    with st.expander("📋 Handoff Summary"):
                        hs = resp.handoff_summary
                        st.json(hs.model_dump(exclude={"conversation_history"}))

            # Feedback buttons
            col_a, col_b, col_c = st.columns([1, 1, 8])
            with col_a:
                if st.button("👍", key=f"thumbs_up_{i}"):
                    store = ConversationStore()
                    store.add_feedback(FeedbackRecord(
                        session_id=st.session_state.session_id,
                        turn_number=resp_idx + 1,
                        feedback=FeedbackType.THUMBS_UP,
                    ))
                    st.toast("Thanks for the feedback! 👍")
            with col_b:
                if st.button("👎", key=f"thumbs_down_{i}"):
                    store = ConversationStore()
                    store.add_feedback(FeedbackRecord(
                        session_id=st.session_state.session_id,
                        turn_number=resp_idx + 1,
                        feedback=FeedbackType.THUMBS_DOWN,
                    ))
                    st.toast("Thanks for the feedback. We'll improve! 👎")
        else:
            st.markdown(msg["content"])


# ── Chat Input ────────────────────────────────────────────────

if prompt := st.chat_input("Type your question or describe your issue..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with agent
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your query..."):
            try:
                response = st.session_state.agent.process_message(
                    prompt, st.session_state.session_id
                )

                # Update session state
                st.session_state.turn_count += 1
                st.session_state.current_persona = response.persona
                st.session_state.latest_response = response
                st.session_state.responses.append(response)

                if response.escalation.should_escalate:
                    st.session_state.escalated = True

                # Display persona badge
                st.markdown(get_persona_badge_html(response.persona.persona), unsafe_allow_html=True)

                # Display response
                st.markdown(response.response_text)

                # Sources
                if response.retrieval.documents:
                    with st.expander(f"📚 Sources ({len(response.retrieval.documents)} documents)"):
                        for doc in response.retrieval.documents[:5]:
                            score_class = get_score_class(doc.similarity_score)
                            st.markdown(f"""
                                <div class="source-card">
                                    <span class="source-score {score_class}">{doc.similarity_score:.3f}</span>
                                    📄 **{doc.source}**
                                    {f' · Page {doc.page}' if doc.page else ''}
                                    {f' · {doc.section[:50]}' if doc.section else ''}
                                </div>
                            """, unsafe_allow_html=True)

                # Escalation
                if response.escalation.should_escalate:
                    st.markdown(f"""
                        <div class="escalation-banner">
                            <strong>🚨 Escalated to Human Agent</strong><br>
                            <span style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">
                                {response.escalation.details}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                    if response.handoff_summary:
                        with st.expander("📋 Handoff Summary"):
                            st.json(response.handoff_summary.model_dump(exclude={"conversation_history"}))

                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.response_text,
                })

            except Exception as e:
                st.error(f"Error processing your message: {str(e)}")
                st.info("Make sure you've run `python ingest.py` and set your `GOOGLE_API_KEY` in the `.env` file.")

    st.rerun()
