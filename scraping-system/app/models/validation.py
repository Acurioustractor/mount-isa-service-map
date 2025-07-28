"""
Validation models and schemas
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationStatus(str, Enum):
    """Validation status values"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    INFO = "info"


class ValidationResult(BaseModel):
    """Result of a single validation check"""
    field: str = Field(..., description="Field being validated")
    check_type: str = Field(..., description="Type of validation check")
    status: ValidationStatus = Field(..., description="Validation status")
    level: ValidationLevel = Field(..., description="Severity level")
    message: str = Field(..., description="Validation message")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in validation result")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    raw_value: Optional[Any] = Field(None, description="Original value being validated")
    validated_value: Optional[Any] = Field(None, description="Corrected/validated value")


class ValidationSummary(BaseModel):
    """Summary of validation results"""
    service_id: str = Field(..., description="Service ID")
    total_checks: int = Field(..., ge=0, description="Total number of validation checks")
    passed: int = Field(..., ge=0, description="Number of checks that passed")
    failed: int = Field(..., ge=0, description="Number of checks that failed")
    warnings: int = Field(..., ge=0, description="Number of warnings")
    overall_score: float = Field(..., ge=0, le=1, description="Overall validation score")
    critical_issues: List[ValidationResult] = Field(default_factory=list, description="Critical validation issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    validated_data: Dict[str, Any] = Field(default_factory=dict, description="Validated/corrected service data")


class ValidationOptions(BaseModel):
    """Options for validation process"""
    include_warnings: bool = Field(True, description="Include warning-level validations")
    strict_mode: bool = Field(False, description="Use strict validation rules")
    validate_urls: bool = Field(True, description="Check URL accessibility")
    validate_phones: bool = Field(True, description="Validate phone number formats")
    validate_emails: bool = Field(True, description="Validate email addresses")
    validate_addresses: bool = Field(True, description="Validate address formats")
    business_rules: bool = Field(True, description="Apply business rule validations")
    content_quality: bool = Field(True, description="Check content quality")
    data_consistency: bool = Field(True, description="Check data consistency")


class ValidationRequest(BaseModel):
    """Request for service validation"""
    service_data: Dict[str, Any] = Field(..., description="Service data to validate")
    options: Optional[ValidationOptions] = Field(None, description="Validation options")


class ValidationResponse(BaseModel):
    """Response from validation request"""
    task_id: str = Field(..., description="Validation task ID")
    status: str = Field(..., description="Validation status")
    message: str = Field(..., description="Status message")
    summary: Optional[ValidationSummary] = Field(None, description="Validation summary (if completed)")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Request creation time")


class ValidationBatchRequest(BaseModel):
    """Request for batch validation"""
    services: List[Dict[str, Any]] = Field(..., description="List of services to validate")
    options: Optional[ValidationOptions] = Field(None, description="Validation options")


class ValidationBatchResponse(BaseModel):
    """Response from batch validation request"""
    batch_id: str = Field(..., description="Batch validation ID")
    task_ids: List[str] = Field(..., description="Individual task IDs")
    status: str = Field(..., description="Batch status")
    total_services: int = Field(..., description="Total number of services in batch")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation time")


class ValidationRule(BaseModel):
    """Definition of a validation rule"""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    field: str = Field(..., description="Field this rule applies to")
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    level: ValidationLevel = Field(..., description="Validation level")
    enabled: bool = Field(True, description="Whether rule is enabled")
    custom_message: Optional[str] = Field(None, description="Custom validation message")


class ValidationMetrics(BaseModel):
    """Validation system performance metrics"""
    total_validations: int = Field(..., description="Total number of validations performed")
    successful_validations: int = Field(..., description="Number of successful validations")
    failed_validations: int = Field(..., description="Number of failed validations")
    average_processing_time: float = Field(..., description="Average processing time")
    critical_failures: int = Field(..., description="Number of critical validation failures")
    validation_accuracy: float = Field(..., description="Validation accuracy percentage")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class ValidationPattern(BaseModel):
    """Validation pattern definition"""
    pattern_id: str = Field(..., description="Pattern identifier")
    name: str = Field(..., description="Pattern name")
    regex: str = Field(..., description="Regular expression pattern")
    description: str = Field(..., description="Pattern description")
    examples: List[str] = Field(default_factory=list, description="Example values")
    confidence: float = Field(..., ge=0, le=1, description="Pattern confidence")


class ContactValidationRequest(BaseModel):
    """Request for contact information validation"""
    phone: Optional[str] = Field(None, description="Phone number to validate")
    email: Optional[str] = Field(None, description="Email address to validate")
    website: Optional[str] = Field(None, description="Website URL to validate")


class LocationValidationRequest(BaseModel):
    """Request for location validation"""
    address: Optional[str] = Field(None, description="Street address")
    suburb: Optional[str] = Field(None, description="Suburb/city")
    postcode: Optional[str] = Field(None, description="Postal code")
    state: Optional[str] = Field(None, description="State/territory")


class ContentValidationRequest(BaseModel):
    """Request for content quality validation"""
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    category: Optional[str] = Field(None, description="Service category")


class ValidationReport(BaseModel):
    """Comprehensive validation report"""
    report_id: str = Field(..., description="Report identifier")
    service_id: str = Field(..., description="Service ID")
    validation_date: datetime = Field(default_factory=datetime.utcnow, description="Validation date")
    validator_agent_id: str = Field(..., description="ID of validating agent")
    summary: ValidationSummary = Field(..., description="Validation summary")
    detailed_results: List[ValidationResult] = Field(..., description="Detailed validation results")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    follow_up_required: bool = Field(False, description="Whether manual follow-up is required")
    estimated_accuracy: float = Field(..., ge=0, le=1, description="Estimated accuracy of validation")


class ValidationHistory(BaseModel):
    """Historical validation record"""
    validation_id: str = Field(..., description="Validation record ID")
    service_id: str = Field(..., description="Service ID")
    validation_date: datetime = Field(..., description="When validation was performed")
    overall_score: float = Field(..., ge=0, le=1, description="Overall validation score")
    critical_issues_count: int = Field(..., ge=0, description="Number of critical issues")
    status: str = Field(..., description="Validation outcome")
    agent_id: str = Field(..., description="Validating agent ID")


class ValidationQueue(BaseModel):
    """Validation queue item"""
    queue_id: str = Field(..., description="Queue item ID")
    service_data: Dict[str, Any] = Field(..., description="Service data to validate")
    priority: int = Field(default=5, ge=1, le=10, description="Validation priority (1=highest)")
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Submission time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    requester: Optional[str] = Field(None, description="Who requested the validation")


class ValidationAgentStatus(BaseModel):
    """Status of validation agent"""
    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Agent status")
    current_task: Optional[str] = Field(None, description="Current task being processed")
    tasks_completed: int = Field(default=0, description="Number of tasks completed")
    tasks_failed: int = Field(default=0, description="Number of tasks failed")
    average_processing_time: float = Field(default=0.0, description="Average processing time")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat time")
    performance_score: float = Field(default=1.0, ge=0, le=1, description="Performance score")