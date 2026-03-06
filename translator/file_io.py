"""File I/O: read Arabic source files and write translated output."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read an input file and return its text content.

    Supported formats: .txt, .pdf, .docx
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".txt":
        return _read_txt(p)
    elif suffix == ".pdf":
        return _read_pdf(p)
    elif suffix == ".docx":
        return _read_docx(p)
    else:
        raise ValueError(
            f"Unsupported file format '{suffix}'. Supported: .txt, .pdf, .docx"
        )


def _read_txt(path: Path) -> str:
    """Read a plain text file (UTF-8)."""
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required to read PDF files. "
            "Install it with: pip install PyMuPDF"
        )

    doc = fitz.open(str(path))
    pages: List[str] = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n\n".join(pages)


def _read_docx(path: Path) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docx is required to read DOCX files. "
            "Install it with: pip install python-docx"
        )

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_output(text: str, path: str) -> None:
    """Write the translated text to the output file (UTF-8)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Default output path helper
# ---------------------------------------------------------------------------

def default_output_path(input_path: str) -> str:
    """Generate a default output path from the input path.

    e.g.  book.pdf  →  book_translated.md
    """
    p = Path(input_path)
    return str(p.with_name(f"{p.stem}_translated.md"))


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, max_tokens: int = 1500) -> List[str]:
    """Split Arabic text into chunks of roughly *max_tokens* tokens.

    We approximate tokens as ``len(text) / 2`` for Arabic (conservative).
    Splits happen at paragraph boundaries (double newlines) first,
    then at sentence boundaries (period + space) if paragraphs are too long.
    """
    # Target character count (rough: 1 Arabic token ≈ 2 chars on average)
    max_chars = max_tokens * 2

    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_len = len(para)

        # If appending this paragraph would exceed the limit, flush current
        if current_len + para_len > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_len = 0

        # If a single paragraph exceeds the limit, split by sentences
        if para_len > max_chars:
            sentences = re.split(r"(?<=[.؟!])\s+", para)
            sub_chunk: List[str] = []
            sub_len = 0
            for sent in sentences:
                sent_len = len(sent)
                if sub_len + sent_len > max_chars and sub_chunk:
                    chunks.append(" ".join(sub_chunk))
                    sub_chunk = []
                    sub_len = 0
                sub_chunk.append(sent)
                sub_len += sent_len
            if sub_chunk:
                current_chunk.append(" ".join(sub_chunk))
                current_len += sub_len
        else:
            current_chunk.append(para)
            current_len += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
