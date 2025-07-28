"""
Logging configuration for the scraping system
"""

import logging
import logging.handlers
import sys
from pathlib import Path
import structlog
from datetime import datetime

from app.core.config import settings


def setup_logging():
    """Setup structured logging for the application"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class AgentLogger:
    """Specialized logger for agents with context"""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = get_logger(f"agent.{agent_type}.{agent_id}")
        
    def info(self, message: str, **kwargs):
        """Log info message with agent context"""
        self.logger.info(
            message,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def warning(self, message: str, **kwargs):
        """Log warning message with agent context"""
        self.logger.warning(
            message,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with agent context"""
        self.logger.error(
            message,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.utcnow().isoformat(),
            error=str(error) if error else None,
            error_type=type(error).__name__ if error else None,
            **kwargs
        )
    
    def debug(self, message: str, **kwargs):
        """Log debug message with agent context"""
        self.logger.debug(
            message,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )