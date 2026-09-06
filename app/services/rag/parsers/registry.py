"""Parser registry — selects the right parser based on file extension."""

from pathlib import Path

from app.services.rag.parsers.base import BaseParser
from app.services.rag.parsers.docx_parser import DocxParser
from app.services.rag.parsers.pdf_parser import PDFParser
from app.services.rag.parsers.text_parser import TextParser

_PARSERS: dict[str, type[BaseParser]] = {
    ".txt": TextParser,
    ".md": TextParser,
    ".pdf": PDFParser,
    ".docx": DocxParser,
}


def get_parser(file_path: Path) -> BaseParser:
    """Return an appropriate parser for the given file.

    Args:
        file_path: Path to the document file.

    Returns:
        A parser instance matching the file extension.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = file_path.suffix.lower()
    parser_cls = _PARSERS.get(ext)
    if parser_cls is None:
        supported = ", ".join(sorted(_PARSERS.keys()))
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported types: {supported}"
        )
    return parser_cls()
