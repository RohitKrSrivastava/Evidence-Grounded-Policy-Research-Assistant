"""Privacy preservation, data minimisation, and PII redaction for policy data."""
import re
from typing import Tuple, Dict
from src.config import CONFIG

class PrivacyGuard:
    """Detects and redacts Personally Identifiable Information (PII) and classified markers."""

    # Singapore NRIC / FIN pattern: S1234567A, T1234567B, F1234567C, G1234567D, M1234567E
    NRIC_PATTERN = r"\b[STFGM]\d{7}[A-Z]\b"
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    PHONE_PATTERN = r"(?:\+65\s?)?[689]\d{3}[-\s]?\d{4}\b"
    SECRET_KEY_PATTERN = r"\b(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|api_key=[a-zA-Z0-9_-]+)\b"

    def __init__(self, redaction_token: str = None):
        self.redaction_token = redaction_token or CONFIG.security.pii_redaction_token
        self.nric_re = re.compile(self.NRIC_PATTERN, re.IGNORECASE)
        self.email_re = re.compile(self.EMAIL_PATTERN, re.IGNORECASE)
        self.phone_re = re.compile(self.PHONE_PATTERN)
        self.key_re = re.compile(self.SECRET_KEY_PATTERN, re.IGNORECASE)

    def scan_and_redact(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Redacts sensitive PII and secrets, returning sanitized text and counts."""
        redacted = text
        stats = {
            "nric_detected": 0,
            "emails_detected": 0,
            "phones_detected": 0,
            "secrets_detected": 0
        }

        # NRIC
        nrics = self.nric_re.findall(redacted)
        if nrics:
            stats["nric_detected"] = len(nrics)
            redacted = self.nric_re.sub(f"{self.redaction_token}_NRIC", redacted)

        # Emails
        emails = self.email_re.findall(redacted)
        if emails:
            stats["emails_detected"] = len(emails)
            redacted = self.email_re.sub(f"{self.redaction_token}_EMAIL", redacted)

        # Phones
        phones = self.phone_re.findall(redacted)
        if phones:
            stats["phones_detected"] = len(phones)
            redacted = self.phone_re.sub(f"{self.redaction_token}_PHONE", redacted)

        # API Keys / Tokens
        keys = self.key_re.findall(redacted)
        if keys:
            stats["secrets_detected"] = len(keys)
            redacted = self.key_re.sub(f"{self.redaction_token}_SECRET_KEY", redacted)

        return redacted, stats

    def contains_pii(self, text: str) -> bool:
        """Quick boolean check if text contains any PII."""
        _, stats = self.scan_and_redact(text)
        return any(v > 0 for v in stats.values())
