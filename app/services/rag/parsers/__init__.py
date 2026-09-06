"""Document parsers for extracting text from various file formats."""

from app.services.rag.parsers.base import BaseParser, ParsedDocument
from app.services.rag.parsers.pdf_parser import PDFParser
from app.services.rag.parsers.text_parser import TextParser
from app.services.rag.parsers.docx_parser import DocxParser
from app.services.rag.parsers.registry import get_parser

__all__ = [
    "BaseParser",
    "ParsedDocument",
    "PDFParser",
    "TextParser",
    "DocxParser",
    "get_parser",
]
