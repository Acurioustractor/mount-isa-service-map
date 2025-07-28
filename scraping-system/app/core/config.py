"""
Configuration settings for the scraping system
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Mount Isa Service Map Scraping System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://scraper_user:scraper_pass@localhost:5432/mount_isa_services"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "mount_isa_services"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://scraper_user:scraper_pass@localhost:5672/"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Scraping
    USER_AGENT: str = "Mount Isa Service Map Bot/1.0 (+https://mountisaservices.com/bot)"
    REQUEST_DELAY: float = 1.0  # Delay between requests (seconds)
    CONCURRENT_REQUESTS: int = 8
    DOWNLOAD_TIMEOUT: int = 30
    RETRY_ATTEMPTS: int = 3
    
    # Agent Configuration
    MAX_DISCOVERY_AGENTS: int = 5
    MAX_VALIDATION_AGENTS: int = 3
    MAX_MONITORING_AGENTS: int = 2
    AGENT_HEARTBEAT_INTERVAL: int = 60  # seconds
    
    # Validation
    MIN_CONFIDENCE_THRESHOLD: float = 0.6
    CROSS_REFERENCE_SOURCES: List[str] = [
        "https://www.health.qld.gov.au",
        "https://www.mountisa.qld.gov.au",
        "https://www.yellowpages.com.au"
    ]
    
    # Geographic
    DEFAULT_LOCATION: str = "Mount Isa, QLD, Australia"
    SEARCH_RADIUS_KM: int = 100
    VALID_POSTCODES: List[str] = ["4825", "4828", "4829", "4830"]
    
    # External APIs
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    OPENCAGE_API_KEY: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    
    # Machine Learning
    MODEL_PATH: str = "./models"
    RETRAIN_THRESHOLD: int = 1000  # New samples before retraining
    MODEL_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/scraping_system.log"
    LOG_MAX_SIZE: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring
    METRICS_PORT: int = 8001
    PROMETHEUS_MULTIPROC_DIR: str = "./prometheus_multiproc_dir"
    
    # File Storage
    TEMP_DIR: str = "./temp"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra environment variables


# Create settings instance
settings = Settings()