"""Tests for document parsers."""

from pathlib import Path

import pytest

from app.services.rag.parsers import get_parser
from app.services.rag.parsers.docx_parser import DocxParser
from app.services.rag.parsers.pdf_parser import PDFParser
from app.services.rag.parsers.text_parser import TextParser


def test_registry_returns_text_parser_for_txt(tmp_path: Path):
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello world")
    parser = get_parser(file_path)
    assert isinstance(parser, TextParser)


def test_registry_returns_text_parser_for_markdown(tmp_path: Path):
    file_path = tmp_path / "doc.md"
    file_path.write_text("# heading\n\nbody")
    parser = get_parser(file_path)
    assert isinstance(parser, TextParser)


def test_registry_returns_pdf_parser(tmp_path: Path):
    file_path = tmp_path / "doc.pdf"
    file_path.write_bytes(b"%PDF-fake")
    parser = get_parser(file_path)
    assert isinstance(parser, PDFParser)


def test_registry_returns_docx_parser(tmp_path: Path):
    file_path = tmp_path / "doc.docx"
    file_path.write_bytes(b"PK\x03\x04-fake")
    parser = get_parser(file_path)
    assert isinstance(parser, DocxParser)


def test_registry_raises_for_unknown_extension(tmp_path: Path):
    file_path = tmp_path / "doc.xyz"
    file_path.write_text("nope")
    with pytest.raises(ValueError, match="Unsupported file type"):
        get_parser(file_path)


@pytest.mark.asyncio
async def test_text_parser_reads_file(tmp_path: Path):
    file_path = tmp_path / "doc.txt"
    file_path.write_text("First paragraph.\n\nSecond paragraph.")
    parser = TextParser()
    result = await parser.parse(file_path)
    assert "First paragraph" in result.full_text
    assert "Second paragraph" in result.full_text
    assert result.total_pages == 1


@pytest.mark.asyncio
async def test_parser_raises_for_missing_file(tmp_path: Path):
    file_path = tmp_path / "missing.txt"
    parser = TextParser()
    with pytest.raises(FileNotFoundError):
        await parser.parse(file_path)
