"""
Base agent implementation for the intelligent scraping system
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import aiohttp
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import AgentLogger
from app.core.exceptions import AgentException
from app.models.agent import AgentType, AgentStatus, AgentTask, AgentTaskResult


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_heartbeat: Optional[datetime] = None


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class BaseAgent(ABC):
    """Base class for all intelligent agents"""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        config: Optional[Dict[str, Any]] = None,
        db_session: Optional[AsyncSession] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.db_session = db_session
        
        # Initialize logging
        self.logger = AgentLogger(agent_id, agent_type.value)
        
        # Agent state
        self.status = AgentStatus.INACTIVE
        self.is_running = False
        self.current_task: Optional[AgentTask] = None
        
        # Performance tracking
        self.metrics = AgentMetrics()
        
        # Async resources
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Task management
        self.task_queue = asyncio.Queue()
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 1)
        self.request_delay = config.get('request_delay', settings.REQUEST_DELAY)
        
        # Initialize components
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize agent resources"""
        try:
            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
            self.http_session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': settings.USER_AGENT}
            )
            
            # Initialize Redis connection
            self.redis_client = redis.from_url(settings.REDIS_URL)
            
            # Register agent in Redis
            await self._register_agent()
            
            self.logger.info("Agent initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize agent", error=e)
            raise AgentException(
                f"Agent initialization failed: {str(e)}",
                agent_id=self.agent_id,
                agent_type=self.agent_type.value
            )
    
    async def _register_agent(self):
        """Register agent in the system"""
        agent_data = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'status': self.status.value,
            'config': self.config,
            'registered_at': datetime.utcnow().isoformat(),
            'pid': os.getpid() if 'os' in globals() else 0
        }
        
        await self.redis_client.hset(
            f"agent:{self.agent_id}",
            mapping=agent_data
        )
        
        # Add to agent registry
        await self.redis_client.sadd("agents:registry", self.agent_id)
        await self.redis_client.sadd(f"agents:type:{self.agent_type.value}", self.agent_id)
    
    async def start(self):
        """Start the agent"""
        if self.is_running:
            self.logger.warning("Agent is already running")
            return
        
        self.is_running = True
        self.status = AgentStatus.ACTIVE
        
        self.logger.info("Starting agent")
        
        # Start main tasks
        tasks = [
            asyncio.create_task(self._main_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._metrics_collection_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error("Agent execution failed", error=e)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the agent"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping agent")
        self.is_running = False
        self.status = AgentStatus.INACTIVE
        
        # Clean up resources
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up agent resources"""
        try:
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
            
            # Update agent status in Redis
            if self.redis_client:
                await self.redis_client.hset(
                    f"agent:{self.agent_id}",
                    mapping={
                        'status': self.status.value,
                        'stopped_at': datetime.utcnow().isoformat()
                    }
                )
                await self.redis_client.close()
            
            # Close database session
            if self.db_session:
                await self.db_session.close()
            
            self.logger.info("Agent cleanup completed")
            
        except Exception as e:
            self.logger.error("Error during agent cleanup", error=e)
    
    async def _main_loop(self):
        """Main agent execution loop"""
        while self.is_running:
            try:
                # Get next task
                task = await self._get_next_task()
                
                if task:
                    # Execute task
                    result = await self._execute_task_with_tracking(task)
                    
                    # Report result
                    await self._report_task_result(task, result)
                else:
                    # No tasks available, wait
                    await asyncio.sleep(self.config.get('idle_wait', 10))
                
            except Exception as e:
                self.logger.error("Error in main loop", error=e)
                await asyncio.sleep(self.config.get('error_wait', 30))
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        heartbeat_interval = self.config.get('heartbeat_interval', 60)
        
        while self.is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(heartbeat_interval)
            except Exception as e:
                self.logger.error("Error in heartbeat loop", error=e)
                await asyncio.sleep(heartbeat_interval)
    
    async def _metrics_collection_loop(self):
        """Collect and update performance metrics"""
        metrics_interval = self.config.get('metrics_interval', 30)
        
        while self.is_running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(metrics_interval)
            except Exception as e:
                self.logger.error("Error in metrics collection", error=e)
                await asyncio.sleep(metrics_interval)
    
    async def _send_heartbeat(self):
        """Send heartbeat to coordination system"""
        heartbeat_data = {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_usage': self.metrics.cpu_usage,
            'memory_usage': self.metrics.memory_usage,
            'tasks_completed': self.metrics.tasks_completed,
            'tasks_failed': self.metrics.tasks_failed,
            'current_task': self.current_task.task_id if self.current_task else None
        }
        
        # Store in Redis with expiration
        await self.redis_client.setex(
            f"heartbeat:{self.agent_id}",
            120,  # 2 minutes expiration
            str(heartbeat_data)
        )
        
        self.metrics.last_heartbeat = datetime.utcnow()
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        try:
            import psutil
            process = psutil.Process()
            
            self.metrics.cpu_usage = process.cpu_percent()
            self.metrics.memory_usage = process.memory_percent()
            
        except ImportError:
            # psutil not available, use basic metrics
            self.metrics.cpu_usage = 0.0
            self.metrics.memory_usage = 0.0
    
    async def _get_next_task(self) -> Optional[AgentTask]:
        """Get next task from the task queue"""
        try:
            # Check local queue first
            if not self.task_queue.empty():
                return await self.task_queue.get()
            
            # Check Redis task queue for this agent type
            task_data = await self.redis_client.lpop(f"tasks:{self.agent_type.value}")
            
            if task_data:
                task_dict = eval(task_data.decode()) if isinstance(task_data, bytes) else eval(task_data)
                return AgentTask(**task_dict)
            
            return None
            
        except Exception as e:
            self.logger.error("Error getting next task", error=e)
            return None
    
    async def _execute_task_with_tracking(self, task: AgentTask) -> AgentTaskResult:
        """Execute task with performance tracking"""
        start_time = datetime.utcnow()
        self.current_task = task
        
        try:
            self.logger.info(f"Starting task {task.task_id}", task_type=task.task_type)
            
            # Execute the task
            result = await self.execute_task(task)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            self.metrics.tasks_completed += 1
            self.metrics.total_processing_time += processing_time
            
            # Create result
            task_result = AgentTaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=result,
                processing_time=processing_time,
                completed_at=datetime.utcnow()
            )
            
            self.logger.info(
                f"Task {task.task_id} completed successfully",
                processing_time=processing_time
            )
            
            return task_result
            
        except Exception as e:
            # Calculate processing time even for failed tasks
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            self.metrics.tasks_failed += 1
            
            # Create error result
            task_result = AgentTaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="failed",
                error_message=str(e),
                processing_time=processing_time,
                completed_at=datetime.utcnow()
            )
            
            self.logger.error(
                f"Task {task.task_id} failed",
                error=e,
                processing_time=processing_time
            )
            
            return task_result
            
        finally:
            self.current_task = None
    
    async def _report_task_result(self, task: AgentTask, result: AgentTaskResult):
        """Report task result to the coordination system"""
        try:
            # Store result in Redis
            await self.redis_client.setex(
                f"task_result:{task.task_id}",
                3600,  # 1 hour expiration
                str(result.dict())
            )
            
            # Add to completed tasks list
            await self.redis_client.lpush(
                f"completed_tasks:{self.agent_id}",
                str(result.dict())
            )
            
            # Trim completed tasks list to last 100
            await self.redis_client.ltrim(f"completed_tasks:{self.agent_id}", 0, 99)
            
        except Exception as e:
            self.logger.error("Error reporting task result", error=e)
    
    async def add_task(self, task: AgentTask):
        """Add task to the agent's queue"""
        await self.task_queue.put(task)
        self.logger.debug(f"Task {task.task_id} added to queue")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'status': self.status.value,
            'is_running': self.is_running,
            'current_task': self.current_task.task_id if self.current_task else None,
            'metrics': {
                'tasks_completed': self.metrics.tasks_completed,
                'tasks_failed': self.metrics.tasks_failed,
                'success_rate': (
                    self.metrics.tasks_completed / 
                    max(1, self.metrics.tasks_completed + self.metrics.tasks_failed)
                ),
                'avg_processing_time': (
                    self.metrics.total_processing_time / 
                    max(1, self.metrics.tasks_completed)
                ),
                'cpu_usage': self.metrics.cpu_usage,
                'memory_usage': self.metrics.memory_usage,
                'last_heartbeat': self.metrics.last_heartbeat.isoformat() if self.metrics.last_heartbeat else None
            }
        }
    
    @abstractmethod
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a specific task (to be implemented by subclasses)"""
        pass


# Utility functions for agent management
async def create_agent_task(
    task_type: str,
    payload: Dict[str, Any],
    priority: float = 0.5,
    max_attempts: int = 3
) -> AgentTask:
    """Create a new agent task"""
    return AgentTask(
        task_id=str(uuid.uuid4()),
        task_type=task_type,
        priority=priority,
        payload=payload,
        max_attempts=max_attempts,
        scheduled_for=datetime.utcnow()
    )


async def submit_task_to_queue(
    agent_type: AgentType,
    task: AgentTask,
    redis_client: redis.Redis
):
    """Submit task to agent queue"""
    await redis_client.rpush(
        f"tasks:{agent_type.value}",
        str(task.dict())
    )