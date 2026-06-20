# CloudNova Support Agent

> **Persona-Adaptive AI Customer Support Agent** powered by LLMs, RAG, and Human-in-the-Loop Escalation

An intelligent customer support system for the CloudNova cloud platform that automatically detects customer personas, retrieves relevant documentation, generates tailored responses, and escalates complex issues to human agents — all with full conversation memory and a premium web interface.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Gemini](https://img.shields.io/badge/LLM-Gemini_2.0_Flash-orange?logo=google)
![LangGraph](https://img.shields.io/badge/Framework-LangGraph-green)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red?logo=streamlit)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Persona Detection](#persona-detection)
- [RAG Pipeline](#rag-pipeline)
- [Escalation Logic](#escalation-logic)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Example Queries](#example-queries)
- [Bonus Features](#bonus-features)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)

---

## Project Overview

CloudNova Support Agent is an AI-powered customer support system that:

1. **Detects Customer Personas** — Classifies users as Technical Expert, Frustrated User, or Business Executive using LLM-based analysis with sentiment detection
2. **Retrieves Relevant Knowledge** — Uses a RAG pipeline with ChromaDB and Sentence Transformers to ground responses in a 16-document knowledge base
3. **Adapts Response Tone** — Generates persona-specific responses with different system prompts for each persona
4. **Escalates Intelligently** — Routes conversations to human agents based on 6 configurable triggers
5. **Provides Handoff Summaries** — Generates structured JSON summaries for human agents with full context

The system is built around a **LangGraph state machine** with typed state and conditional routing.

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11+ | Core runtime |
| **LLM** | Google Gemini 2.0 Flash | Persona detection and response generation |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) | Local embedding generation (384 dimensions) |
| **Vector Database** | ChromaDB | Semantic document retrieval |
| **Agent Framework** | LangGraph | Workflow orchestration with typed state |
| **Orchestration** | LangChain | Document processing utilities |
| **Web UI** | Streamlit | Chat interface |
| **CLI** | Rich | Terminal UI with formatting |
| **Storage** | SQLite | Conversation persistence |
| **Document Loaders** | PyPDF, docx2txt | PDF, DOCX, TXT, MD support |

---

## Architecture

```
User Message
    │
    ▼
┌─────────────────────┐
│  1. Persona Detection│  ← Gemini classifies the customer type
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. KB Retrieval     │  ← Searches ChromaDB for relevant docs
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. Escalation Check │  ← Checks 6 triggers
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐ ┌──────────┐
│Response│ │ Human    │
│Generate│ │ Handoff  │
└───┬────┘ └────┬─────┘
    │           │
    └─────┬─────┘
          ▼
┌─────────────────────┐
│  5. Output Assembly  │
└─────────────────────┘
```

The workflow is implemented as a **LangGraph `StateGraph`** with typed state (`AgentState`) and conditional edges for the escalation/response routing.

---

## Persona Detection

| Persona | Key Indicators | Response Style |
|---------|---------------|----------------|
| **Technical Expert** | API, configuration, logs, error codes, debugging | Detailed root cause analysis, step-by-step troubleshooting, code examples |
| **Frustrated User** | Emotional language, exclamation marks, CAPS, urgency | Empathetic opening, simple language, immediate actionable steps |
| **Business Executive** | Business impact, timeline, SLA, operations, revenue | Concise bullets, impact-focused, timeline estimates |

- LLM-based classification using Gemini with structured JSON output
- Rule-based fallback when LLM is unavailable
- Persona re-detected on every turn to capture shifts
- Sentiment analysis: positive / neutral / negative / angry

---

## RAG Pipeline

```
data/ (16 documents) → Document Loader → Text Splitter (500 chars, 100 overlap)
    → Sentence Transformer Embeddings (384-dim) → ChromaDB (cosine similarity)
```

- **16 knowledge base documents**: 12 Markdown + 1 PDF + 1 DOCX + 1 TXT
- **Chunking**: RecursiveCharacterTextSplitter with section detection
- **Embeddings**: `all-MiniLM-L6-v2` running locally
- **Retrieval**: Top-5 results with cosine similarity scoring

---

## Escalation Logic

| # | Trigger | Configurable |
|---|---------|:---:|
| 1 | **Explicit request** — "speak to a human", "escalate", etc. | Yes |
| 2 | **No relevant docs** — zero documents retrieved | Built-in |
| 3 | **Low confidence** — top score below threshold (default: 0.35) | Yes |
| 4 | **Persistent frustration** — frustrated for 3+ consecutive turns | Yes |
| 5 | **Sensitive topic** — refund, legal, billing dispute, etc. | Yes |
| 6 | **Angry sentiment** — angry sentiment with high confidence | Built-in |

When escalation triggers, the system generates a structured **handoff summary** with escalation ID, priority level, issue summary, attempted steps, and recommended next steps.

---

## Setup Instructions

### Prerequisites
- Python 3.11 or higher
- Google Gemini API Key ([Get free key](https://aistudio.google.com/apikey))

### Installation
```bash
# Clone and enter directory
git clone <repository-url>
cd CloudNova

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Generate PDF and DOCX documents
python generate_docs.py

# Ingest knowledge base
python ingest.py

# Run the application
streamlit run app.py           # Web UI
python cli.py                  # CLI
```

---

## Usage

### Streamlit Web UI
```bash
streamlit run app.py
```
Features: Chat interface, real-time persona detection, confidence meter, source citations, escalation alerts, feedback buttons.

### CLI
```bash
python cli.py
```
Commands: `/quit` · `/reset` · `/export` (exports handoff summary as JSON)

---

## Example Queries

| Query | Expected Persona | Expected Behavior |
|-------|:---:|---|
| "Can you explain the API authentication failure with OAuth2?" | Technical Expert | Detailed OAuth2 flow with error codes |
| "I've been trying to reset my password for THREE DAYS!!!" | Frustrated User | Empathetic response, simple steps |
| "What's the business impact and how does the SLA cover us?" | Business Executive | Concise bullets, SLA references |
| "I need a full refund for last month's billing" | Escalation | Sensitive topic triggers handoff |
| "Let me speak to a human support agent" | Escalation | Explicit request triggers handoff |

---

## Bonus Features

| Feature | Implementation |
|---------|---------------|
| Sentiment Analysis | Built into persona detection (positive/neutral/negative/angry) |
| Multi-turn Memory | SQLite-backed conversation history |
| LangGraph Workflow | State machine with typed `AgentState` and conditional edges |
| Confidence Scoring | Retrieval similarity scores + persona detection confidence |
| Feedback Collection | Thumbs up/down in Streamlit UI, stored in SQLite |
| Agentic Architecture | Separate agents for detection, retrieval, generation, escalation |

---

## Project Structure

```
CloudNova/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── generate_docs.py               # PDF/DOCX generation script
├── ingest.py                      # Knowledge base ingestion
├── cli.py                         # CLI interface (Rich)
├── app.py                         # Web UI (Streamlit)
├── config/
│   └── settings.py                # Central configuration
├── data/                          # 16 knowledge base documents
├── src/
│   ├── knowledge_base/
│   │   ├── document_loader.py     # Multi-format document loading
│   │   ├── chunker.py             # Recursive text splitting
│   │   ├── embeddings.py          # Sentence Transformer embeddings
│   │   └── vector_store.py        # ChromaDB vector store
│   ├── agents/
│   │   ├── persona_detector.py    # LLM-based persona classification
│   │   ├── response_generator.py  # Persona-adaptive responses
│   │   ├── escalation_manager.py  # Escalation logic + handoff
│   │   └── workflow.py            # LangGraph state machine
│   ├── models/
│   │   └── schemas.py             # Pydantic data models
│   └── utils/
│       ├── logger.py              # Structured logging
│       └── conversation_store.py  # SQLite persistence
└── tests/
    └── test_pipeline.py           # Unit tests (12 tests)
```

---

## Known Limitations

1. **Single LLM Provider** — Currently only supports Google Gemini
2. **Static Knowledge Base** — Documents are ingested once; no automatic re-indexing
3. **English Only** — System works best with English text
4. **No Ticketing Integration** — Handoff summaries generated but not sent to external systems
5. **No Analytics Dashboard** — Feedback collected but not visualized

---

## License

This project was built for educational and assessment purposes.
