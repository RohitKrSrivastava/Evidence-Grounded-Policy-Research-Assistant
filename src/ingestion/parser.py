"""Document and dataset parsers for structured and unstructured policy sources."""
import csv
from pathlib import Path
from typing import List, Dict, Any

class PolicyDataParser:
    """Parses mixed-format files (CSV tables and Markdown whitepapers)."""

    @staticmethod
    def parse_csv_file(file_path: Path) -> List[Dict[str, Any]]:
        """Parses a CSV file into structured dictionary rows with cleaned values."""
        records = []
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                cleaned_row = {k.strip(): (v.strip() if v else "") for k, v in row.items()}
                cleaned_row["_row_idx"] = idx
                cleaned_row["_source_file"] = file_path.name
                records.append(cleaned_row)
        return records

    @staticmethod
    def parse_markdown_file(file_path: Path) -> Dict[str, Any]:
        """Parses a markdown policy report into metadata header and section blocks."""
        with open(file_path, mode="r", encoding="utf-8") as f:
            text = f.read()

        lines = text.splitlines()
        doc_title = file_path.stem.replace("_", " ").title()
        metadata: Dict[str, str] = {}
        sections: List[Dict[str, str]] = []
        current_section = "Header"
        current_content: List[str] = []

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("# ") and not metadata.get("title"):
                doc_title = line_stripped.lstrip("# ").strip()
                metadata["title"] = doc_title
                continue

            if line_stripped.startswith("**") and ":" in line_stripped:
                # Metadata line (e.g. **Author:** ...)
                parts = line_stripped.split(":", 1)
                k = parts[0].replace("*", "").strip()
                v = parts[1].replace("*", "").strip()
                metadata[k.lower()] = v
                continue

            if line_stripped.startswith("## "):
                if current_content:
                    sections.append({
                        "section": current_section,
                        "content": "\n".join(current_content).strip()
                    })
                    current_content = []
                current_section = line_stripped.lstrip("# ").strip()
                continue

            current_content.append(line)

        if current_content:
            sections.append({
                "section": current_section,
                "content": "\n".join(current_content).strip()
            })

        return {
            "file_name": file_path.name,
            "title": metadata.get("title", doc_title),
            "metadata": metadata,
            "sections": sections
        }
