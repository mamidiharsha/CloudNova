"""
Knowledge Base Ingestion Script
Loads documents from data/, chunks them, generates embeddings, and stores in ChromaDB.

Usage:
    python ingest.py
    python ingest.py --reset  # Clear existing data first
"""

import argparse
import sys
import os
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config.settings import DATA_DIR, CHROMA_DB_DIR
from src.knowledge_base.document_loader import load_all_documents
from src.knowledge_base.chunker import chunk_documents
from src.knowledge_base.vector_store import VectorStore
from src.utils.logger import get_logger

logger = get_logger("ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base documents")
    parser.add_argument("--reset", action="store_true", help="Reset the vector store before ingestion")
    args = parser.parse_args()

    print("=" * 60)
    print("  CloudNova Support Agent - Knowledge Base Ingestion")
    print("=" * 60)
    print()

    start_time = time.time()

    # Step 1: Load documents
    print(f"[LOAD] Loading documents from: {DATA_DIR}")
    documents = load_all_documents()

    if not documents:
        print("[ERROR] No documents found! Ensure the data/ directory contains supported files.")
        sys.exit(1)

    print(f"[OK] Loaded {len(documents)} document pages\n")

    # Step 2: Chunk documents
    print("[CHUNK] Chunking documents...")
    chunks = chunk_documents(documents)
    print(f"[OK] Created {len(chunks)} chunks\n")

    # Step 3: Calculate stats
    total_chars = sum(len(c.page_content) for c in chunks)
    avg_chunk_size = total_chars / len(chunks) if chunks else 0

    print("[STATS] Chunk Statistics:")
    print(f"   Total chunks:     {len(chunks)}")
    print(f"   Total characters: {total_chars:,}")
    print(f"   Avg chunk size:   {avg_chunk_size:.0f} chars")
    print()

    # Step 4: Store in vector database
    print("[DB] Initializing vector store...")
    vector_store = VectorStore()

    if args.reset:
        print("[RESET] Resetting vector store...")
        vector_store.reset()

    print("[EMBED] Generating embeddings and storing documents...")
    added = vector_store.add_documents(chunks)

    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print("  [DONE] Ingestion Complete!")
    print("=" * 60)
    print(f"   Documents loaded:  {len(documents)}")
    print(f"   Chunks created:    {len(chunks)}")
    print(f"   Vectors stored:    {added}")
    print(f"   Total in store:    {vector_store.get_count()}")
    print(f"   Storage location:  {CHROMA_DB_DIR}")
    print(f"   Time elapsed:      {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
