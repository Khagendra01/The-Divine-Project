from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import AgentExecution, Task, Subtask
from app.schemas import AgentMessage


class BaseAgent(ABC):
    """Base class for all MiniMind agents"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.db: Optional[Session] = None
    
    def set_db(self, db: Session):
        """Set database session for the agent"""
        self.db = db
    
    @abstractmethod
    async def execute(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int] = None) -> Dict[str, Any]:
        """Execute the agent's main logic"""
        pass
    
    def log_execution(self, task_id: int, input_data: Dict[str, Any], output_data: Dict[str, Any], 
                     status: str = "completed", error_message: Optional[str] = None, 
                     subtask_id: Optional[int] = None) -> AgentExecution:
        """Log agent execution to database"""
        if not self.db:
            raise ValueError("Database session not set")
        
        execution = AgentExecution(
            task_id=task_id,
            subtask_id=subtask_id,
            agent_type=self.agent_type,
            input_data=input_data,
            output_data=output_data,
            status=status,
            error_message=error_message,
            started_at=datetime.now(),
            completed_at=datetime.now() if status in ["completed", "failed"] else None
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def create_message(self, message: str, data: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Create an agent message for real-time updates"""
        return AgentMessage(
            agent_type=self.agent_type,
            message=message,
            data=data,
            timestamp=datetime.now()
        )
    
    def update_task_status(self, task_id: int, status: str):
        """Update task status in database"""
        if not self.db:
            return
        
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            task.updated_at = datetime.now()
            self.db.commit()
    
    def update_subtask_status(self, subtask_id: int, status: str):
        """Update subtask status in database"""
        if not self.db:
            return
        
        subtask = self.db.query(Subtask).filter(Subtask.id == subtask_id).first()
        if subtask:
            subtask.status = status
            if status == "completed":
                subtask.completed_at = datetime.now()
            self.db.commit() 