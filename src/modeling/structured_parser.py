"""Programmatic parsing and validation for structured policy responses."""
import json
import re
from typing import Dict, Any, Tuple
from src.schema import PolicyAnswer, Citation, AbstentionDetails, AbstentionReason, UncertaintyLevel

class StructuredOutputParser:
    """Validates and enforces strict Pydantic schemas on raw model outputs."""

    @staticmethod
    def parse_and_validate(raw_json_str: str, query: str) -> Tuple[bool, PolicyAnswer, str]:
        """Attempts to parse JSON and validate against the PolicyAnswer model."""
        error_msg = ""
        # Clean markdown code blocks if model wrapped JSON in ```json ... ```
        cleaned = raw_json_str.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback error recovery
            error_msg = f"JSONDecodeError: {str(e)}"
            fallback_answer = PolicyAnswer(
                query=query,
                direct_answer=raw_json_str[:300],
                factual_findings=[],
                model_inferences=[],
                citations=[],
                uncertainty_level=UncertaintyLevel.HIGH,
                uncertainty_rationale="Output failed JSON parsing, returned raw text fallback."
            )
            return False, fallback_answer, error_msg

        try:
            # Ensure query is populated
            if "query" not in data:
                data["query"] = query

            # Ensure citations are formatted
            if "citations" in data and isinstance(data["citations"], list):
                parsed_cits = []
                for cit in data["citations"]:
                    if isinstance(cit, dict):
                        parsed_cits.append(Citation(**cit))
                data["citations"] = parsed_cits

            # Check abstention
            if "abstention" in data and isinstance(data["abstention"], dict):
                data["abstention"] = AbstentionDetails(**data["abstention"])

            answer = PolicyAnswer(**data)
            return True, answer, ""
        except Exception as e:
            error_msg = f"SchemaValidationError: {str(e)}"
            fallback_answer = PolicyAnswer(
                query=query,
                direct_answer=data.get("direct_answer", "Error in structured payload schema validation."),
                factual_findings=data.get("factual_findings", []),
                model_inferences=data.get("model_inferences", []),
                citations=[],
                uncertainty_level=UncertaintyLevel.HIGH,
                uncertainty_rationale=f"Failed validation: {str(e)}"
            )
            return False, fallback_answer, error_msg
