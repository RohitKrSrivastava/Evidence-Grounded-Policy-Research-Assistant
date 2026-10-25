"""Unit and integration tests for data ingestion, chunking, and schemas."""
import pytest
from src.config import STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR
from src.ingestion.parser import PolicyDataParser
from src.ingestion.chunker import PolicyChunker
from src.schema import DocumentChunk, PolicyAnswer

def test_csv_parser():
    macro_path = STRUCTURED_DATA_DIR / "sg_digital_economy_macro.csv"
    assert macro_path.exists()
    records = PolicyDataParser.parse_csv_file(macro_path)
    assert len(records) > 0
    assert "metric" in records[0]
    assert "value" in records[0]

def test_markdown_parser():
    report_path = UNSTRUCTURED_DATA_DIR / "sg_digital_economy_report_2024.md"
    assert report_path.exists()
    doc = PolicyDataParser.parse_markdown_file(report_path)
    assert doc["title"] == "Singapore Digital Economy Report 2024"
    assert len(doc["sections"]) >= 4

def test_chunker_builds_corpus():
    chunker = PolicyChunker()
    chunks = chunker.build_corpus_chunks(STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR)
    assert len(chunks) > 5
    for c in chunks:
        assert isinstance(c, DocumentChunk)
        assert c.chunk_id
        assert c.source_id
        assert len(c.content) > 10
        assert c.token_count > 0
