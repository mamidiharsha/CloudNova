"""
End-to-end tests for the CloudNova Support Agent pipeline.
"""

import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDocumentLoader:
    """Test document loading functionality."""

    def test_load_markdown(self):
        from src.knowledge_base.document_loader import load_markdown
        from config.settings import DATA_DIR

        md_file = os.path.join(str(DATA_DIR), "getting_started.md")
        if os.path.exists(md_file):
            docs = load_markdown(md_file)
            assert len(docs) > 0
            assert docs[0].metadata["source"] == "getting_started.md"
            assert docs[0].metadata["file_type"] == "md"
            assert len(docs[0].page_content) > 100

    def test_load_text(self):
        from src.knowledge_base.document_loader import load_text
        from config.settings import DATA_DIR

        txt_file = os.path.join(str(DATA_DIR), "password_reset_guide.txt")
        if os.path.exists(txt_file):
            docs = load_text(txt_file)
            assert len(docs) == 1
            assert "password" in docs[0].page_content.lower()

    def test_load_all_documents(self):
        from src.knowledge_base.document_loader import load_all_documents

        docs = load_all_documents()
        assert len(docs) >= 10, f"Expected at least 10 documents, got {len(docs)}"


class TestChunker:
    """Test document chunking."""

    def test_chunk_documents(self):
        from langchain_core.documents import Document
        from src.knowledge_base.chunker import chunk_documents

        test_docs = [
            Document(
                page_content="A " * 300,  # Long text that needs chunking
                metadata={"source": "test.md", "page": 1, "file_type": "md"},
            )
        ]
        chunks = chunk_documents(test_docs, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 1, "Expected multiple chunks from long document"

        for chunk in chunks:
            assert "source" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "section" in chunk.metadata

    def test_preserves_metadata(self):
        from langchain_core.documents import Document
        from src.knowledge_base.chunker import chunk_documents

        test_docs = [
            Document(
                page_content="Short content",
                metadata={"source": "test.pdf", "page": 5, "file_type": "pdf"},
            )
        ]
        chunks = chunk_documents(test_docs)
        assert chunks[0].metadata["source"] == "test.pdf"
        assert chunks[0].metadata["page"] == 5


class TestSchemas:
    """Test Pydantic models."""

    def test_persona_result(self):
        from src.models.schemas import PersonaResult, PersonaType, SentimentType

        result = PersonaResult(
            persona=PersonaType.TECHNICAL_EXPERT,
            confidence=0.85,
            reasoning="Uses technical terminology",
            sentiment=SentimentType.NEUTRAL,
        )
        assert result.persona == PersonaType.TECHNICAL_EXPERT
        assert result.confidence == 0.85

    def test_retrieval_result(self):
        from src.models.schemas import RetrievalResult, RetrievedDocument

        doc = RetrievedDocument(
            content="Test content",
            source="test.md",
            chunk_index=0,
            similarity_score=0.8,
        )
        result = RetrievalResult(
            documents=[doc],
            top_score=0.8,
            avg_score=0.8,
            query="test query",
        )
        assert len(result.documents) == 1
        assert result.top_score == 0.8

    def test_escalation_decision(self):
        from src.models.schemas import EscalationDecision, EscalationReason

        decision = EscalationDecision(
            should_escalate=True,
            reasons=[EscalationReason.LOW_CONFIDENCE],
            details="Score below threshold",
        )
        assert decision.should_escalate is True
        assert len(decision.reasons) == 1

    def test_handoff_summary(self):
        from src.models.schemas import HandoffSummary, PersonaType, SentimentType

        summary = HandoffSummary(
            escalation_id="ESC-TEST-001",
            persona=PersonaType.FRUSTRATED_USER,
            sentiment=SentimentType.ANGRY,
            issue_summary="Cannot reset password",
            documents_used=["password_reset_guide.txt"],
            attempted_steps=["Tried reset link"],
            escalation_reasons=["Persistent frustration"],
            recommended_next_steps=["Check account lock status"],
            priority="HIGH",
        )
        assert summary.persona == PersonaType.FRUSTRATED_USER
        assert summary.priority == "HIGH"


class TestConversationStore:
    """Test conversation storage."""

    def test_session_lifecycle(self):
        from src.utils.conversation_store import ConversationStore
        from src.models.schemas import ConversationTurn, PersonaType, SentimentType

        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp_path = tmp.name
        tmp.close()  # Close handle so SQLite can use it

        store = ConversationStore(db_path=tmp_path)

        session_id = store.create_session()
        assert len(session_id) == 8

        turn = ConversationTurn(
            role="user",
            content="Hello, I need help",
            persona=PersonaType.TECHNICAL_EXPERT,
            sentiment=SentimentType.NEUTRAL,
        )
        store.add_turn(session_id, turn, 1)

        history = store.get_history(session_id)
        assert len(history) == 1
        assert history[0]["role"] == "user"

        # Cleanup — ignore if Windows holds the lock
        try:
            os.unlink(tmp_path)
        except PermissionError:
            pass


class TestEscalationKeywords:
    """Test escalation keyword detection."""

    def test_sensitive_topics(self):
        from config.settings import SENSITIVE_TOPICS

        test_message = "I need a refund for my last payment"
        msg_lower = test_message.lower()
        found = any(topic in msg_lower for topic in SENSITIVE_TOPICS)
        assert found, "Should detect 'refund' as a sensitive topic"

    def test_escalation_keywords(self):
        from config.settings import ESCALATION_KEYWORDS

        test_message = "Let me speak to a human please"
        msg_lower = test_message.lower()
        found = any(kw in msg_lower for kw in ESCALATION_KEYWORDS)
        assert found, "Should detect 'speak to a human' as an escalation keyword"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
