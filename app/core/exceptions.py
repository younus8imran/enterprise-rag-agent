from fastapi import HTTPException, status
from typing import Any, Optional

class AppBaseException(Exception):
    """Base exception for the application"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class DatabaseException(AppBaseException):
    """Raised when a database operation fails"""
    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)

class ConfigurationException(AppBaseException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str = "Configuration error", details: Optional[Any] = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)
