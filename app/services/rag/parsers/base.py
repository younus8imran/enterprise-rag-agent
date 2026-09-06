"""Base parser interface and shared data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ParsedPage:
    """A single page or section extracted from a document."""

    text: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Result of parsing a document file."""

    name: str
    doc_type: str
    pages: List[ParsedPage]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        """Return the concatenated text of all pages."""
        return "\n\n".join(p.text for p in self.pages if p.text.strip())

    @property
    def total_pages(self) -> int:
        return len(self.pages)


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a file and return structured text content.

        Args:
            file_path: Path to the document file.

        Returns:
            ParsedDocument with extracted text and metadata.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or corrupt.
        """
        ...

    def _validate_file(self, file_path: Path) -> None:
        """Validate that the file exists and is readable."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")
