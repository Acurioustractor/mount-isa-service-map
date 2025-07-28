"""
Data models for the scraping system
"""

from app.models.service import Service, ServiceCreate, ServiceUpdate
from app.models.agent import Agent, AgentCreate, AgentUpdate
from app.models.validation import ValidationResult, ValidationRequest

__all__ = [
    "Service",
    "ServiceCreate", 
    "ServiceUpdate",
    "Agent",
    "AgentCreate",
    "AgentUpdate", 
    "ValidationResult",
    "ValidationRequest"
]