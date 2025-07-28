"""
Validation Agent - Tier 1 automated validation for discovered services
"""

import re
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import phonenumbers
from textblob import TextBlob
import tldextract

from app.agents.base import BaseAgent
from app.models.agent import AgentType, AgentTask
from app.models.service import ServiceCreate
from app.core.exceptions import ValidationException


class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    field: str
    check_type: str
    status: str  # "pass", "fail", "warning"
    level: ValidationLevel
    message: str
    confidence: float
    suggestions: List[str] = None
    raw_value: Any = None
    validated_value: Any = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ValidationSummary:
    """Summary of all validation results for a service"""
    service_id: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    overall_score: float
    critical_issues: List[ValidationResult]
    recommendations: List[str]
    validated_data: Dict[str, Any]


class ValidationAgent(BaseAgent):
    """Tier 1 automated validation agent for service data"""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(agent_id, AgentType.VALIDATION, config, **kwargs)
        
        # Validation patterns
        self.patterns = self._initialize_validation_patterns()
        
        # Australian-specific data
        self.australian_postcodes = self._load_australian_postcodes()
        self.qld_suburbs = self._load_qld_suburbs()
        
        # Validation statistics
        self.validation_stats = {
            'services_validated': 0,
            'total_checks_performed': 0,
            'critical_failures': 0,
            'validation_time_total': 0.0
        }
    
    def _initialize_validation_patterns(self) -> Dict[str, Any]:
        """Initialize validation patterns and rules"""
        return {
            'phone': {
                'australian_landline': r'^(?:\+?61\s?)?(?:\(0[2-9]\)|0[2-9])\s?\d{4}\s?\d{4}$',
                'australian_mobile': r'^(?:\+?61\s?)?4\d{2}\s?\d{3}\s?\d{3}$',
                'international': r'^\+\d{1,3}\s?\d{1,14}$'
            },
            'email': {
                'standard': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'no_disposable': r'^(?!.*@(10minutemail|tempmail|mailinator|guerrillamail))'
            },
            'website': {
                'valid_url': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
                'australian_domain': r'\.au(/.*)?$',
                'secure_only': r'^https://'
            },
            'address': {
                'australian_street': r'\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Boulevard|Blvd|Lane|Ln|Court|Ct|Crescent|Cres|Close|Cl|Terrace|Tce|Highway|Hwy)\b',
                'po_box': r'(?:PO|P\.O\.)\s*Box\s*\d+',
                'unit_number': r'^(?:Unit|Apt|Suite)\s*\d+[a-zA-Z]?[\/\-\s]+'
            },
            'postcode': {
                'qld': r'^4\d{3}$',
                'australian': r'^[1-9]\d{3}$'
            }
        }
    
    def _load_australian_postcodes(self) -> Dict[str, Dict[str, str]]:
        """Load Australian postcode to suburb mappings"""
        # In a real implementation, this would load from a comprehensive database
        # For now, we'll include key Mount Isa region postcodes
        return {
            '4825': {'suburb': 'Mount Isa', 'state': 'QLD', 'region': 'North West Queensland'},
            '4824': {'suburb': 'Mount Isa', 'state': 'QLD', 'region': 'North West Queensland'},
            '4822': {'suburb': 'Cloncurry', 'state': 'QLD', 'region': 'North West Queensland'},
            '4830': {'suburb': 'Townsville', 'state': 'QLD', 'region': 'North Queensland'},
            '4000': {'suburb': 'Brisbane', 'state': 'QLD', 'region': 'South East Queensland'}
        }
    
    def _load_qld_suburbs(self) -> Dict[str, str]:
        """Load Queensland suburbs and their postcodes"""
        return {
            'mount isa': '4825',
            'cloncurry': '4822',
            'townsville': '4810',
            'cairns': '4870',
            'brisbane': '4000',
            'gold coast': '4217',
            'sunshine coast': '4558'
        }
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute validation task"""
        task_type = task.task_type
        payload = task.payload
        
        if task_type == "validate_service":
            return await self._validate_service_data(payload)
        elif task_type == "validate_contact":
            return await self._validate_contact_information(payload)
        elif task_type == "validate_location":
            return await self._validate_location_data(payload)
        elif task_type == "validate_content":
            return await self._validate_content_quality(payload)
        else:
            raise ValidationException(
                f"Unknown validation task type: {task_type}",
                service_id=payload.get('service_id', 'unknown')
            )
    
    async def _validate_service_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive validation of service data"""
        service_data = payload['service_data']
        service_id = service_data.get('id', 'unknown')
        
        start_time = datetime.utcnow()
        validation_results = []
        
        try:
            # Required fields validation
            validation_results.extend(await self._validate_required_fields(service_data))
            
            # Contact information validation
            validation_results.extend(await self._validate_contact_details(service_data))
            
            # Location validation
            validation_results.extend(await self._validate_location_details(service_data))
            
            # Content quality validation
            validation_results.extend(await self._validate_content_details(service_data))
            
            # Business rules validation
            validation_results.extend(await self._validate_business_rules(service_data))
            
            # Data consistency validation
            validation_results.extend(await self._validate_data_consistency(service_data))
            
            # Generate validation summary
            summary = self._generate_validation_summary(service_id, validation_results, service_data)
            
            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.validation_stats['services_validated'] += 1
            self.validation_stats['total_checks_performed'] += len(validation_results)
            self.validation_stats['validation_time_total'] += processing_time
            
            if summary.overall_score < 0.3:
                self.validation_stats['critical_failures'] += 1
            
            self.logger.info(
                f"Service validation completed",
                service_id=service_id,
                overall_score=summary.overall_score,
                checks_performed=len(validation_results),
                processing_time=processing_time
            )
            
            return {
                'status': 'completed',
                'service_id': service_id,
                'validation_summary': summary.__dict__,
                'processing_time': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Service validation failed", service_id=service_id, error=e)
            return {
                'status': 'failed',
                'service_id': service_id,
                'error': str(e),
                'processing_time': (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _validate_required_fields(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate required fields are present and valid"""
        results = []
        required_fields = ['name', 'description', 'source_url']
        
        for field in required_fields:
            value = service_data.get(field)
            
            if not value:
                results.append(ValidationResult(
                    field=field,
                    check_type="required_field",
                    status="fail",
                    level=ValidationLevel.CRITICAL,
                    message=f"Required field '{field}' is missing",
                    confidence=1.0,
                    suggestions=[f"Add {field} to the service data"]
                ))
            elif isinstance(value, str) and len(value.strip()) == 0:
                results.append(ValidationResult(
                    field=field,
                    check_type="required_field",
                    status="fail",
                    level=ValidationLevel.CRITICAL,
                    message=f"Required field '{field}' is empty",
                    confidence=1.0,
                    suggestions=[f"Provide content for {field}"]
                ))
            else:
                results.append(ValidationResult(
                    field=field,
                    check_type="required_field",
                    status="pass",
                    level=ValidationLevel.INFO,
                    message=f"Required field '{field}' is present",
                    confidence=1.0
                ))
        
        return results
    
    async def _validate_contact_details(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate contact information"""
        results = []
        
        # Phone validation
        phone = service_data.get('phone')
        if phone:
            results.append(await self._validate_phone_number(phone))
        else:
            results.append(ValidationResult(
                field="phone",
                check_type="contact_availability",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message="No phone number provided",
                confidence=0.8,
                suggestions=["Consider adding a phone number for better accessibility"]
            ))
        
        # Email validation
        email = service_data.get('email')
        if email:
            results.append(await self._validate_email_address(email))
        else:
            results.append(ValidationResult(
                field="email",
                check_type="contact_availability",
                status="warning",
                level=ValidationLevel.LOW,
                message="No email address provided",
                confidence=0.6,
                suggestions=["Consider adding an email address for contact"]
            ))
        
        # Website validation
        website = service_data.get('website')
        if website:
            results.append(await self._validate_website_url(website))
        
        return results
    
    async def _validate_phone_number(self, phone: str) -> ValidationResult:
        """Validate phone number format and correctness"""
        try:
            # Clean the phone number
            cleaned_phone = re.sub(r'[^\d+\-\(\)\s]', '', phone)
            
            # Try to parse as Australian number
            parsed_number = phonenumbers.parse(cleaned_phone, "AU")
            
            if phonenumbers.is_valid_number(parsed_number):
                formatted_number = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
                )
                
                return ValidationResult(
                    field="phone",
                    check_type="format_validation",
                    status="pass",
                    level=ValidationLevel.INFO,
                    message="Valid Australian phone number",
                    confidence=0.9,
                    raw_value=phone,
                    validated_value=formatted_number
                )
            else:
                return ValidationResult(
                    field="phone",
                    check_type="format_validation",
                    status="fail",
                    level=ValidationLevel.HIGH,
                    message="Invalid phone number format",
                    confidence=0.8,
                    raw_value=phone,
                    suggestions=["Check phone number format (e.g., (07) 4744 4444)"]
                )
                
        except phonenumbers.phonenumberutil.NumberParseException:
            return ValidationResult(
                field="phone",
                check_type="format_validation",
                status="fail",
                level=ValidationLevel.HIGH,
                message="Unable to parse phone number",
                confidence=0.9,
                raw_value=phone,
                suggestions=["Use standard Australian phone format"]
            )
    
    async def _validate_email_address(self, email: str) -> ValidationResult:
        """Validate email address format and domain"""
        if not re.match(self.patterns['email']['standard'], email):
            return ValidationResult(
                field="email",
                check_type="format_validation",
                status="fail",
                level=ValidationLevel.HIGH,
                message="Invalid email format",
                confidence=0.9,
                raw_value=email,
                suggestions=["Use valid email format (e.g., contact@example.com)"]
            )
        
        # Check for disposable email domains
        domain = email.split('@')[1].lower()
        disposable_domains = ['10minutemail.com', 'tempmail.org', 'mailinator.com']
        
        if domain in disposable_domains:
            return ValidationResult(
                field="email",
                check_type="domain_validation",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message="Email uses disposable domain",
                confidence=0.7,
                raw_value=email,
                suggestions=["Use a permanent email domain for better reliability"]
            )
        
        return ValidationResult(
            field="email",
            check_type="format_validation",
            status="pass",
            level=ValidationLevel.INFO,
            message="Valid email format",
            confidence=0.8,
            raw_value=email,
            validated_value=email.lower()
        )
    
    async def _validate_website_url(self, website: str) -> ValidationResult:
        """Validate website URL and accessibility"""
        if not re.match(self.patterns['website']['valid_url'], website):
            return ValidationResult(
                field="website",
                check_type="format_validation",
                status="fail",
                level=ValidationLevel.MEDIUM,
                message="Invalid website URL format",
                confidence=0.9,
                raw_value=website,
                suggestions=["Use valid URL format (e.g., https://example.com)"]
            )
        
        # Check if HTTPS
        if not website.startswith('https://'):
            return ValidationResult(
                field="website",
                check_type="security_validation",
                status="warning",
                level=ValidationLevel.LOW,
                message="Website does not use HTTPS",
                confidence=0.6,
                raw_value=website,
                suggestions=["Consider using HTTPS for better security"]
            )
        
        # Try to access the website
        try:
            async with self.http_session.get(website, timeout=10) as response:
                if response.status == 200:
                    return ValidationResult(
                        field="website",
                        check_type="accessibility_validation",
                        status="pass",
                        level=ValidationLevel.INFO,
                        message="Website is accessible",
                        confidence=0.8,
                        raw_value=website,
                        validated_value=website
                    )
                else:
                    return ValidationResult(
                        field="website",
                        check_type="accessibility_validation",
                        status="warning",
                        level=ValidationLevel.MEDIUM,
                        message=f"Website returned HTTP {response.status}",
                        confidence=0.7,
                        raw_value=website,
                        suggestions=["Check if website is currently available"]
                    )
        except Exception as e:
            return ValidationResult(
                field="website",
                check_type="accessibility_validation",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message="Website is not accessible",
                confidence=0.6,
                raw_value=website,
                suggestions=["Verify website URL is correct and accessible"]
            )
    
    async def _validate_location_details(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate location information"""
        results = []
        
        # Address validation
        address = service_data.get('address')
        if address:
            results.append(self._validate_address_format(address))
        
        # Postcode validation
        postcode = service_data.get('postcode')
        if postcode:
            results.append(self._validate_postcode(postcode))
        
        # Suburb/location consistency
        suburb = service_data.get('suburb', '').lower()
        if suburb and postcode:
            results.append(self._validate_suburb_postcode_consistency(suburb, postcode))
        
        return results
    
    def _validate_address_format(self, address: str) -> ValidationResult:
        """Validate address format"""
        if re.search(self.patterns['address']['australian_street'], address):
            return ValidationResult(
                field="address",
                check_type="format_validation",
                status="pass",
                level=ValidationLevel.INFO,
                message="Valid Australian street address format",
                confidence=0.8,
                raw_value=address,
                validated_value=address.title()
            )
        elif re.search(self.patterns['address']['po_box'], address):
            return ValidationResult(
                field="address",
                check_type="format_validation",
                status="pass",
                level=ValidationLevel.INFO,
                message="Valid PO Box address",
                confidence=0.7,
                raw_value=address,
                validated_value=address.upper()
            )
        else:
            return ValidationResult(
                field="address",
                check_type="format_validation",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message="Address format not recognized",
                confidence=0.6,
                raw_value=address,
                suggestions=["Use standard Australian address format"]
            )
    
    def _validate_postcode(self, postcode: str) -> ValidationResult:
        """Validate Australian postcode"""
        if re.match(self.patterns['postcode']['australian'], postcode):
            if postcode in self.australian_postcodes:
                location_info = self.australian_postcodes[postcode]
                return ValidationResult(
                    field="postcode",
                    check_type="format_validation",
                    status="pass",
                    level=ValidationLevel.INFO,
                    message=f"Valid postcode for {location_info['suburb']}, {location_info['state']}",
                    confidence=0.9,
                    raw_value=postcode,
                    validated_value=postcode
                )
            else:
                return ValidationResult(
                    field="postcode",
                    check_type="format_validation",
                    status="pass",
                    level=ValidationLevel.INFO,
                    message="Valid Australian postcode format",
                    confidence=0.7,
                    raw_value=postcode,
                    validated_value=postcode
                )
        else:
            return ValidationResult(
                field="postcode",
                check_type="format_validation",
                status="fail",
                level=ValidationLevel.HIGH,
                message="Invalid Australian postcode format",
                confidence=0.9,
                raw_value=postcode,
                suggestions=["Use 4-digit Australian postcode"]
            )
    
    def _validate_suburb_postcode_consistency(self, suburb: str, postcode: str) -> ValidationResult:
        """Validate suburb and postcode consistency"""
        if suburb in self.qld_suburbs:
            expected_postcode = self.qld_suburbs[suburb]
            if expected_postcode == postcode:
                return ValidationResult(
                    field="location_consistency",
                    check_type="consistency_validation",
                    status="pass",
                    level=ValidationLevel.INFO,
                    message="Suburb and postcode are consistent",
                    confidence=0.9
                )
            else:
                return ValidationResult(
                    field="location_consistency",
                    check_type="consistency_validation",
                    status="warning",
                    level=ValidationLevel.MEDIUM,
                    message=f"Suburb '{suburb}' typically uses postcode {expected_postcode}, not {postcode}",
                    confidence=0.7,
                    suggestions=[f"Verify postcode for {suburb}"]
                )
        else:
            return ValidationResult(
                field="location_consistency",
                check_type="consistency_validation",
                status="info",
                level=ValidationLevel.LOW,
                message="Cannot verify suburb-postcode consistency",
                confidence=0.5
            )
    
    async def _validate_content_details(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate content quality"""
        results = []
        
        # Name validation
        name = service_data.get('name', '')
        if name:
            results.append(self._validate_service_name(name))
        
        # Description validation
        description = service_data.get('description', '')
        if description:
            results.append(self._validate_description_quality(description))
        
        return results
    
    def _validate_service_name(self, name: str) -> ValidationResult:
        """Validate service name quality"""
        if len(name) < 3:
            return ValidationResult(
                field="name",
                check_type="content_quality",
                status="fail",
                level=ValidationLevel.HIGH,
                message="Service name is too short",
                confidence=0.9,
                raw_value=name,
                suggestions=["Provide a more descriptive service name"]
            )
        elif len(name) > 100:
            return ValidationResult(
                field="name",
                check_type="content_quality",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message="Service name is very long",
                confidence=0.7,
                raw_value=name,
                suggestions=["Consider shortening the service name"]
            )
        elif name.isupper():
            return ValidationResult(
                field="name",
                check_type="content_quality",
                status="warning",
                level=ValidationLevel.LOW,
                message="Service name is in all caps",
                confidence=0.6,
                raw_value=name,
                validated_value=name.title(),
                suggestions=["Use proper capitalization"]
            )
        else:
            return ValidationResult(
                field="name",
                check_type="content_quality",
                status="pass",
                level=ValidationLevel.INFO,
                message="Service name has good quality",
                confidence=0.8,
                raw_value=name,
                validated_value=name.strip()
            )
    
    def _validate_description_quality(self, description: str) -> ValidationResult:
        """Validate description content quality"""
        if len(description) < 20:
            return ValidationResult(
                field="description",
                check_type="content_quality",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message="Description is very short",
                confidence=0.8,
                raw_value=description,
                suggestions=["Provide a more detailed description"]
            )
        elif len(description) > 1000:
            return ValidationResult(
                field="description",
                check_type="content_quality",
                status="warning",
                level=ValidationLevel.LOW,
                message="Description is very long",
                confidence=0.6,
                raw_value=description,
                suggestions=["Consider shortening the description"]
            )
        
        # Basic language quality check
        try:
            blob = TextBlob(description)
            if blob.sentiment.polarity < -0.5:
                return ValidationResult(
                    field="description",
                    check_type="content_quality",
                    status="warning",
                    level=ValidationLevel.LOW,
                    message="Description has negative sentiment",
                    confidence=0.5,
                    raw_value=description,
                    suggestions=["Review description for neutral or positive tone"]
                )
        except:
            pass
        
        return ValidationResult(
            field="description",
            check_type="content_quality",
            status="pass",
            level=ValidationLevel.INFO,
            message="Description has good quality",
            confidence=0.7,
            raw_value=description,
            validated_value=description.strip()
        )
    
    async def _validate_business_rules(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate business-specific rules"""
        results = []
        
        # Contact information requirement
        has_phone = bool(service_data.get('phone'))
        has_email = bool(service_data.get('email'))
        has_website = bool(service_data.get('website'))
        
        if not (has_phone or has_email or has_website):
            results.append(ValidationResult(
                field="contact_methods",
                check_type="business_rule",
                status="fail",
                level=ValidationLevel.CRITICAL,
                message="Service must have at least one contact method",
                confidence=1.0,
                suggestions=["Add phone, email, or website contact information"]
            ))
        
        # Category validation
        category = service_data.get('category', '').lower()
        valid_categories = [
            'health', 'mental_health', 'disability', 'aged_care', 'youth',
            'family', 'housing', 'employment', 'education', 'legal',
            'emergency', 'transport', 'general'
        ]
        
        if category and category not in valid_categories:
            results.append(ValidationResult(
                field="category",
                check_type="business_rule",
                status="warning",
                level=ValidationLevel.MEDIUM,
                message=f"Unknown service category: {category}",
                confidence=0.8,
                suggestions=[f"Use one of: {', '.join(valid_categories)}"]
            ))
        
        return results
    
    async def _validate_data_consistency(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate data consistency across fields"""
        results = []
        
        # Website and email domain consistency
        website = service_data.get('website', '')
        email = service_data.get('email', '')
        
        if website and email:
            try:
                website_domain = tldextract.extract(website).registered_domain
                email_domain = email.split('@')[1]
                
                if website_domain.lower() == email_domain.lower():
                    results.append(ValidationResult(
                        field="domain_consistency",
                        check_type="consistency_validation",
                        status="pass",
                        level=ValidationLevel.INFO,
                        message="Website and email domains match",
                        confidence=0.8
                    ))
                else:
                    results.append(ValidationResult(
                        field="domain_consistency",
                        check_type="consistency_validation",
                        status="info",
                        level=ValidationLevel.LOW,
                        message="Website and email use different domains",
                        confidence=0.5,
                        suggestions=["Verify both website and email are correct"]
                    ))
            except:
                pass
        
        return results
    
    def _generate_validation_summary(
        self, 
        service_id: str, 
        results: List[ValidationResult], 
        service_data: Dict[str, Any]
    ) -> ValidationSummary:
        """Generate comprehensive validation summary"""
        
        total_checks = len(results)
        passed = sum(1 for r in results if r.status == "pass")
        failed = sum(1 for r in results if r.status == "fail")
        warnings = sum(1 for r in results if r.status == "warning")
        
        # Calculate overall score
        score_weights = {
            ValidationLevel.CRITICAL: 1.0,
            ValidationLevel.HIGH: 0.8,
            ValidationLevel.MEDIUM: 0.5,
            ValidationLevel.LOW: 0.2,
            ValidationLevel.INFO: 0.1
        }
        
        total_weight = 0
        achieved_weight = 0
        
        for result in results:
            weight = score_weights[result.level]
            total_weight += weight
            
            if result.status == "pass":
                achieved_weight += weight
            elif result.status == "warning":
                achieved_weight += weight * 0.5
        
        overall_score = achieved_weight / max(total_weight, 1)
        
        # Identify critical issues
        critical_issues = [r for r in results if r.level == ValidationLevel.CRITICAL and r.status == "fail"]
        
        # Generate recommendations
        recommendations = []
        for result in results:
            if result.status in ["fail", "warning"] and result.suggestions:
                recommendations.extend(result.suggestions)
        
        # Create validated data with corrections
        validated_data = service_data.copy()
        for result in results:
            if result.validated_value is not None:
                validated_data[result.field] = result.validated_value
        
        return ValidationSummary(
            service_id=service_id,
            total_checks=total_checks,
            passed=passed,
            failed=failed,
            warnings=warnings,
            overall_score=overall_score,
            critical_issues=critical_issues,
            recommendations=list(set(recommendations)),
            validated_data=validated_data
        )
    
    async def _validate_contact_information(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate specific contact information"""
        contact_data = payload['contact_data']
        results = []
        
        if 'phone' in contact_data:
            results.append(await self._validate_phone_number(contact_data['phone']))
        
        if 'email' in contact_data:
            results.append(await self._validate_email_address(contact_data['email']))
        
        if 'website' in contact_data:
            results.append(await self._validate_website_url(contact_data['website']))
        
        return {
            'status': 'completed',
            'validation_results': [r.__dict__ for r in results]
        }
    
    async def _validate_location_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location data"""
        location_data = payload['location_data']
        results = await self._validate_location_details(location_data)
        
        return {
            'status': 'completed',
            'validation_results': [r.__dict__ for r in results]
        }
    
    async def _validate_content_quality(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content quality"""
        content_data = payload['content_data']
        results = await self._validate_content_details(content_data)
        
        return {
            'status': 'completed',
            'validation_results': [r.__dict__ for r in results]
        }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation performance statistics"""
        total_services = self.validation_stats['services_validated']
        avg_validation_time = (
            self.validation_stats['validation_time_total'] / max(1, total_services)
        )
        
        return {
            'services_validated': total_services,
            'total_checks_performed': self.validation_stats['total_checks_performed'],
            'critical_failures': self.validation_stats['critical_failures'],
            'avg_checks_per_service': (
                self.validation_stats['total_checks_performed'] / max(1, total_services)
            ),
            'avg_validation_time': avg_validation_time,
            'critical_failure_rate': (
                self.validation_stats['critical_failures'] / max(1, total_services)
            )
        }