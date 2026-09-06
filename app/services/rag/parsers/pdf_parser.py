"""PDF file parser using pypdf."""

from pathlib import Path

from app.services.rag.parsers.base import BaseParser, ParsedDocument, ParsedPage


class PDFParser(BaseParser):
    """Parser for .pdf files using pypdf."""

    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a PDF file, extracting text per page.

        Args:
            file_path: Path to the PDF file.

        Returns:
            ParsedDocument with one ParsedPage per PDF page.
        """
        self._validate_file(file_path)

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError(
                "pypdf is required for PDF parsing. Install with: uv pip install pypdf"
            ) from exc

        reader = PdfReader(str(file_path))
        pages: list[ParsedPage] = []

        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(ParsedPage(text=text, page_number=i))

        return ParsedDocument(
            name=file_path.name,
            doc_type="pdf",
            pages=pages,
            metadata={
                "source": str(file_path),
                "total_pages": len(reader.pages),
                "pdf_info": reader.metadata.get("/Title", "") if reader.metadata else "",
            },
        )
