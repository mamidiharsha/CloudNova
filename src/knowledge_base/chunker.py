"""
Document chunking with metadata preservation.
Uses RecursiveCharacterTextSplitter for intelligent splitting.
"""

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_section_name(text: str) -> str:
    """Extract the most relevant section heading from a chunk of text."""
    # Look for Markdown headings
    md_match = re.search(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)
    if md_match:
        return md_match.group(1).strip()

    # Look for uppercase section headers (for TXT files)
    upper_match = re.search(r"^([A-Z][A-Z\s\-:]{5,})$", text, re.MULTILINE)
    if upper_match:
        return upper_match.group(1).strip().title()

    # Use the first line as a fallback
    first_line = text.strip().split("\n")[0][:80]
    return first_line


def chunk_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """
    Split documents into overlapping chunks while preserving metadata.

    Each chunk carries:
    - source: Original filename
    - page: Page number (if from PDF)
    - section: Detected section heading
    - chunk_index: Position within the source document
    """
    chunk_size = chunk_size or CHUNK_SIZE
    chunk_overlap = chunk_overlap or CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    all_chunks: list[Document] = []
    chunk_counts: dict[str, int] = {}

    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", 1)
        file_type = doc.metadata.get("file_type", "unknown")

        if source not in chunk_counts:
            chunk_counts[source] = 0

        splits = splitter.split_text(doc.page_content)

        for split_text in splits:
            if not split_text.strip():
                continue

            section = extract_section_name(split_text)
            chunk_index = chunk_counts[source]
            chunk_counts[source] += 1

            chunk_doc = Document(
                page_content=split_text,
                metadata={
                    "source": source,
                    "page": page,
                    "section": section,
                    "chunk_index": chunk_index,
                    "file_type": file_type,
                },
            )
            all_chunks.append(chunk_doc)

    logger.info(
        f"Chunked {len(documents)} documents into {len(all_chunks)} chunks "
        f"(size={chunk_size}, overlap={chunk_overlap})"
    )
    for source, count in sorted(chunk_counts.items()):
        logger.info(f"  {source}: {count} chunks")

    return all_chunks
