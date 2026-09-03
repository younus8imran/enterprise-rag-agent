import re
from typing import Any, Optional
from fastapi import HTTPException
from app.core.logging import logger

class SecurityValidator:
    """
    Provides defenses against prompt injection and input/output validation.
    Treats all LLM and Tool outputs as untrusted data.
    """

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"reveal the system prompt",
        r"you are now a",
        r"act as a",
        r"forget all prior",
        r"system prompt",
        r"developer mode",
        r"dan mode",
    ]

    @classmethod
    def validate_input(cls, text: str) -> str:
        """
        Checks for prompt injection attempts in user input.
        """
        if not text:
            return text

        text_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning("prompt_injection_detected", input=text)
                # In production, we might raise an exception or sanitize.
                # For the agent, we flag it as untrusted/malicious.
                raise HTTPException(status_code=400, detail="Malicious input detected")

        return text

    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """
        Sanitizes tool or LLM output to prevent XSS or injection into downstream components.
        """
        if not text:
            return ""

        # Basic sanitization (escaping HTML tags)
        return text.replace("<", "&lt;").replace(">", "&gt;")

    @classmethod
    def validate_sql(cls, sql: str) -> bool:
        """
        Additional safety check for generated SQL.
        """
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "GRANT", "REVOKE", "ALTER"]
        for word in forbidden:
            if word in sql.upper():
                return False
        return True
