"""
Database configuration and connection management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base model with common fields"""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import service, agent, validation, learning
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


# Service Data Models
class ServiceModel(Base):
    """Core service information model"""
    __tablename__ = "services"
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    
    # Contact Information
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(500))
    
    # Location Information
    address = Column(String(500))
    suburb = Column(String(100), default="Mount Isa")
    state = Column(String(10), default="QLD")
    postcode = Column(String(10), default="4825")
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Service Details
    operating_hours = Column(JSON)
    services_offered = Column(JSON)  # List of services
    eligibility = Column(Text)
    fees = Column(Text)
    
    # Metadata
    confidence_score = Column(Float, default=0.0)
    last_verified = Column(DateTime)
    source_urls = Column(JSON)  # List of source URLs
    metadata = Column(JSON)  # Additional metadata
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)


class AgentModel(Base):
    """Agent information and status model"""
    __tablename__ = "agents"
    
    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)  # discovery, validation, monitoring
    status = Column(String(20), default="inactive")  # active, inactive, error
    
    # Configuration
    config = Column(JSON)
    capabilities = Column(JSON)  # List of capabilities
    
    # Performance
    tasks_completed = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime)
    
    # Resource Usage
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    
    # Error Tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_time = Column(DateTime)


class ValidationResultModel(Base):
    """Validation result tracking"""
    __tablename__ = "validation_results"
    
    service_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    validation_type = Column(String(50), nullable=False)  # tier1, tier2, tier3
    validator_id = Column(String(100), nullable=False)
    
    # Result
    status = Column(String(20), nullable=False)  # passed, failed, pending, manual_review
    confidence = Column(Float, nullable=False)
    details = Column(JSON)
    
    # Issues and Suggestions
    issues_found = Column(JSON)  # List of issues
    suggestions = Column(JSON)  # List of suggestions
    
    # Timing
    validation_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)  # seconds


class LearningEventModel(Base):
    """Learning event tracking for continuous improvement"""
    __tablename__ = "learning_events"
    
    event_id = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # validation_result, user_feedback, etc.
    source_agent = Column(String(100))
    
    # Event Data
    data = Column(JSON)
    outcome = Column(String(50))
    confidence = Column(Float)
    context = Column(JSON)
    
    # Processing
    processed = Column(Boolean, default=False)
    processing_time = Column(Float)


class TaskQueueModel(Base):
    """Task queue for agent coordination"""
    __tablename__ = "task_queue"
    
    task_id = Column(String(100), unique=True, nullable=False)
    task_type = Column(String(50), nullable=False)  # discovery, validation, monitoring
    priority = Column(Float, default=0.5)
    
    # Task Data
    payload = Column(JSON)
    assigned_agent = Column(String(100))
    
    # Status
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timing
    scheduled_for = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    result = Column(JSON)
    error_message = Column(Text)


class CrossReferenceModel(Base):
    """Cross-reference data from external sources"""
    __tablename__ = "cross_references"
    
    service_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    source_url = Column(String(500), nullable=False)
    
    # Reference Data
    reference_data = Column(JSON)
    match_score = Column(Float)
    confidence = Column(Float)
    
    # Status
    is_verified = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.utcnow)