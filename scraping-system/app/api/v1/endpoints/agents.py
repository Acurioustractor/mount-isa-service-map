"""
Agents API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import json

from app.core.database import get_async_session
from app.models.agent import AgentType, AgentStatus, AgentTask
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()


@router.get("/")
async def list_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by agent status"),
    db: AsyncSession = Depends(get_async_session)
):
    """List all agents with optional filters"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get all agents from registry
        all_agents = await redis_client.smembers("agents:registry")
        
        agents_info = []
        
        for agent_id in all_agents:
            agent_id_str = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            
            # Get agent details
            agent_data = await redis_client.hgetall(f"agent:{agent_id_str}")
            
            if not agent_data:
                continue
            
            # Convert bytes to strings
            agent_info = {}
            for key, value in agent_data.items():
                key_str = key.decode() if isinstance(key, bytes) else key
                value_str = value.decode() if isinstance(value, bytes) else value
                agent_info[key_str] = value_str
            
            # Apply filters
            if agent_type and agent_info.get('agent_type') != agent_type:
                continue
            
            if status and agent_info.get('status') != status:
                continue
            
            # Get heartbeat info
            heartbeat_data = await redis_client.get(f"heartbeat:{agent_id_str}")
            if heartbeat_data:
                try:
                    heartbeat_info = eval(heartbeat_data.decode() if isinstance(heartbeat_data, bytes) else heartbeat_data)
                    agent_info['last_heartbeat'] = heartbeat_info.get('timestamp')
                    agent_info['cpu_usage'] = heartbeat_info.get('cpu_usage', 0.0)
                    agent_info['memory_usage'] = heartbeat_info.get('memory_usage', 0.0)
                    agent_info['tasks_completed'] = heartbeat_info.get('tasks_completed', 0)
                    agent_info['tasks_failed'] = heartbeat_info.get('tasks_failed', 0)
                except:
                    pass
            
            agents_info.append(agent_info)
        
        await redis_client.close()
        
        return {
            'agents': agents_info,
            'total_count': len(agents_info)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get("/{agent_id}")
async def get_agent_details(
    agent_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get detailed information about a specific agent"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get agent details
        agent_data = await redis_client.hgetall(f"agent:{agent_id}")
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Convert bytes to strings
        agent_info = {}
        for key, value in agent_data.items():
            key_str = key.decode() if isinstance(key, bytes) else key
            value_str = value.decode() if isinstance(value, bytes) else value
            agent_info[key_str] = value_str
        
        # Get heartbeat info
        heartbeat_data = await redis_client.get(f"heartbeat:{agent_id}")
        if heartbeat_data:
            try:
                heartbeat_info = eval(heartbeat_data.decode() if isinstance(heartbeat_data, bytes) else heartbeat_data)
                agent_info['heartbeat'] = heartbeat_info
            except:
                pass
        
        # Get recent completed tasks
        completed_tasks = await redis_client.lrange(f"completed_tasks:{agent_id}", 0, 9)
        agent_info['recent_tasks'] = []
        
        for task_data in completed_tasks:
            try:
                task_info = eval(task_data.decode() if isinstance(task_data, bytes) else task_data)
                agent_info['recent_tasks'].append(task_info)
            except:
                pass
        
        await redis_client.close()
        
        return agent_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent details: {str(e)}"
        )


@router.get("/{agent_id}/status")
async def get_agent_status(
    agent_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get current status of an agent"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get heartbeat data
        heartbeat_data = await redis_client.get(f"heartbeat:{agent_id}")
        
        if not heartbeat_data:
            return {
                'agent_id': agent_id,
                'status': 'unknown',
                'message': 'No heartbeat data available'
            }
        
        try:
            heartbeat_info = eval(heartbeat_data.decode() if isinstance(heartbeat_data, bytes) else heartbeat_data)
            
            await redis_client.close()
            
            return {
                'agent_id': agent_id,
                'status': heartbeat_info.get('status', 'unknown'),
                'timestamp': heartbeat_info.get('timestamp'),
                'cpu_usage': heartbeat_info.get('cpu_usage', 0.0),
                'memory_usage': heartbeat_info.get('memory_usage', 0.0),
                'current_task': heartbeat_info.get('current_task'),
                'tasks_completed': heartbeat_info.get('tasks_completed', 0),
                'tasks_failed': heartbeat_info.get('tasks_failed', 0)
            }
            
        except:
            await redis_client.close()
            return {
                'agent_id': agent_id,
                'status': 'error',
                'message': 'Failed to parse heartbeat data'
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/{agent_id}/tasks")
async def get_agent_tasks(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session)
):
    """Get recent tasks for an agent"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get completed tasks
        completed_tasks = await redis_client.lrange(f"completed_tasks:{agent_id}", 0, limit - 1)
        
        tasks = []
        for task_data in completed_tasks:
            try:
                task_info = eval(task_data.decode() if isinstance(task_data, bytes) else task_data)
                tasks.append(task_info)
            except:
                pass
        
        await redis_client.close()
        
        return {
            'agent_id': agent_id,
            'tasks': tasks,
            'total_count': len(tasks)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent tasks: {str(e)}"
        )


@router.get("/types/{agent_type}")
async def get_agents_by_type(
    agent_type: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get all agents of a specific type"""
    try:
        # Validate agent type
        try:
            AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {agent_type}"
            )
        
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get agents of specific type
        agents_of_type = await redis_client.smembers(f"agents:type:{agent_type}")
        
        agents_info = []
        
        for agent_id in agents_of_type:
            agent_id_str = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            
            # Get agent details
            agent_data = await redis_client.hgetall(f"agent:{agent_id_str}")
            
            if agent_data:
                # Convert bytes to strings
                agent_info = {}
                for key, value in agent_data.items():
                    key_str = key.decode() if isinstance(key, bytes) else key
                    value_str = value.decode() if isinstance(value, bytes) else value
                    agent_info[key_str] = value_str
                
                # Get heartbeat info
                heartbeat_data = await redis_client.get(f"heartbeat:{agent_id_str}")
                if heartbeat_data:
                    try:
                        heartbeat_info = eval(heartbeat_data.decode() if isinstance(heartbeat_data, bytes) else heartbeat_data)
                        agent_info['last_heartbeat'] = heartbeat_info.get('timestamp')
                        agent_info['status'] = heartbeat_info.get('status', agent_info.get('status'))
                    except:
                        pass
                
                agents_info.append(agent_info)
        
        await redis_client.close()
        
        return {
            'agent_type': agent_type,
            'agents': agents_info,
            'total_count': len(agents_info)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agents by type: {str(e)}"
        )


@router.get("/stats/performance")
async def get_agent_performance_stats(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get performance statistics for agents"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Determine which agents to include
        if agent_type:
            try:
                AgentType(agent_type)
                agents = await redis_client.smembers(f"agents:type:{agent_type}")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid agent type: {agent_type}"
                )
        else:
            agents = await redis_client.smembers("agents:registry")
        
        total_stats = {
            'total_agents': 0,
            'active_agents': 0,
            'inactive_agents': 0,
            'total_tasks_completed': 0,
            'total_tasks_failed': 0,
            'average_cpu_usage': 0.0,
            'average_memory_usage': 0.0,
            'success_rate': 0.0
        }
        
        active_count = 0
        cpu_usage_sum = 0.0
        memory_usage_sum = 0.0
        cpu_memory_count = 0
        
        for agent_id in agents:
            agent_id_str = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            total_stats['total_agents'] += 1
            
            # Get heartbeat data
            heartbeat_data = await redis_client.get(f"heartbeat:{agent_id_str}")
            
            if heartbeat_data:
                try:
                    heartbeat_info = eval(heartbeat_data.decode() if isinstance(heartbeat_data, bytes) else heartbeat_data)
                    
                    if heartbeat_info.get('status') == 'active':
                        active_count += 1
                    
                    total_stats['total_tasks_completed'] += heartbeat_info.get('tasks_completed', 0)
                    total_stats['total_tasks_failed'] += heartbeat_info.get('tasks_failed', 0)
                    
                    cpu_usage = heartbeat_info.get('cpu_usage', 0.0)
                    memory_usage = heartbeat_info.get('memory_usage', 0.0)
                    
                    if cpu_usage > 0 or memory_usage > 0:
                        cpu_usage_sum += cpu_usage
                        memory_usage_sum += memory_usage
                        cpu_memory_count += 1
                    
                except:
                    pass
        
        total_stats['active_agents'] = active_count
        total_stats['inactive_agents'] = total_stats['total_agents'] - active_count
        
        if cpu_memory_count > 0:
            total_stats['average_cpu_usage'] = cpu_usage_sum / cpu_memory_count
            total_stats['average_memory_usage'] = memory_usage_sum / cpu_memory_count
        
        total_tasks = total_stats['total_tasks_completed'] + total_stats['total_tasks_failed']
        if total_tasks > 0:
            total_stats['success_rate'] = total_stats['total_tasks_completed'] / total_tasks
        
        await redis_client.close()
        
        return total_stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance stats: {str(e)}"
        )


@router.get("/queue/status")
async def get_agent_queue_status(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get current agent queue status"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        queue_status = {}
        
        if agent_type:
            try:
                AgentType(agent_type)
                queue_length = await redis_client.llen(f"tasks:{agent_type}")
                queue_status[agent_type] = queue_length
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid agent type: {agent_type}"
                )
        else:
            # Get all agent types
            for atype in AgentType:
                queue_length = await redis_client.llen(f"tasks:{atype.value}")
                queue_status[atype.value] = queue_length
        
        await redis_client.close()
        
        total_queued = sum(queue_status.values())
        
        return {
            'total_queued_tasks': total_queued,
            'queue_by_type': queue_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue status: {str(e)}"
        )


@router.post("/types/{agent_type}/start")
async def start_agent_type(
    agent_type: str,
    count: int = Query(1, ge=1, le=5, description="Number of agents to start"),
    db: AsyncSession = Depends(get_async_session)
):
    """Start new agents of specified type"""
    try:
        # Validate agent type
        try:
            AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {agent_type}"
            )
        
        # In a real implementation, this would start actual agent processes
        # For now, we'll return a placeholder response
        
        return {
            'message': f'Request to start {count} {agent_type} agent(s) received',
            'agent_type': agent_type,
            'count': count,
            'note': 'Agent starting is not implemented in this demo'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start agents: {str(e)}"
        )


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Stop a specific agent"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Check if agent exists
        agent_data = await redis_client.hgetall(f"agent:{agent_id}")
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # In a real implementation, this would send a stop signal to the agent
        # For now, we'll just return a placeholder response
        
        await redis_client.close()
        
        return {
            'message': f'Stop request sent to agent {agent_id}',
            'agent_id': agent_id,
            'note': 'Agent stopping is not implemented in this demo'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop agent: {str(e)}"
        )


@router.get("/health/check")
async def check_agent_system_health(
    db: AsyncSession = Depends(get_async_session)
):
    """Check overall health of the agent system"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Get all agents
        all_agents = await redis_client.smembers("agents:registry")
        total_agents = len(all_agents)
        
        # Count active agents
        active_agents = 0
        for agent_id in all_agents:
            agent_id_str = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            heartbeat_data = await redis_client.get(f"heartbeat:{agent_id_str}")
            
            if heartbeat_data:
                try:
                    heartbeat_info = eval(heartbeat_data.decode() if isinstance(heartbeat_data, bytes) else heartbeat_data)
                    if heartbeat_info.get('status') == 'active':
                        active_agents += 1
                except:
                    pass
        
        # Get queue lengths
        total_queued = 0
        for atype in AgentType:
            queue_length = await redis_client.llen(f"tasks:{atype.value}")
            total_queued += queue_length
        
        await redis_client.close()
        
        # Determine health status
        health_status = "healthy"
        if active_agents == 0:
            health_status = "critical"
        elif active_agents < total_agents * 0.5:
            health_status = "degraded"
        elif total_queued > 100:
            health_status = "overloaded"
        
        return {
            'status': health_status,
            'total_agents': total_agents,
            'active_agents': active_agents,
            'inactive_agents': total_agents - active_agents,
            'total_queued_tasks': total_queued,
            'system_operational': active_agents > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check system health: {str(e)}"
        )