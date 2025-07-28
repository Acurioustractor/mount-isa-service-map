"""
Agent data models and schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class AgentType(str, Enum):
    """Agent type enumeration"""
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    MONITORING = "monitoring"
    LEARNING = "learning"


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentBase(BaseModel):
    """Base agent model"""
    agent_id: str = Field(..., min_length=1, max_length=100)
    agent_type: AgentType
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    capabilities: Optional[List[str]] = Field(default_factory=list)


class AgentCreate(AgentBase):
    """Model for creating a new agent"""
    pass


class AgentUpdate(BaseModel):
    """Model for updating an existing agent"""
    status: Optional[AgentStatus] = None
    config: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_usage: Optional[float] = Field(None, ge=0, le=100)


class Agent(AgentBase):
    """Full agent model with all fields"""
    id: UUID
    status: AgentStatus = Field(default=AgentStatus.INACTIVE)
    
    # Performance Metrics
    tasks_completed: int = Field(default=0)
    success_rate: float = Field(default=0.0, ge=0, le=1)
    last_heartbeat: Optional[datetime] = None
    
    # Resource Usage
    cpu_usage: float = Field(default=0.0, ge=0, le=100)
    memory_usage: float = Field(default=0.0, ge=0, le=100)
    
    # Error Tracking
    error_count: int = Field(default=0)
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentHeartbeat(BaseModel):
    """Agent heartbeat model"""
    agent_id: str
    status: AgentStatus
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    tasks_in_progress: int = Field(ge=0)
    last_task_completed: Optional[datetime] = None


class AgentTask(BaseModel):
    """Agent task model"""
    task_id: str
    task_type: str
    priority: float = Field(default=0.5, ge=0, le=1)
    payload: Dict[str, Any]
    max_attempts: int = Field(default=3, ge=1, le=10)
    scheduled_for: Optional[datetime] = None


class AgentTaskResult(BaseModel):
    """Agent task result model"""
    task_id: str
    agent_id: str
    status: str  # completed, failed, partial
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None  # seconds
    completed_at: datetime


class AgentPerformanceMetrics(BaseModel):
    """Agent performance metrics"""
    agent_id: str
    agent_type: AgentType
    
    # Task Metrics
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    
    # Performance Metrics
    avg_processing_time: float  # seconds
    avg_cpu_usage: float
    avg_memory_usage: float
    
    # Time Period
    period_start: datetime
    period_end: datetime


class AgentConfiguration(BaseModel):
    """Agent configuration model"""
    agent_type: AgentType
    max_concurrent_tasks: int = Field(default=1, ge=1, le=10)
    request_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    timeout: int = Field(default=30, ge=5, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    
    # Type-specific configuration
    discovery_config: Optional[Dict[str, Any]] = None
    validation_config: Optional[Dict[str, Any]] = None
    monitoring_config: Optional[Dict[str, Any]] = None
    
    # Resource limits
    max_memory_mb: int = Field(default=512, ge=64, le=4096)
    max_cpu_percent: float = Field(default=50.0, ge=1.0, le=100.0)