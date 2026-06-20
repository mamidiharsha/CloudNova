"""
Embedding model wrapper using Sentence Transformers.
Implements a LangChain-compatible interface for ChromaDB integration.
"""

from typing import Optional

from sentence_transformers import SentenceTransformer

from config.settings import EMBEDDING_MODEL
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level cache for the embedding model
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Get or create the singleton embedding model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Embedding model loaded (dim={_model.get_embedding_dimension()})")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Generate an embedding for a single query."""
    model = get_model()
    embedding = model.encode(query, convert_to_numpy=True)
    return embedding.tolist()


def get_embedding_dimension() -> int:
    """Return the dimension of the embeddings."""
    model = get_model()
    return model.get_embedding_dimension()
