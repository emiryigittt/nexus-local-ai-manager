"""Text extraction for files explicitly selected by the user."""

from __future__ import annotations

from pathlib import Path

TEXT_SUFFIXES = {
    ".txt", ".md", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".json",
    ".yaml", ".yml", ".toml", ".html", ".css", ".sql", ".go", ".rs", ".java",
}


def extract_document(path: Path) -> tuple[str, str]:
    suffix = path.suffix.casefold()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace"), suffix.lstrip(".")
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        text = "\n\n".join(
            f"[Sayfa {index}]\n{page.extract_text() or ''}"
            for index, page in enumerate(reader.pages, 1)
        )
        return text, "pdf"
    if suffix == ".docx":
        from docx import Document

        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs), "docx"
    raise ValueError(f"Desteklenmeyen belge türü: {suffix or 'uzantısız dosya'}")
