"""
ChromaDB vector store for document storage and retrieval.
"""

import os
from typing import Optional

import chromadb
from langchain_core.documents import Document

from config.settings import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, TOP_K_RETRIEVAL
from src.knowledge_base.embeddings import embed_texts, embed_query
from src.models.schemas import RetrievedDocument, RetrievalResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """ChromaDB-backed vector store for the knowledge base."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or str(CHROMA_DB_DIR)
        self.collection_name = collection_name or CHROMA_COLLECTION_NAME

        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"VectorStore ready: {self.collection_name} "
            f"({self.collection.count()} existing documents)"
        )

    def add_documents(self, documents: list[Document]) -> int:
        """
        Add chunked documents to the vector store.
        Returns the number of documents added.
        """
        if not documents:
            logger.warning("No documents to add")
            return 0

        texts = [doc.page_content for doc in documents]
        metadatas = []
        ids = []

        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "unknown")
            chunk_idx = doc.metadata.get("chunk_index", i)
            doc_id = f"{source}_chunk_{chunk_idx}"
            ids.append(doc_id)
            metadatas.append({
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 1),
                "section": doc.metadata.get("section", ""),
                "chunk_index": doc.metadata.get("chunk_index", 0),
                "file_type": doc.metadata.get("file_type", "unknown"),
            })

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = embed_texts(texts)

        # Add to ChromaDB in batches
        batch_size = 500
        added = 0
        for start in range(0, len(texts), batch_size):
            end = min(start + batch_size, len(texts))
            self.collection.upsert(
                ids=ids[start:end],
                documents=texts[start:end],
                embeddings=embeddings[start:end],
                metadatas=metadatas[start:end],
            )
            added += end - start
            logger.info(f"  Added batch {start}-{end} ({added}/{len(texts)})")

        logger.info(f"Total documents in store: {self.collection.count()}")
        return added

    def query(self, query_text: str, top_k: Optional[int] = None) -> RetrievalResult:
        """
        Query the vector store and return ranked results.
        """
        top_k = top_k or TOP_K_RETRIEVAL

        if self.collection.count() == 0:
            logger.warning("Vector store is empty — no documents to search")
            return RetrievalResult(query=query_text)

        query_embedding = embed_query(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved_docs = []
        if results["documents"] and results["documents"][0]:
            for i, doc_text in enumerate(results["documents"][0]):
                # ChromaDB returns cosine distance; convert to similarity
                distance = results["distances"][0][i]
                similarity = 1 - distance  # cosine distance to similarity

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                retrieved_docs.append(
                    RetrievedDocument(
                        content=doc_text,
                        source=metadata.get("source", "unknown"),
                        page=metadata.get("page"),
                        section=metadata.get("section"),
                        chunk_index=metadata.get("chunk_index", 0),
                        similarity_score=max(0.0, min(1.0, similarity)),
                    )
                )

        # Sort by similarity (highest first)
        retrieved_docs.sort(key=lambda d: d.similarity_score, reverse=True)

        scores = [d.similarity_score for d in retrieved_docs]
        return RetrievalResult(
            documents=retrieved_docs,
            top_score=max(scores) if scores else 0.0,
            avg_score=sum(scores) / len(scores) if scores else 0.0,
            query=query_text,
        )

    def get_count(self) -> int:
        """Return the total number of documents in the store."""
        return self.collection.count()

    def reset(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store reset complete")
