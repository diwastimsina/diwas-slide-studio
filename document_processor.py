import pypdf
import docx
import re
from pathlib import Path


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import io
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    import io
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, max_chars: int = 6000) -> str:
    """Trim to a manageable size for the LLM context window."""
    if len(text) <= max_chars:
        return text
    # Keep start, middle sample, and end for better coverage
    third = max_chars // 3
    start = text[:third]
    mid_start = len(text) // 2 - third // 2
    middle = text[mid_start: mid_start + third]
    end = text[-third:]
    return f"{start}\n\n[...]\n\n{middle}\n\n[...]\n\n{end}"
