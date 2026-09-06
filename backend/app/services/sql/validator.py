from typing import List, Optional, Dict, Any
import re
from pydantic import BaseModel, Field
from app.core.logging import logger

class SQLValidationError(Exception):
    """Raised when SQL fails validation"""
    pass

class SQLValidator:
    """
    Validates SQL queries to ensure they are safe for execution.
    Rejects any write operations and enforces read-only constraints.
    """

    # Dangerous SQL keywords that modify data or schema
    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "TRUNCATE", "CREATE", "GRANT", "REVOKE",
        "EXEC", "EXECUTE", "CALL", "REPLACE",
        # Postgres-specific dangerous commands
        "COPY", "VACUUM", "CLUSTER", "REINDEX",
        "COMMENT", "PREPARE", "DEALLOCATE"
    ]

    # Dangerous characters and patterns
    SUSPICIOUS_PATTERNS = [
        r";\s*(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE)",  # Stacked queries
        r"--\s*\n",  # Comment injection attempts
        r"/\*.*\*/",  # Block comments (can hide malicious SQL)
        r"\bxp_cmdshell\b",  # SQL Server command execution
        r"\binto\s+outfile\b",  # MySQL file write
        r"\bload_file\b",  # MySQL file read
        r"\bpg_read_file\b",  # Postgres file read
    ]

    @classmethod
    def validate(cls, sql: str) -> None:
        """
        Validates a SQL query for safety.

        Args:
            sql: The SQL query to validate

        Raises:
            SQLValidationError: If the query fails validation
        """
        if not sql or not sql.strip():
            raise SQLValidationError("Empty SQL query")

        sql_upper = sql.upper()

        # Check for forbidden keywords
        for keyword in cls.FORBIDDEN_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                raise SQLValidationError(
                    f"Forbidden operation detected: {keyword}. "
                    f"Only SELECT queries are allowed."
                )

        # Check for suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE | re.DOTALL):
                raise SQLValidationError(
                    f"Suspicious pattern detected. Query rejected for security."
                )

        # Ensure it's a SELECT statement
        if not sql_upper.strip().startswith("SELECT") and not sql_upper.strip().startswith("WITH"):
            raise SQLValidationError(
                "Only SELECT statements (and CTEs starting with WITH) are allowed."
            )

        logger.info("sql_validation_passed", sql_length=len(sql))

    @classmethod
    def sanitize_limit(cls, sql: str, max_rows: int = 1000) -> str:
        """
        Ensures a LIMIT clause exists to prevent unbounded result sets.

        Args:
            sql: The SQL query
            max_rows: Maximum number of rows to return

        Returns:
            The SQL with a LIMIT clause
        """
        sql_upper = sql.upper()

        # Check if LIMIT already exists
        if "LIMIT" in sql_upper:
            # Extract the existing limit
            match = re.search(r'\bLIMIT\s+(\d+)', sql, re.IGNORECASE)
            if match:
                existing_limit = int(match.group(1))
                if existing_limit > max_rows:
                    # Replace with max_rows
                    sql = re.sub(
                        r'\bLIMIT\s+\d+',
                        f'LIMIT {max_rows}',
                        sql,
                        flags=re.IGNORECASE
                    )
            return sql

        # Add LIMIT if not present
        return f"{sql.rstrip(';')} LIMIT {max_rows}"
