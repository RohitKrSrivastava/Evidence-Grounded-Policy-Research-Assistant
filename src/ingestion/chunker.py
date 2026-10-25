"""Chunking and provenance indexing for structured and unstructured policy records."""
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from src.schema import DocumentChunk
from src.ingestion.parser import PolicyDataParser
from src.config import CONFIG

class PolicyChunker:
    """Creates deterministic, traceable chunks from structured and unstructured sources."""

    def __init__(self, chunk_size_words: int = None, chunk_overlap_words: int = None):
        self.chunk_size = chunk_size_words or CONFIG.retrieval.chunk_size_words
        self.chunk_overlap = chunk_overlap_words or CONFIG.retrieval.chunk_overlap_words

    @staticmethod
    def _generate_chunk_id(source_id: str, section: str, index: int) -> str:
        unique_str = f"{source_id}:{section}:{index}"
        hash_suffix = hashlib.md5(unique_str.encode("utf-8")).hexdigest()[:8]
        clean_section = "".join(c if c.isalnum() else "_" for c in section)[:16]
        return f"{source_id}_{clean_section}_{index}_{hash_suffix}"

    def chunk_structured_records(self, csv_path: Path) -> List[DocumentChunk]:
        """Converts tabular CSV rows into semantic chunks while retaining structured metadata."""
        records = PolicyDataParser.parse_csv_file(csv_path)
        chunks = []
        source_id = csv_path.stem

        # Aggregate related rows (e.g., by metric or sector or year)
        # to ensure the chunk has sufficient context for comparison
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            key = r.get("metric") or r.get("role_category") or r.get("sector") or "general"
            grouped.setdefault(key, []).append(r)

        chunk_idx = 0
        for group_key, rows in grouped.items():
            lines = [f"Dataset: {csv_path.name} | Category: {group_key}"]
            for row in rows:
                formatted_cols = ", ".join(f"{k}: {v}" for k, v in row.items() if not k.startswith("_"))
                lines.append(f"- {formatted_cols}")

            content = "\n".join(lines)
            tokens = len(content.split())
            chunk_id = self._generate_chunk_id(source_id, group_key, chunk_idx)

            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                source_id=csv_path.name,
                doc_title=f"Structured Table: {csv_path.stem.replace('_', ' ').title()}",
                doc_type="structured_csv",
                section=group_key,
                content=content,
                metadata={
                    "filename": csv_path.name,
                    "category": group_key,
                    "row_count": len(rows),
                    "raw_rows": rows
                },
                token_count=tokens
            ))
            chunk_idx += 1

        return chunks

    def chunk_markdown_report(self, md_path: Path) -> List[DocumentChunk]:
        """Chunks unstructured markdown whitepaper into section-aware chunks."""
        doc = PolicyDataParser.parse_markdown_file(md_path)
        chunks = []
        doc_id = doc["metadata"].get("doc id", md_path.stem)
        doc_title = doc["title"]

        chunk_idx = 0
        for sec in doc["sections"]:
            sec_name = sec["section"]
            sec_content = sec["content"]
            if not sec_content:
                continue

            words = sec_content.split()
            if len(words) <= self.chunk_size:
                chunks.append(DocumentChunk(
                    chunk_id=self._generate_chunk_id(doc_id, sec_name, chunk_idx),
                    source_id=doc_id,
                    doc_title=doc_title,
                    doc_type="policy_report",
                    section=sec_name,
                    content=sec_content,
                    metadata={
                        "filename": md_path.name,
                        "metadata": doc["metadata"],
                        "section": sec_name
                    },
                    token_count=len(words)
                ))
                chunk_idx += 1
            else:
                # Sliding window chunking respecting word boundary
                step = self.chunk_size - self.chunk_overlap
                for start_idx in range(0, len(words), step):
                    window_words = words[start_idx : start_idx + self.chunk_size]
                    if not window_words:
                        break
                    chunk_text = " ".join(window_words)
                    chunks.append(DocumentChunk(
                        chunk_id=self._generate_chunk_id(doc_id, sec_name, chunk_idx),
                        source_id=doc_id,
                        doc_title=doc_title,
                        doc_type="policy_report",
                        section=sec_name,
                        content=chunk_text,
                        metadata={
                            "filename": md_path.name,
                            "metadata": doc["metadata"],
                            "section": sec_name,
                            "sub_chunk_index": chunk_idx
                        },
                        token_count=len(window_words)
                    ))
                    chunk_idx += 1
                    if start_idx + self.chunk_size >= len(words):
                        break

        return chunks

    def build_corpus_chunks(self, structured_dir: Path, unstructured_dir: Path) -> List[DocumentChunk]:
        """Ingests and chunks all files across both source directories."""
        all_chunks: List[DocumentChunk] = []

        # Process CSVs
        for csv_file in sorted(structured_dir.glob("*.csv")):
            chunks = self.chunk_structured_records(csv_file)
            all_chunks.extend(chunks)

        # Process Markdown files
        for md_file in sorted(unstructured_dir.glob("*.md")):
            chunks = self.chunk_markdown_report(md_file)
            all_chunks.extend(chunks)

        return all_chunks
