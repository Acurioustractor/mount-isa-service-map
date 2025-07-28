#!/usr/bin/env python3
"""
Data Validation and Quality Assurance System
Advanced multi-layer validation for scraped service information
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import requests
from urllib.parse import urlparse
import phonenumbers
import email_validator
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import difflib
from textdistance import levenshtein
import hashlib
import sqlite3
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class ValidationLevel(Enum):
    TIER_1_AUTOMATED = "tier_1_automated"
    TIER_2_CROSS_REFERENCE = "tier_2_cross_reference"
    TIER_3_COMMUNITY = "tier_3_community"
    TIER_4_PROFESSIONAL = "tier_4_professional"


class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    MANUAL_REVIEW = "manual_review"
    CONFLICTED = "conflicted"


class ConfidenceLevel(Enum):
    VERY_HIGH = 0.9
    HIGH = 0.75
    MEDIUM = 0.6
    LOW = 0.4
    VERY_LOW = 0.2


@dataclass
class ValidationResult:
    """Result of a validation check"""
    validation_type: str
    status: ValidationStatus
    confidence: float
    details: Dict[str, Any]
    timestamp: datetime
    validator_id: str
    issues_found: List[str] = None
    suggestions: List[str] = None

    def __post_init__(self):
        if self.issues_found is None:
            self.issues_found = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class CrossReferenceMatch:
    """Match found during cross-reference validation"""
    source_url: str
    source_name: str
    match_score: float
    matched_fields: Dict[str, Any]
    conflicting_fields: Dict[str, Any]
    confidence: float


@dataclass
class QualityMetrics:
    """Overall quality metrics for a service record"""
    completeness_score: float
    accuracy_score: float
    freshness_score: float
    consistency_score: float
    overall_quality: float
    validation_count: int
    last_updated: datetime


class Tier1AutomatedValidator:
    """Tier 1: Automated validation of data formats and basic consistency"""
    
    def __init__(self):
        self.logger = logging.getLogger("validator.tier1")
        self.geocoder = Nominatim(user_agent="mount_isa_service_validator")
        
        # Australian postcode patterns
        self.aus_postcode_pattern = r'\b[0-9]{4}\b'
        self.qld_postcode_ranges = [(4000, 4999), (9000, 9999)]
        
        # Mount Isa region specific patterns
        self.mount_isa_postcodes = ['4825', '4828', '4829', '4830']
        self.regional_suburbs = [
            'Mount Isa', 'Camooweal', 'Cloncurry', 'Dajarra', 
            'Duchess', 'McKinlay', 'Mornington Island', 'Normanton'
        ]
    
    async def validate_service(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Perform comprehensive Tier 1 validation"""
        results = []
        
        # Required field validation
        results.append(await self._validate_required_fields(service_data))
        
        # Contact information validation
        if service_data.get('phone'):
            results.append(await self._validate_phone_number(service_data['phone']))
        
        if service_data.get('email'):
            results.append(await self._validate_email_address(service_data['email']))
        
        if service_data.get('website'):
            results.append(await self._validate_website_url(service_data['website']))
        
        # Address validation
        if service_data.get('address'):
            results.append(await self._validate_address(service_data))
        
        # Content validation
        results.append(await self._validate_content_quality(service_data))
        
        # Consistency validation
        results.append(await self._validate_internal_consistency(service_data))
        
        # Format validation
        results.append(await self._validate_data_formats(service_data))
        
        return [r for r in results if r is not None]
    
    async def _validate_required_fields(self, service_data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate that required fields are present and non-empty"""
        required_fields = ['name', 'category', 'description']
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in service_data:
                missing_fields.append(field)
            elif not service_data[field] or str(service_data[field]).strip() == '':
                empty_fields.append(field)
        
        issues = []
        if missing_fields:
            issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        if empty_fields:
            issues.append(f"Empty required fields: {', '.join(empty_fields)}")
        
        status = ValidationStatus.FAILED if issues else ValidationStatus.PASSED
        confidence = 1.0 if not issues else max(0.1, 1.0 - (len(issues) * 0.3))
        
        return ValidationResult(
            validation_type="required_fields",
            status=status,
            confidence=confidence,
            details={
                'missing_fields': missing_fields,
                'empty_fields': empty_fields,
                'checked_fields': required_fields
            },
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues
        )
    
    async def _validate_phone_number(self, phone: str) -> ValidationResult:
        """Validate Australian phone number format"""
        issues = []
        suggestions = []
        
        try:
            # Parse as Australian number
            parsed_number = phonenumbers.parse(phone, "AU")
            
            # Check if valid
            is_valid = phonenumbers.is_valid_number(parsed_number)
            is_possible = phonenumbers.is_possible_number(parsed_number)
            
            if not is_valid:
                if is_possible:
                    issues.append("Phone number format is questionable but possible")
                    suggestions.append("Verify phone number format manually")
                else:
                    issues.append("Invalid phone number format")
                    suggestions.append("Check phone number and reformat if necessary")
            
            # Check if it's a mobile vs landline
            number_type = phonenumbers.number_type(parsed_number)
            
            formatted_national = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
            )
            formatted_international = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            
            details = {
                'original': phone,
                'formatted_national': formatted_national,
                'formatted_international': formatted_international,
                'is_valid': is_valid,
                'is_possible': is_possible,
                'number_type': str(number_type),
                'country_code': parsed_number.country_code,
                'national_number': parsed_number.national_number
            }
            
        except phonenumbers.NumberParseException as e:
            issues.append(f"Could not parse phone number: {e}")
            suggestions.append("Check phone number format and country code")
            details = {'original': phone, 'parse_error': str(e)}
            is_valid = False
        
        status = ValidationStatus.PASSED if is_valid and not issues else ValidationStatus.FAILED
        confidence = 0.9 if is_valid else 0.3 if not issues else 0.1
        
        return ValidationResult(
            validation_type="phone_number",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )
    
    async def _validate_email_address(self, email: str) -> ValidationResult:
        """Validate email address format and domain"""
        issues = []
        suggestions = []
        
        try:
            # Validate email format
            validated_email = email_validator.validate_email(email)
            
            details = {
                'original': email,
                'normalized': validated_email.email,
                'local_part': validated_email.local,
                'domain': validated_email.domain,
                'domain_literal': validated_email.domain_literal,
                'ascii_email': validated_email.ascii_email,
                'ascii_local': validated_email.ascii_local,
                'ascii_domain': validated_email.ascii_domain
            }
            
            # Check for common domain issues
            if '@gmail.' in email.lower() or '@hotmail.' in email.lower():
                suggestions.append("Personal email domain detected - consider verifying this is the official contact")
            
            # Check for suspicious patterns
            if any(pattern in email.lower() for pattern in ['noreply', 'donotreply', 'no-reply']):
                issues.append("Email appears to be a no-reply address")
                suggestions.append("Verify this is the correct contact email for the service")
            
            status = ValidationStatus.PASSED
            confidence = 0.9
            
        except email_validator.EmailNotValidError as e:
            issues.append(f"Invalid email format: {e}")
            suggestions.append("Check email address format")
            details = {'original': email, 'validation_error': str(e)}
            status = ValidationStatus.FAILED
            confidence = 0.1
        
        return ValidationResult(
            validation_type="email_address",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )
    
    async def _validate_website_url(self, url: str) -> ValidationResult:
        """Validate website URL format and accessibility"""
        issues = []
        suggestions = []
        
        # Parse URL
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                issues.append("URL missing protocol (http/https)")
                suggestions.append("Add 'https://' to the beginning of the URL")
            elif parsed.scheme not in ['http', 'https']:
                issues.append(f"Unusual URL protocol: {parsed.scheme}")
            
            if not parsed.netloc:
                issues.append("URL missing domain name")
                suggestions.append("Provide complete URL with domain")
            
            # Check for accessibility (with timeout)
            accessible = False
            status_code = None
            
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.head(url) as response:
                        status_code = response.status
                        accessible = status_code < 400
                        
                        if status_code >= 400:
                            issues.append(f"Website returned error code: {status_code}")
                            suggestions.append("Check if website URL is correct or if site is temporarily down")
                        
            except asyncio.TimeoutError:
                issues.append("Website request timed out")
                suggestions.append("Website may be slow or temporarily unavailable")
            except Exception as e:
                issues.append(f"Could not access website: {str(e)}")
                suggestions.append("Verify website URL is correct")
            
            details = {
                'original': url,
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'accessible': accessible,
                'status_code': status_code
            }
            
        except Exception as e:
            issues.append(f"Invalid URL format: {e}")
            suggestions.append("Check URL format")
            details = {'original': url, 'parse_error': str(e)}
            accessible = False
        
        if accessible and not issues:
            status = ValidationStatus.PASSED
            confidence = 0.9
        elif accessible:
            status = ValidationStatus.PASSED
            confidence = 0.7
        else:
            status = ValidationStatus.FAILED
            confidence = 0.3
        
        return ValidationResult(
            validation_type="website_url",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )
    
    async def _validate_address(self, service_data: Dict[str, Any]) -> ValidationResult:
        """Validate address information and geocoding"""
        issues = []
        suggestions = []
        
        address = service_data.get('address', '')
        suburb = service_data.get('suburb', 'Mount Isa')
        state = service_data.get('state', 'QLD')
        postcode = service_data.get('postcode', '4825')
        
        # Construct full address
        full_address = f"{address}, {suburb}, {state} {postcode}, Australia"
        
        # Validate postcode format
        if not re.match(self.aus_postcode_pattern, postcode):
            issues.append(f"Invalid Australian postcode format: {postcode}")
        elif postcode not in self.mount_isa_postcodes:
            suggestions.append(f"Postcode {postcode} is outside Mount Isa region - verify location")
        
        # Validate suburb
        if suburb not in self.regional_suburbs:
            suggestions.append(f"Suburb '{suburb}' not in known Mount Isa region suburbs")
        
        # Attempt geocoding
        geocoding_success = False
        coordinates = None
        
        try:
            location = self.geocoder.geocode(full_address, timeout=10)
            if location:
                geocoding_success = True
                coordinates = (location.latitude, location.longitude)
                
                # Check if coordinates are in reasonable range for Mount Isa region
                # Mount Isa is approximately -20.7256° S, 139.4927° E
                if not (-25 <= location.latitude <= -15 and 135 <= location.longitude <= 145):
                    issues.append("Geocoded coordinates are outside Queensland region")
                    suggestions.append("Verify address details are correct")
            else:
                issues.append("Could not geocode address")
                suggestions.append("Check address format and verify all components are correct")
        
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            suggestions.append("Geocoding service temporarily unavailable - retry later")
        except Exception as e:
            issues.append(f"Geocoding error: {e}")
        
        details = {
            'address': address,
            'suburb': suburb,
            'state': state,
            'postcode': postcode,
            'full_address': full_address,
            'geocoding_success': geocoding_success,
            'coordinates': coordinates,
            'in_region_postcodes': postcode in self.mount_isa_postcodes,
            'known_suburb': suburb in self.regional_suburbs
        }
        
        # Determine status and confidence
        if geocoding_success and not issues:
            status = ValidationStatus.PASSED
            confidence = 0.9
        elif geocoding_success:
            status = ValidationStatus.PASSED
            confidence = 0.7
        elif not issues:
            status = ValidationStatus.PENDING
            confidence = 0.5
        else:
            status = ValidationStatus.FAILED
            confidence = 0.3
        
        return ValidationResult(
            validation_type="address_validation",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )
    
    async def _validate_content_quality(self, service_data: Dict[str, Any]) -> ValidationResult:
        """Validate the quality of textual content"""
        issues = []
        suggestions = []
        
        name = service_data.get('name', '')
        description = service_data.get('description', '')
        
        # Name validation
        if len(name) < 3:
            issues.append("Service name is too short")
        elif len(name) > 100:
            issues.append("Service name is unusually long")
            suggestions.append("Consider shortening the service name")
        
        # Check for placeholder text
        placeholder_patterns = [
            'lorem ipsum', 'placeholder', 'insert text here',
            'coming soon', 'under construction', 'test'
        ]
        
        if any(pattern in name.lower() for pattern in placeholder_patterns):
            issues.append("Service name contains placeholder text")
        
        if any(pattern in description.lower() for pattern in placeholder_patterns):
            issues.append("Description contains placeholder text")
        
        # Description validation
        if len(description) < 20:
            issues.append("Description is too short - should be at least 20 characters")
            suggestions.append("Provide more detailed description of the service")
        elif len(description) > 1000:
            suggestions.append("Description is very long - consider summarizing key points")
        
        # Check for repeated characters or words
        if re.search(r'(.)\1{5,}', description):
            issues.append("Description contains excessive repeated characters")
        
        # Basic spell check (simple approach)
        if description.count('???') > 0:
            issues.append("Description contains question marks that may indicate missing information")
        
        # Check for HTML/XML tags that shouldn't be there
        if re.search(r'<[^>]+>', description):
            issues.append("Description contains HTML/XML tags")
            suggestions.append("Remove HTML formatting from description")
        
        details = {
            'name_length': len(name),
            'description_length': len(description),
            'contains_html': bool(re.search(r'<[^>]+>', description)),
            'word_count': len(description.split()),
            'sentence_count': len(re.split(r'[.!?]+', description))
        }
        
        if not issues:
            status = ValidationStatus.PASSED
            confidence = 0.8
        elif len(issues) <= 2:
            status = ValidationStatus.PASSED
            confidence = 0.6
        else:
            status = ValidationStatus.FAILED
            confidence = 0.4
        
        return ValidationResult(
            validation_type="content_quality",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )
    
    async def _validate_internal_consistency(self, service_data: Dict[str, Any]) -> ValidationResult:
        """Validate internal consistency of the service data"""
        issues = []
        suggestions = []
        
        name = service_data.get('name', '').lower()
        description = service_data.get('description', '').lower()
        category = service_data.get('category', '').lower()
        website = service_data.get('website', '').lower()
        
        # Check if category matches content
        category_keywords = {
            'health': ['health', 'medical', 'doctor', 'clinic', 'hospital'],
            'mental_health': ['mental', 'psychology', 'counselling', 'therapy'],
            'disability': ['disability', 'ndis', 'accessible', 'special needs'],
            'aged_care': ['aged', 'elderly', 'seniors', 'retirement'],
            'youth': ['youth', 'young', 'teenagers', 'adolescent'],
            'family': ['family', 'children', 'parenting', 'childcare'],
            'housing': ['housing', 'accommodation', 'rental', 'homeless'],
            'employment': ['employment', 'job', 'career', 'training', 'work'],
            'education': ['education', 'school', 'training', 'learning'],
            'legal': ['legal', 'law', 'advice', 'court', 'justice'],
            'emergency': ['emergency', 'crisis', 'urgent', '24 hour'],
            'transport': ['transport', 'bus', 'taxi', 'mobility']
        }
        
        if category in category_keywords:
            keywords = category_keywords[category]
            content_text = f"{name} {description}"
            
            keyword_matches = sum(1 for keyword in keywords if keyword in content_text)
            if keyword_matches == 0:
                issues.append(f"Content doesn't match category '{category}' - no relevant keywords found")
                suggestions.append("Verify service category is correct")
        
        # Check if website domain matches organization name
        if website and name:
            domain = website.replace('www.', '').split('/')[0]
            name_words = name.split()
            
            domain_match = any(word in domain for word in name_words if len(word) > 3)
            if not domain_match and len(name_words) > 0:
                suggestions.append("Website domain doesn't clearly match organization name")
        
        # Check for contradictory information
        if 'closed' in description and 'open' in description:
            suggestions.append("Description contains contradictory information about operating status")
        
        details = {
            'category_keyword_match': keyword_matches if category in category_keywords else None,
            'domain_name_similarity': domain_match if website and name else None
        }
        
        status = ValidationStatus.PASSED if not issues else ValidationStatus.MANUAL_REVIEW
        confidence = 0.8 if not issues else 0.6
        
        return ValidationResult(
            validation_type="internal_consistency",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )
    
    async def _validate_data_formats(self, service_data: Dict[str, Any]) -> ValidationResult:
        """Validate data formats and types"""
        issues = []
        suggestions = []
        
        # Check operating hours format if present
        operating_hours = service_data.get('operating_hours')
        if operating_hours:
            if isinstance(operating_hours, str):
                # Try to parse common formats
                if not re.search(r'\d+:\d+', operating_hours):
                    issues.append("Operating hours don't contain recognizable time format")
            elif isinstance(operating_hours, dict):
                # Validate day names and time formats
                valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                for day, hours in operating_hours.items():
                    if day.lower() not in valid_days:
                        issues.append(f"Invalid day name in operating hours: {day}")
        
        # Check services offered format
        services_offered = service_data.get('services_offered')
        if services_offered:
            if not isinstance(services_offered, (list, str)):
                issues.append("Services offered should be a list or string")
        
        details = {
            'operating_hours_format': type(operating_hours).__name__ if operating_hours else None,
            'services_offered_format': type(services_offered).__name__ if services_offered else None
        }
        
        status = ValidationStatus.PASSED if not issues else ValidationStatus.FAILED
        confidence = 0.9 if not issues else 0.5
        
        return ValidationResult(
            validation_type="data_formats",
            status=status,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            validator_id="tier1_automated",
            issues_found=issues,
            suggestions=suggestions
        )


class Tier2CrossReferenceValidator:
    """Tier 2: Cross-reference validation against multiple sources"""
    
    def __init__(self, reference_sources: List[str]):
        self.logger = logging.getLogger("validator.tier2")
        self.reference_sources = reference_sources
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
    async def validate_service(self, service_data: Dict[str, Any]) -> List[ValidationResult]:
        """Perform cross-reference validation"""
        results = []
        
        # Find potential matches in reference sources
        matches = await self._find_cross_references(service_data)
        
        # Validate against each match
        for match in matches:
            validation_result = await self._validate_against_reference(service_data, match)
            results.append(validation_result)
        
        # Aggregate validation
        if matches:
            aggregate_result = self._aggregate_cross_reference_results(results)
            results.append(aggregate_result)
        
        return results
    
    async def _find_cross_references(self, service_data: Dict[str, Any]) -> List[CrossReferenceMatch]:
        """Find potential matches in reference databases"""
        # This would query external reference sources
        # For demonstration, return mock matches
        return []
    
    async def _validate_against_reference(self, service_data: Dict[str, Any], 
                                        reference_match: CrossReferenceMatch) -> ValidationResult:
        """Validate service data against a reference match"""
        # Compare fields and identify conflicts
        conflicts = []
        confirmations = []
        
        # This would perform detailed field-by-field comparison
        # Return validation result based on comparison
        
        return ValidationResult(
            validation_type="cross_reference",
            status=ValidationStatus.PASSED,
            confidence=reference_match.confidence,
            details={'reference_source': reference_match.source_name},
            timestamp=datetime.now(),
            validator_id="tier2_cross_reference"
        )
    
    def _aggregate_cross_reference_results(self, results: List[ValidationResult]) -> ValidationResult:
        """Aggregate multiple cross-reference validation results"""
        if not results:
            return ValidationResult(
                validation_type="cross_reference_aggregate",
                status=ValidationStatus.FAILED,
                confidence=0.0,
                details={'message': 'No cross-references found'},
                timestamp=datetime.now(),
                validator_id="tier2_cross_reference"
            )
        
        # Calculate aggregate confidence
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        # Determine overall status
        passed_count = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        overall_status = ValidationStatus.PASSED if passed_count >= len(results) / 2 else ValidationStatus.FAILED
        
        return ValidationResult(
            validation_type="cross_reference_aggregate",
            status=overall_status,
            confidence=avg_confidence,
            details={
                'total_references': len(results),
                'passed_references': passed_count,
                'average_confidence': avg_confidence
            },
            timestamp=datetime.now(),
            validator_id="tier2_cross_reference"
        )


class QualityAssuranceOrchestrator:
    """Orchestrates the entire quality assurance process"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("qa_orchestrator")
        
        # Initialize validators
        self.tier1_validator = Tier1AutomatedValidator()
        self.tier2_validator = Tier2CrossReferenceValidator(
            config.get('reference_sources', [])
        )
        
        # Quality thresholds
        self.quality_thresholds = {
            'minimum_confidence': 0.6,
            'minimum_completeness': 0.7,
            'maximum_staleness_days': 30
        }
    
    async def validate_service_comprehensive(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive validation across all tiers"""
        validation_report = {
            'service_id': service_data.get('id'),
            'validation_timestamp': datetime.now(),
            'tier1_results': [],
            'tier2_results': [],
            'overall_quality': None,
            'recommendations': [],
            'requires_manual_review': False
        }
        
        # Tier 1 validation
        self.logger.info(f"Starting Tier 1 validation for service {service_data.get('name', 'Unknown')}")
        tier1_results = await self.tier1_validator.validate_service(service_data)
        validation_report['tier1_results'] = [asdict(r) for r in tier1_results]
        
        # Tier 2 validation (if Tier 1 passes basic checks)
        tier1_passed = all(r.status in [ValidationStatus.PASSED, ValidationStatus.PENDING] 
                          for r in tier1_results)
        
        if tier1_passed:
            self.logger.info(f"Starting Tier 2 validation for service {service_data.get('name', 'Unknown')}")
            tier2_results = await self.tier2_validator.validate_service(service_data)
            validation_report['tier2_results'] = [asdict(r) for r in tier2_results]
        
        # Calculate overall quality metrics
        quality_metrics = self._calculate_quality_metrics(tier1_results, tier2_results)
        validation_report['overall_quality'] = asdict(quality_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(tier1_results, tier2_results, quality_metrics)
        validation_report['recommendations'] = recommendations
        
        # Determine if manual review is needed
        validation_report['requires_manual_review'] = self._requires_manual_review(
            tier1_results, tier2_results, quality_metrics
        )
        
        return validation_report
    
    def _calculate_quality_metrics(self, tier1_results: List[ValidationResult], 
                                 tier2_results: List[ValidationResult]) -> QualityMetrics:
        """Calculate overall quality metrics"""
        all_results = tier1_results + tier2_results
        
        if not all_results:
            return QualityMetrics(
                completeness_score=0.0,
                accuracy_score=0.0,
                freshness_score=0.0,
                consistency_score=0.0,
                overall_quality=0.0,
                validation_count=0,
                last_updated=datetime.now()
            )
        
        # Calculate component scores
        passed_count = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
        accuracy_score = passed_count / len(all_results)
        
        avg_confidence = sum(r.confidence for r in all_results) / len(all_results)
        
        # Completeness based on number of fields validated
        completeness_score = min(len(all_results) / 10.0, 1.0)  # Expect ~10 validation checks
        
        # Freshness score (assume recent for new validations)
        freshness_score = 1.0
        
        # Consistency score based on confidence variance
        confidence_variance = np.var([r.confidence for r in all_results])
        consistency_score = max(0.0, 1.0 - confidence_variance)
        
        # Overall quality (weighted average)
        overall_quality = (
            accuracy_score * 0.4 +
            avg_confidence * 0.3 +
            completeness_score * 0.2 +
            consistency_score * 0.1
        )
        
        return QualityMetrics(
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            freshness_score=freshness_score,
            consistency_score=consistency_score,
            overall_quality=overall_quality,
            validation_count=len(all_results),
            last_updated=datetime.now()
        )
    
    def _generate_recommendations(self, tier1_results: List[ValidationResult], 
                                tier2_results: List[ValidationResult],
                                quality_metrics: QualityMetrics) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        all_results = tier1_results + tier2_results
        
        # Collect all suggestions from validation results
        for result in all_results:
            recommendations.extend(result.suggestions)
        
        # Add quality-based recommendations
        if quality_metrics.overall_quality < 0.6:
            recommendations.append("Overall data quality is below acceptable threshold - comprehensive review needed")
        
        if quality_metrics.accuracy_score < 0.7:
            recommendations.append("Multiple validation failures detected - verify data sources")
        
        if quality_metrics.completeness_score < 0.5:
            recommendations.append("Service record appears incomplete - gather additional information")
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def _requires_manual_review(self, tier1_results: List[ValidationResult], 
                              tier2_results: List[ValidationResult],
                              quality_metrics: QualityMetrics) -> bool:
        """Determine if manual review is required"""
        all_results = tier1_results + tier2_results
        
        # Check for manual review flags
        manual_review_flags = [
            r for r in all_results 
            if r.status == ValidationStatus.MANUAL_REVIEW
        ]
        
        # Check for conflicts
        conflicts = [
            r for r in all_results 
            if r.status == ValidationStatus.CONFLICTED
        ]
        
        # Check for low quality scores
        low_quality = quality_metrics.overall_quality < self.quality_thresholds['minimum_confidence']
        
        return bool(manual_review_flags or conflicts or low_quality)


async def main():
    """Demonstration of the validation system"""
    # Sample service data for testing
    sample_service = {
        'id': 'test_001',
        'name': 'Mount Isa Community Health Centre',
        'category': 'health',
        'description': 'Comprehensive health services for the Mount Isa community including general practice, mental health support, and specialist clinics.',
        'phone': '07 4744 4444',
        'email': 'info@mtisahealth.qld.gov.au',
        'website': 'https://www.health.qld.gov.au/north-west/services/mount-isa',
        'address': '23 Camooweal Street',
        'suburb': 'Mount Isa',
        'state': 'QLD',
        'postcode': '4825',
        'operating_hours': {
            'monday': '8:00 AM - 5:00 PM',
            'tuesday': '8:00 AM - 5:00 PM',
            'wednesday': '8:00 AM - 5:00 PM',
            'thursday': '8:00 AM - 5:00 PM',
            'friday': '8:00 AM - 5:00 PM'
        },
        'services_offered': ['General Practice', 'Mental Health', 'Women\'s Health', 'Aboriginal Health']
    }
    
    # Configure quality assurance system
    config = {
        'reference_sources': [
            'https://www.health.qld.gov.au',
            'https://www.mountisa.qld.gov.au'
        ]
    }
    
    # Initialize QA orchestrator
    qa_orchestrator = QualityAssuranceOrchestrator(config)
    
    # Perform comprehensive validation
    print("Starting comprehensive validation...")
    validation_report = await qa_orchestrator.validate_service_comprehensive(sample_service)
    
    # Display results
    print("\n" + "="*80)
    print("VALIDATION REPORT")
    print("="*80)
    print(f"Service: {sample_service['name']}")
    print(f"Validation Time: {validation_report['validation_timestamp']}")
    print(f"Overall Quality Score: {validation_report['overall_quality']['overall_quality']:.2f}")
    print(f"Requires Manual Review: {validation_report['requires_manual_review']}")
    
    print(f"\nTier 1 Results: {len(validation_report['tier1_results'])} checks")
    for result in validation_report['tier1_results']:
        status_icon = "✓" if result['status'] == 'passed' else "✗" if result['status'] == 'failed' else "?"
        print(f"  {status_icon} {result['validation_type']}: {result['status']} (confidence: {result['confidence']:.2f})")
    
    if validation_report['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(validation_report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the validation demonstration
    asyncio.run(main())