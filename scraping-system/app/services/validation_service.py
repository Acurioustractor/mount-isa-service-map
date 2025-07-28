"""
Validation service for business logic
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import uuid

from app.models.validation import (
    ValidationRequest, ValidationResponse, ValidationSummary,
    ValidationResult, ValidationReport, ValidationHistory,
    ValidationMetrics, ValidationQueue
)
from app.core.database import ValidationResultModel, ServiceModel
from app.core.exceptions import ValidationException


class ValidationService:
    """Service for managing validation operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_validation_request(
        self, 
        service_data: Dict[str, Any], 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new validation request"""
        validation_id = str(uuid.uuid4())
        
        # Store validation request in database
        # This would typically create a ValidationRequest record
        # For now, we'll return the validation ID
        
        return validation_id
    
    async def get_validation_result(self, validation_id: str) -> Optional[ValidationResponse]:
        """Get validation result by ID"""
        try:
            # Query validation result from database
            stmt = select(ValidationResultModel).where(
                ValidationResultModel.validation_id == validation_id
            )
            result = await self.db.execute(stmt)
            validation_record = result.scalar_one_or_none()
            
            if not validation_record:
                return None
            
            # Convert database record to response model
            return ValidationResponse(
                task_id=validation_record.validation_id,
                status=validation_record.status,
                message=validation_record.message or "Validation completed",
                summary=ValidationSummary(**validation_record.summary) if validation_record.summary else None,
                processing_time=validation_record.processing_time
            )
            
        except Exception as e:
            raise ValidationException(
                f"Failed to retrieve validation result: {str(e)}",
                validation_id=validation_id
            )
    
    async def store_validation_result(
        self, 
        validation_id: str, 
        summary: ValidationSummary,
        detailed_results: List[ValidationResult]
    ) -> bool:
        """Store validation results in database"""
        try:
            # Create validation record
            validation_record = ValidationResultModel(
                validation_id=validation_id,
                service_id=summary.service_id,
                overall_score=summary.overall_score,
                total_checks=summary.total_checks,
                passed_checks=summary.passed,
                failed_checks=summary.failed,
                warning_checks=summary.warnings,
                critical_issues_count=len(summary.critical_issues),
                summary=summary.dict(),
                detailed_results=[result.dict() for result in detailed_results],
                validated_at=datetime.utcnow(),
                status="completed"
            )
            
            self.db.add(validation_record)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValidationException(
                f"Failed to store validation result: {str(e)}",
                validation_id=validation_id
            )
    
    async def get_service_validation_history(
        self, 
        service_id: str, 
        limit: int = 10
    ) -> List[ValidationHistory]:
        """Get validation history for a service"""
        try:
            stmt = select(ValidationResultModel).where(
                ValidationResultModel.service_id == service_id
            ).order_by(desc(ValidationResultModel.validated_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            history = []
            for record in records:
                history.append(ValidationHistory(
                    validation_id=record.validation_id,
                    service_id=record.service_id,
                    validation_date=record.validated_at,
                    overall_score=record.overall_score,
                    critical_issues_count=record.critical_issues_count,
                    status=record.status,
                    agent_id=record.validator_agent_id or "unknown"
                ))
            
            return history
            
        except Exception as e:
            raise ValidationException(
                f"Failed to retrieve validation history: {str(e)}",
                service_id=service_id
            )
    
    async def get_validation_metrics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ValidationMetrics:
        """Get validation system metrics"""
        try:
            # Base query
            base_query = select(ValidationResultModel)
            
            # Add date filters if provided
            if start_date:
                base_query = base_query.where(ValidationResultModel.validated_at >= start_date)
            if end_date:
                base_query = base_query.where(ValidationResultModel.validated_at <= end_date)
            
            result = await self.db.execute(base_query)
            records = result.scalars().all()
            
            # Calculate metrics
            total_validations = len(records)
            successful_validations = len([r for r in records if r.status == "completed"])
            failed_validations = len([r for r in records if r.status == "failed"])
            
            # Calculate average processing time
            processing_times = [r.processing_time for r in records if r.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            
            # Count critical failures
            critical_failures = len([r for r in records if r.critical_issues_count > 0])
            
            # Calculate accuracy (services with score > 0.7)
            high_quality_validations = len([r for r in records if r.overall_score > 0.7])
            validation_accuracy = (high_quality_validations / total_validations * 100) if total_validations > 0 else 0.0
            
            return ValidationMetrics(
                total_validations=total_validations,
                successful_validations=successful_validations,
                failed_validations=failed_validations,
                average_processing_time=avg_processing_time,
                critical_failures=critical_failures,
                validation_accuracy=validation_accuracy
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to calculate validation metrics: {str(e)}")
    
    async def get_failed_validations(
        self, 
        limit: int = 50
    ) -> List[ValidationHistory]:
        """Get services that failed validation"""
        try:
            stmt = select(ValidationResultModel).where(
                and_(
                    ValidationResultModel.status == "completed",
                    ValidationResultModel.overall_score < 0.5
                )
            ).order_by(desc(ValidationResultModel.validated_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            failed_validations = []
            for record in records:
                failed_validations.append(ValidationHistory(
                    validation_id=record.validation_id,
                    service_id=record.service_id,
                    validation_date=record.validated_at,
                    overall_score=record.overall_score,
                    critical_issues_count=record.critical_issues_count,
                    status="failed_quality",
                    agent_id=record.validator_agent_id or "unknown"
                ))
            
            return failed_validations
            
        except Exception as e:
            raise ValidationException(f"Failed to retrieve failed validations: {str(e)}")
    
    async def get_services_needing_validation(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get services that need validation"""
        try:
            # Find services without recent validation
            stmt = """
            SELECT s.id, s.name, s.source_url, s.created_at
            FROM services s
            LEFT JOIN validation_results v ON s.id = v.service_id
            WHERE v.service_id IS NULL 
               OR v.validated_at < NOW() - INTERVAL '30 days'
            ORDER BY s.created_at DESC
            LIMIT :limit
            """
            
            result = await self.db.execute(stmt, {"limit": limit})
            records = result.fetchall()
            
            services_needing_validation = []
            for record in records:
                services_needing_validation.append({
                    "service_id": record.id,
                    "name": record.name,
                    "source_url": record.source_url,
                    "created_at": record.created_at
                })
            
            return services_needing_validation
            
        except Exception as e:
            raise ValidationException(f"Failed to find services needing validation: {str(e)}")
    
    async def mark_service_validated(
        self, 
        service_id: str, 
        validation_score: float
    ) -> bool:
        """Mark a service as validated"""
        try:
            # Update service validation status
            stmt = select(ServiceModel).where(ServiceModel.id == service_id)
            result = await self.db.execute(stmt)
            service = result.scalar_one_or_none()
            
            if not service:
                return False
            
            service.validation_score = validation_score
            service.last_validated = datetime.utcnow()
            service.is_validated = validation_score > 0.7
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValidationException(
                f"Failed to mark service as validated: {str(e)}",
                service_id=service_id
            )
    
    async def create_validation_report(
        self, 
        validation_id: str
    ) -> Optional[ValidationReport]:
        """Create a comprehensive validation report"""
        try:
            # Get validation record
            stmt = select(ValidationResultModel).where(
                ValidationResultModel.validation_id == validation_id
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if not record:
                return None
            
            # Create comprehensive report
            summary = ValidationSummary(**record.summary)
            detailed_results = [ValidationResult(**result) for result in record.detailed_results]
            
            report = ValidationReport(
                report_id=str(uuid.uuid4()),
                service_id=record.service_id,
                validation_date=record.validated_at,
                validator_agent_id=record.validator_agent_id or "unknown",
                summary=summary,
                detailed_results=detailed_results,
                recommendations=summary.recommendations,
                follow_up_required=record.overall_score < 0.5 or record.critical_issues_count > 0,
                estimated_accuracy=min(record.overall_score + 0.1, 1.0)
            )
            
            return report
            
        except Exception as e:
            raise ValidationException(
                f"Failed to create validation report: {str(e)}",
                validation_id=validation_id
            )
    
    async def queue_validation_task(
        self, 
        service_data: Dict[str, Any], 
        priority: int = 5
    ) -> str:
        """Queue a validation task"""
        queue_id = str(uuid.uuid4())
        
        # In a real implementation, this would add to a proper queue system
        # For now, we'll return the queue ID
        
        return queue_id
    
    async def get_validation_queue_status(self) -> Dict[str, Any]:
        """Get current validation queue status"""
        # In a real implementation, this would query the actual queue
        return {
            "pending_validations": 0,
            "active_validations": 0,
            "completed_today": 0,
            "average_wait_time": 0.0
        }
    
    async def update_service_validation_status(
        self, 
        service_id: str, 
        is_valid: bool, 
        validation_notes: Optional[str] = None
    ) -> bool:
        """Update service validation status"""
        try:
            stmt = select(ServiceModel).where(ServiceModel.id == service_id)
            result = await self.db.execute(stmt)
            service = result.scalar_one_or_none()
            
            if not service:
                return False
            
            service.is_validated = is_valid
            service.validation_notes = validation_notes
            service.last_validated = datetime.utcnow()
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise ValidationException(
                f"Failed to update service validation status: {str(e)}",
                service_id=service_id
            )