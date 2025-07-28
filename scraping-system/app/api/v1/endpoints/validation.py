"""
Validation API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import json

from app.core.database import get_async_session
from app.models.validation import (
    ValidationRequest, ValidationResponse, ValidationSummary,
    ValidationResult, ValidationBatchRequest, ValidationBatchResponse
)
from app.services.validation_service import ValidationService
from app.agents.validation import ValidationAgent
from app.agents.base import create_agent_task, submit_task_to_queue
from app.models.agent import AgentType
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()


@router.post("/service", response_model=ValidationResponse)
async def validate_service(
    validation_request: ValidationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Validate a service using Tier 1 automated validation"""
    validation_service = ValidationService(db)
    
    try:
        # Submit validation task to queue for processing
        redis_client = redis.from_url(settings.REDIS_URL)
        
        task = await create_agent_task(
            task_type="validate_service",
            payload={
                "service_data": validation_request.service_data,
                "validation_options": validation_request.options.__dict__ if validation_request.options else {}
            }
        )
        
        await submit_task_to_queue(AgentType.VALIDATION, task, redis_client)
        await redis_client.close()
        
        # Return immediate response with task ID
        return ValidationResponse(
            task_id=task.task_id,
            status="queued",
            message="Validation task submitted for processing"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit validation task: {str(e)}"
        )


@router.get("/service/{task_id}", response_model=ValidationResponse)
async def get_validation_result(
    task_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get validation result by task ID"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Check if task result exists
        result_data = await redis_client.get(f"task_result:{task_id}")
        
        if not result_data:
            return ValidationResponse(
                task_id=task_id,
                status="processing",
                message="Validation still in progress"
            )
        
        # Parse result data
        result_dict = json.loads(result_data.decode() if isinstance(result_data, bytes) else result_data)
        
        await redis_client.close()
        
        if result_dict['status'] == 'completed':
            validation_summary = result_dict['result']['validation_summary']
            
            return ValidationResponse(
                task_id=task_id,
                status="completed",
                message="Validation completed successfully",
                summary=ValidationSummary(**validation_summary),
                processing_time=result_dict['result']['processing_time']
            )
        else:
            return ValidationResponse(
                task_id=task_id,
                status="failed",
                message=f"Validation failed: {result_dict.get('error_message', 'Unknown error')}",
                processing_time=result_dict['processing_time']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve validation result: {str(e)}"
        )


@router.post("/batch", response_model=ValidationBatchResponse)
async def validate_service_batch(
    batch_request: ValidationBatchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Validate multiple services in batch"""
    validation_service = ValidationService(db)
    
    if len(batch_request.services) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size cannot exceed 100 services"
        )
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        task_ids = []
        
        # Submit each service for validation
        for service_data in batch_request.services:
            task = await create_agent_task(
                task_type="validate_service",
                payload={
                    "service_data": service_data,
                    "validation_options": batch_request.options.__dict__ if batch_request.options else {}
                }
            )
            
            await submit_task_to_queue(AgentType.VALIDATION, task, redis_client)
            task_ids.append(task.task_id)
        
        await redis_client.close()
        
        return ValidationBatchResponse(
            batch_id=f"batch_{len(task_ids)}_{task_ids[0][:8]}",
            task_ids=task_ids,
            status="queued",
            total_services=len(batch_request.services)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit batch validation: {str(e)}"
        )


@router.get("/batch/{batch_id}/status")
async def get_batch_validation_status(
    batch_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get status of batch validation"""
    try:
        # Extract task IDs from batch_id or get from database
        # For simplicity, we'll require the client to track task IDs
        # In a full implementation, this would be stored in database
        
        return {
            "message": "Use individual task IDs to check validation status",
            "batch_id": batch_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.post("/contact", response_model=ValidationResponse)
async def validate_contact_info(
    contact_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Validate contact information separately"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        task = await create_agent_task(
            task_type="validate_contact",
            payload={"contact_data": contact_data}
        )
        
        await submit_task_to_queue(AgentType.VALIDATION, task, redis_client)
        await redis_client.close()
        
        return ValidationResponse(
            task_id=task.task_id,
            status="queued",
            message="Contact validation task submitted"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate contact info: {str(e)}"
        )


@router.post("/location", response_model=ValidationResponse)
async def validate_location_info(
    location_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Validate location information separately"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        task = await create_agent_task(
            task_type="validate_location",
            payload={"location_data": location_data}
        )
        
        await submit_task_to_queue(AgentType.VALIDATION, task, redis_client)
        await redis_client.close()
        
        return ValidationResponse(
            task_id=task.task_id,
            status="queued",
            message="Location validation task submitted"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate location info: {str(e)}"
        )


@router.post("/content", response_model=ValidationResponse)
async def validate_content_quality(
    content_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Validate content quality separately"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        task = await create_agent_task(
            task_type="validate_content",
            payload={"content_data": content_data}
        )
        
        await submit_task_to_queue(AgentType.VALIDATION, task, redis_client)
        await redis_client.close()
        
        return ValidationResponse(
            task_id=task.task_id,
            status="queued",
            message="Content validation task submitted"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate content: {str(e)}"
        )


@router.get("/stats/performance")
async def get_validation_performance():
    """Get validation system performance statistics"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get all validation agents
        validation_agents = await redis_client.smembers("agents:type:validation")
        
        total_stats = {
            'services_validated': 0,
            'total_checks_performed': 0,
            'critical_failures': 0,
            'avg_validation_time': 0.0,
            'active_agents': len(validation_agents)
        }
        
        # Aggregate stats from all agents (simplified implementation)
        # In a real system, this would query actual agent statistics
        
        await redis_client.close()
        
        return total_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance stats: {str(e)}"
        )


@router.get("/patterns/list")
async def get_validation_patterns():
    """Get list of available validation patterns"""
    # Create a temporary validation agent to get patterns
    temp_agent = ValidationAgent("temp", {})
    
    patterns_info = {
        'phone_patterns': [
            {
                'name': 'Australian Landline',
                'pattern': temp_agent.patterns['phone']['australian_landline'],
                'description': 'Standard Australian landline format'
            },
            {
                'name': 'Australian Mobile',
                'pattern': temp_agent.patterns['phone']['australian_mobile'],
                'description': 'Australian mobile phone format'
            }
        ],
        'email_patterns': [
            {
                'name': 'Standard Email',
                'pattern': temp_agent.patterns['email']['standard'],
                'description': 'Standard email address format'
            }
        ],
        'address_patterns': [
            {
                'name': 'Australian Street',
                'pattern': temp_agent.patterns['address']['australian_street'],
                'description': 'Australian street address format'
            }
        ]
    }
    
    return patterns_info


@router.post("/test/pattern")
async def test_validation_pattern(
    pattern_test: Dict[str, Any]
):
    """Test a value against validation patterns"""
    pattern_name = pattern_test.get('pattern_name')
    test_value = pattern_test.get('value')
    
    if not pattern_name or not test_value:
        raise HTTPException(
            status_code=400,
            detail="Both pattern_name and value are required"
        )
    
    # Create temporary validation agent
    temp_agent = ValidationAgent("temp", {})
    
    try:
        if pattern_name == 'phone':
            result = await temp_agent._validate_phone_number(test_value)
        elif pattern_name == 'email':
            result = await temp_agent._validate_email_address(test_value)
        elif pattern_name == 'website':
            result = await temp_agent._validate_website_url(test_value)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown pattern type: {pattern_name}"
            )
        
        return {
            'pattern_name': pattern_name,
            'test_value': test_value,
            'validation_result': result.__dict__
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern test failed: {str(e)}"
        )