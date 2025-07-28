"""
Discovery models and schemas
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class DiscoveryStatus(str, Enum):
    """Discovery task status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExtractionMethod(str, Enum):
    """Service extraction methods"""
    SECTION_BASED = "section_based"
    PAGE_BASED = "page_based"
    PATTERN_BASED = "pattern_based"
    ML_BASED = "ml_based"


class DiscoveryOptions(BaseModel):
    """Options for discovery process"""
    follow_links: bool = Field(True, description="Follow links to discover more services")
    extract_contact: bool = Field(True, description="Extract contact information")
    extract_location: bool = Field(True, description="Extract location information")
    extract_hours: bool = Field(True, description="Extract operating hours")
    extract_services: bool = Field(True, description="Extract services offered")
    min_confidence: float = Field(0.4, ge=0, le=1, description="Minimum confidence for extraction")
    validate_urls: bool = Field(True, description="Validate extracted URLs")
    respect_robots_txt: bool = Field(True, description="Respect robots.txt")
    max_processing_time: int = Field(300, description="Maximum processing time per URL (seconds)")


class DiscoveryRequest(BaseModel):
    """Request for service discovery"""
    url: HttpUrl = Field(..., description="URL to discover services from")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum crawl depth")
    options: Optional[DiscoveryOptions] = Field(None, description="Discovery options")


class DiscoveredService(BaseModel):
    """A service discovered during crawling"""
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    source_url: str = Field(..., description="URL where service was discovered")
    extraction_method: ExtractionMethod = Field(..., description="How the service was extracted")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in extraction")
    
    # Contact information
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Location information
    address: Optional[str] = Field(None, description="Street address")
    suburb: Optional[str] = Field(None, description="Suburb/city")
    postcode: Optional[str] = Field(None, description="Postal code")
    state: Optional[str] = Field(None, description="State/territory")
    
    # Service details
    category: Optional[str] = Field(None, description="Service category")
    operating_hours: Optional[str] = Field(None, description="Operating hours")
    services_offered: Optional[List[str]] = Field(None, description="List of services offered")
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow, description="Discovery timestamp")
    needs_validation: bool = Field(True, description="Whether service needs validation")


class DiscoveryResult(BaseModel):
    """Result of discovery operation"""
    url: str = Field(..., description="URL that was processed")
    status: DiscoveryStatus = Field(..., description="Discovery status")
    services_found: int = Field(..., ge=0, description="Number of services found")
    services: List[DiscoveredService] = Field(default_factory=list, description="Discovered services")
    additional_urls: List[str] = Field(default_factory=list, description="Additional URLs found for crawling")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    page_relevance: Optional[float] = Field(None, ge=0, le=1, description="Page relevance score")
    depth: int = Field(0, description="Crawl depth of this URL")


class DiscoveryResponse(BaseModel):
    """Response from discovery request"""
    task_id: str = Field(..., description="Discovery task ID")
    status: DiscoveryStatus = Field(..., description="Discovery status")
    message: str = Field(..., description="Status message")
    url: Optional[str] = Field(None, description="URL being processed")
    services_found: Optional[int] = Field(None, description="Number of services found (if completed)")
    services: Optional[List[DiscoveredService]] = Field(None, description="Discovered services (if completed)")
    additional_urls: Optional[List[str]] = Field(None, description="Additional URLs found")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Request creation time")


class DiscoveryBatchRequest(BaseModel):
    """Request for batch discovery"""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=50, description="URLs to discover services from")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum crawl depth")
    options: Optional[DiscoveryOptions] = Field(None, description="Discovery options")


class DiscoveryBatchResponse(BaseModel):
    """Response from batch discovery request"""
    batch_id: str = Field(..., description="Batch discovery ID")
    task_ids: List[str] = Field(..., description="Individual task IDs")
    status: str = Field(..., description="Batch status")
    total_urls: int = Field(..., description="Total number of URLs in batch")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation time")


class DiscoveryTask(BaseModel):
    """Discovery task definition"""
    task_id: str = Field(..., description="Task identifier")
    url: str = Field(..., description="URL to process")
    depth: int = Field(0, description="Current crawl depth")
    max_depth: int = Field(2, description="Maximum crawl depth")
    priority: int = Field(5, ge=1, le=10, description="Task priority (1=highest)")
    options: Optional[DiscoveryOptions] = Field(None, description="Discovery options")
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Task submission time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")


class ExtractionPattern(BaseModel):
    """Pattern for extracting specific data types"""
    name: str = Field(..., description="Pattern name")
    pattern: str = Field(..., description="Regular expression pattern")
    confidence: float = Field(..., ge=0, le=1, description="Pattern confidence")
    examples: List[str] = Field(default_factory=list, description="Example values")
    description: Optional[str] = Field(None, description="Pattern description")


class ServicePattern(BaseModel):
    """Pattern library for service extraction"""
    category: str = Field(..., description="Pattern category (contact, location, etc.)")
    subcategory: str = Field(..., description="Pattern subcategory (phone, email, etc.)")
    patterns: List[ExtractionPattern] = Field(..., description="List of patterns")


class DiscoveryMetrics(BaseModel):
    """Discovery system performance metrics"""
    total_pages_processed: int = Field(..., description="Total pages processed")
    total_services_discovered: int = Field(..., description="Total services discovered")
    total_extraction_failures: int = Field(..., description="Total extraction failures")
    success_rate: float = Field(..., ge=0, le=1, description="Success rate percentage")
    avg_services_per_page: float = Field(..., description="Average services discovered per page")
    avg_processing_time: float = Field(..., description="Average processing time per page")
    pattern_match_rates: Dict[str, float] = Field(default_factory=dict, description="Pattern match rates")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class DiscoveryAgent(BaseModel):
    """Discovery agent status"""
    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Agent status")
    current_url: Optional[str] = Field(None, description="Currently processing URL")
    pages_processed: int = Field(default=0, description="Pages processed by this agent")
    services_discovered: int = Field(default=0, description="Services discovered by this agent")
    extraction_failures: int = Field(default=0, description="Extraction failures by this agent")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat time")
    performance_score: float = Field(default=1.0, ge=0, le=1, description="Performance score")


class CrawlResult(BaseModel):
    """Result of a website crawl"""
    crawl_id: str = Field(..., description="Crawl identifier")
    start_url: str = Field(..., description="Starting URL")
    total_pages_crawled: int = Field(..., description="Total pages crawled")
    total_services_found: int = Field(..., description="Total services found")
    crawl_depth_reached: int = Field(..., description="Maximum crawl depth reached")
    crawl_duration: float = Field(..., description="Crawl duration in seconds")
    status: str = Field(..., description="Crawl status")
    discovered_services: List[DiscoveredService] = Field(..., description="All discovered services")
    failed_urls: List[str] = Field(default_factory=list, description="URLs that failed to process")
    started_at: datetime = Field(..., description="Crawl start time")
    completed_at: Optional[datetime] = Field(None, description="Crawl completion time")


class DiscoveryHistory(BaseModel):
    """Historical discovery record"""
    discovery_id: str = Field(..., description="Discovery record ID")
    url: str = Field(..., description="URL that was processed")
    discovery_date: datetime = Field(..., description="When discovery was performed")
    services_found: int = Field(..., description="Number of services found")
    success: bool = Field(..., description="Whether discovery was successful")
    processing_time: float = Field(..., description="Processing time in seconds")
    agent_id: str = Field(..., description="Discovering agent ID")


class DiscoveryQueue(BaseModel):
    """Discovery queue item"""
    queue_id: str = Field(..., description="Queue item ID")
    url: str = Field(..., description="URL to process")
    priority: int = Field(default=5, ge=1, le=10, description="Discovery priority (1=highest)")
    max_depth: int = Field(default=2, description="Maximum crawl depth")
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Submission time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    requester: Optional[str] = Field(None, description="Who requested the discovery")


class LinkCandidate(BaseModel):
    """Candidate link for discovery"""
    url: str = Field(..., description="Link URL")
    anchor_text: str = Field(..., description="Link anchor text")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")
    depth: int = Field(..., description="Depth level")
    parent_url: str = Field(..., description="Parent page URL")


class PageAnalysis(BaseModel):
    """Analysis of a webpage for service discovery"""
    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")
    relevance_score: float = Field(..., ge=0, le=1, description="Service relevance score")
    content_length: int = Field(..., description="Content length in characters")
    has_contact_info: bool = Field(..., description="Whether page has contact information")
    has_service_indicators: bool = Field(..., description="Whether page has service indicators")
    language: Optional[str] = Field(None, description="Detected language")
    service_categories: List[str] = Field(default_factory=list, description="Detected service categories")
    extraction_confidence: float = Field(..., ge=0, le=1, description="Extraction confidence")


class DiscoveryConfiguration(BaseModel):
    """Configuration for discovery system"""
    max_concurrent_agents: int = Field(3, ge=1, le=10, description="Maximum concurrent discovery agents")
    request_delay: float = Field(1.0, ge=0.1, le=10.0, description="Delay between requests (seconds)")
    max_page_size: int = Field(1000000, description="Maximum page size to process (bytes)")
    timeout_per_page: int = Field(30, description="Timeout per page (seconds)")
    user_agent: str = Field("Mount Isa Service Map Discovery Bot", description="User agent string")
    respect_robots_txt: bool = Field(True, description="Respect robots.txt")
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")
    max_redirects: int = Field(5, description="Maximum redirects to follow")
    allowed_domains: Optional[List[str]] = Field(None, description="Allowed domains for crawling")
    blocked_domains: List[str] = Field(default_factory=list, description="Blocked domains")
    file_extensions_to_skip: List[str] = Field(
        default=["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip", "rar"],
        description="File extensions to skip"
    )