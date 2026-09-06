"""Plain text and Markdown file parser."""

from pathlib import Path

from app.services.rag.parsers.base import BaseParser, ParsedDocument, ParsedPage


class TextParser(BaseParser):
    """Parser for .txt and .md files."""

    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a plain-text or markdown file.

        Args:
            file_path: Path to the text file.

        Returns:
            ParsedDocument with the file content as a single page.
        """
        self._validate_file(file_path)

        text = file_path.read_text(encoding="utf-8")

        return ParsedDocument(
            name=file_path.name,
            doc_type=file_path.suffix.lstrip("."),
            pages=[ParsedPage(text=text, page_number=1)],
            metadata={"source": str(file_path), "char_count": len(text)},
        )
