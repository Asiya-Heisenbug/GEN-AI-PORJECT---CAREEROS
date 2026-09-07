from io import BytesIO
from typing import BinaryIO

from docx import Document
from pypdf import PdfReader


def _content(file: BinaryIO) -> bytes:
    if hasattr(file, "getvalue"):
        return file.getvalue()
    return file.read()


def extract_text(file: BinaryIO) -> str:
    """Extract text from a PDF or DOCX upload without consuming upload state."""
    filename = getattr(file, "name", "").lower()
    content = _content(file)

    if filename.endswith(".pdf"):
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages).strip()

    if filename.endswith(".docx"):
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()

    raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def render_pdf_pages(file: BinaryIO, dpi: int = 110) -> list[bytes]:
    """Render every PDF page to PNG bytes for Ollama vision input."""
    import fitz

    if not getattr(file, "name", "").lower().endswith(".pdf"):
        return []
    document = fitz.open(stream=_content(file), filetype="pdf")
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    return [page.get_pixmap(matrix=matrix, alpha=False).tobytes("png") for page in document]
