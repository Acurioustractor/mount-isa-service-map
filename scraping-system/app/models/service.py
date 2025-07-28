"""
Service data models and schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re


class ServiceBase(BaseModel):
    """Base service model"""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    
    # Contact Information
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    
    # Location Information
    address: Optional[str] = Field(None, max_length=500)
    suburb: str = Field(default="Mount Isa", max_length=100)
    state: str = Field(default="QLD", max_length=10)
    postcode: str = Field(default="4825", max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    # Service Details
    operating_hours: Optional[Dict[str, str]] = None
    services_offered: Optional[List[str]] = None
    eligibility: Optional[str] = Field(None, max_length=2000)
    fees: Optional[str] = Field(None, max_length=1000)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            # Basic Australian phone number validation
            phone_pattern = r'^(\+?61\s?)?(\(0\d\)\s?|\(0\d{1,2}\)\s?|0\d)\s?\d{4}\s?\d{4}$'
            if not re.match(phone_pattern, v.replace(' ', '')):
                raise ValueError('Invalid Australian phone number format')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
            # Basic URL validation
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, v):
                raise ValueError('Invalid website URL format')
        return v
    
    @validator('postcode')
    def validate_postcode(cls, v):
        if v:
            # Australian postcode validation
            if not re.match(r'^\d{4}$', v):
                raise ValueError('Australian postcode must be 4 digits')
        return v


class ServiceCreate(ServiceBase):
    """Model for creating a new service"""
    source_urls: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServiceUpdate(BaseModel):
    """Model for updating an existing service"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    
    # Contact Information
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    
    # Location Information
    address: Optional[str] = Field(None, max_length=500)
    suburb: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=10)
    postcode: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    # Service Details
    operating_hours: Optional[Dict[str, str]] = None
    services_offered: Optional[List[str]] = None
    eligibility: Optional[str] = Field(None, max_length=2000)
    fees: Optional[str] = Field(None, max_length=1000)
    
    # Metadata
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class Service(ServiceBase):
    """Full service model with all fields"""
    id: UUID
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    last_verified: Optional[datetime] = None
    source_urls: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceSummary(BaseModel):
    """Summary model for service listings"""
    id: UUID
    name: str
    category: str
    suburb: str
    confidence_score: float
    is_verified: bool
    last_verified: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ServiceSearchRequest(BaseModel):
    """Search request model"""
    query: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    postcode: Optional[str] = None
    verified_only: bool = False
    min_confidence: float = Field(default=0.0, ge=0, le=1)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ServiceSearchResponse(BaseModel):
    """Search response model"""
    services: List[ServiceSummary]
    total: int
    limit: int
    offset: int
    has_more: bool