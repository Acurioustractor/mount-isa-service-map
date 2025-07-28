"""
Custom exceptions for the scraping system
"""

from typing import Optional, Dict, Any


class ScrapingSystemException(Exception):
    """Base exception for scraping system"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "SCRAPING_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AgentException(ScrapingSystemException):
    """Exception related to agent operations"""
    
    def __init__(self, message: str, agent_id: str, agent_type: str, **kwargs):
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            status_code=500,
            details={"agent_id": agent_id, "agent_type": agent_type},
            **kwargs
        )


class ValidationException(ScrapingSystemException):
    """Exception related to validation operations"""
    
    def __init__(self, message: str, validation_type: str, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"validation_type": validation_type},
            **kwargs
        )


class ExtractionException(ScrapingSystemException):
    """Exception related to data extraction"""
    
    def __init__(self, message: str, url: str, **kwargs):
        super().__init__(
            message=message,
            error_code="EXTRACTION_ERROR",
            status_code=500,
            details={"url": url},
            **kwargs
        )


class DatabaseException(ScrapingSystemException):
    """Exception related to database operations"""
    
    def __init__(self, message: str, operation: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation},
            **kwargs
        )


class ConfigurationException(ScrapingSystemException):
    """Exception related to configuration issues"""
    
    def __init__(self, message: str, config_key: str, **kwargs):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={"config_key": config_key},
            **kwargs
        )


class RateLimitException(ScrapingSystemException):
    """Exception when rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details={"retry_after": retry_after},
            **kwargs
        )


class ExternalServiceException(ScrapingSystemException):
    """Exception when external services are unavailable"""
    
    def __init__(self, message: str, service_name: str, **kwargs):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details={"service_name": service_name},
            **kwargs
        )


class ResearchException(ScrapingSystemException):
    """Exception related to research operations"""
    
    def __init__(self, message: str, research_type: str = "general", **kwargs):
        super().__init__(
            message=message,
            error_code="RESEARCH_ERROR",
            status_code=500,
            details={"research_type": research_type},
            **kwargs
        )