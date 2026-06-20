"""
Multi-format document loader supporting PDF, TXT, MD, and DOCX files.
"""

import os
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_pdf(file_path: str) -> list[Document]:
    """Load a PDF file and return pages as documents."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    documents = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            documents.append(
                Document(
                    page_content=text.strip(),
                    metadata={
                        "source": os.path.basename(file_path),
                        "page": i + 1,
                        "file_type": "pdf",
                    },
                )
            )
    return documents


def load_text(file_path: str) -> list[Document]:
    """Load a plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return [
        Document(
            page_content=content,
            metadata={
                "source": os.path.basename(file_path),
                "page": 1,
                "file_type": "txt",
            },
        )
    ]


def load_markdown(file_path: str) -> list[Document]:
    """Load a markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return [
        Document(
            page_content=content,
            metadata={
                "source": os.path.basename(file_path),
                "page": 1,
                "file_type": "md",
            },
        )
    ]


def load_docx(file_path: str) -> list[Document]:
    """Load a DOCX file."""
    import docx2txt

    content = docx2txt.process(file_path)
    return [
        Document(
            page_content=content,
            metadata={
                "source": os.path.basename(file_path),
                "page": 1,
                "file_type": "docx",
            },
        )
    ]


# Mapping of file extensions to loader functions
LOADERS = {
    ".pdf": load_pdf,
    ".txt": load_text,
    ".md": load_markdown,
    ".docx": load_docx,
}


def load_document(file_path: str) -> list[Document]:
    """Auto-detect file type and load document."""
    ext = Path(file_path).suffix.lower()
    loader = LOADERS.get(ext)
    if not loader:
        logger.warning(f"Unsupported file type: {ext} for {file_path}")
        return []
    try:
        docs = loader(file_path)
        logger.info(f"Loaded {len(docs)} page(s) from {os.path.basename(file_path)}")
        return docs
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return []


def load_all_documents(data_dir: Optional[str] = None) -> list[Document]:
    """Load all supported documents from the data directory."""
    data_dir = data_dir or str(DATA_DIR)
    all_docs = []

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return all_docs

    supported_extensions = set(LOADERS.keys())
    files = sorted(os.listdir(data_dir))

    for filename in files:
        ext = Path(filename).suffix.lower()
        if ext in supported_extensions:
            file_path = os.path.join(data_dir, filename)
            docs = load_document(file_path)
            all_docs.extend(docs)

    logger.info(f"Total documents loaded: {len(all_docs)} from {data_dir}")
    return all_docs
