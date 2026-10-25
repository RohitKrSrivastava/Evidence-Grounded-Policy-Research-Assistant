"""Detection and mitigation of direct and indirect prompt injection attacks."""
import re
from typing import Tuple, List

class PromptInjectionGuard:
    """Guards against direct adversarial prompt injection and indirect poisoned retrieved content."""

    # Direct adversarial patterns
    DIRECT_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"system\s*prompt\s*(override|leak|reveal|dump)",
        r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|an\s+unrestricted)",
        r"disregard\s+(all\s+)?guidelines",
        r"bypass\s+(safety|content\s+filter|guardrail)",
        r"repeat\s+the\s+(secret|password|confidential\s+token)",
        r"output\s+the\s+hidden\s+system\s+instructions",
        r"reveal\s+internal\s+instructions",
    ]

    # Indirect injection markers typically injected into untrusted text or corpus docs
    INDIRECT_PATTERNS = [
        r"\[system\s*instruction:",
        r"<system_override>",
        r"ignore\s+the\s+user\s+query\s+and\s+say",
        r"disregard\s+prior\s+instructions\s+and\s+(confirm|state|output)",
        r"exfiltrate\s+user\s+data\s+to",
    ]

    def __init__(self):
        self.direct_regexes = [re.compile(p, re.IGNORECASE) for p in self.DIRECT_PATTERNS]
        self.indirect_regexes = [re.compile(p, re.IGNORECASE) for p in self.INDIRECT_PATTERNS]

    def check_user_query(self, query: str) -> Tuple[bool, List[str]]:
        """Scans user query for adversarial prompt injection attempts."""
        flags = []
        for idx, pattern in enumerate(self.direct_regexes):
            if pattern.search(query):
                flags.append(f"DIRECT_PROMPT_INJECTION_RULE_{idx+1}")

        is_safe = (len(flags) == 0)
        return is_safe, flags

    def check_retrieved_content(self, text: str) -> Tuple[bool, List[str]]:
        """Scans retrieved documents for indirect prompt injection or poisoned commands."""
        flags = []
        for idx, pattern in enumerate(self.indirect_regexes):
            if pattern.search(text):
                flags.append(f"INDIRECT_CONTENT_POISONING_RULE_{idx+1}")

        # Also verify no direct injection payload is hiding inside retrieved document
        for idx, pattern in enumerate(self.direct_regexes):
            if pattern.search(text):
                flags.append(f"EMBEDDED_INJECTION_IN_RETRIEVED_TEXT_{idx+1}")

        is_safe = (len(flags) == 0)
        return is_safe, flags

    def sanitize_untrusted_input(self, text: str) -> str:
        """Neutralizes execution tags and delimiters before passing into prompts."""
        sanitized = text.replace("<script>", "").replace("</script>", "")
        sanitized = sanitized.replace("```system", "```escaped_block")
        sanitized = sanitized.replace("<system>", "&lt;system&gt;")
        return sanitized
