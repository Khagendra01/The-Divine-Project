from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    preferences: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: str
    priority: str = "medium"


class TaskCreate(TaskBase):
    user_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class Task(TaskBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SubtaskBase(BaseModel):
    title: str
    description: str
    agent_type: str
    order_index: int = 0


class SubtaskCreate(SubtaskBase):
    task_id: int


class Subtask(SubtaskBase):
    id: int
    task_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentExecutionBase(BaseModel):
    agent_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None


class AgentExecutionCreate(AgentExecutionBase):
    task_id: int
    subtask_id: Optional[int] = None


class AgentExecution(AgentExecutionBase):
    id: int
    task_id: int
    subtask_id: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MemoryBase(BaseModel):
    memory_type: str
    key: str
    value: Dict[str, Any]
    importance: int = 1


class MemoryCreate(MemoryBase):
    user_id: int


class Memory(MemoryBase):
    id: int
    user_id: int
    created_at: datetime
    last_accessed: datetime
    
    class Config:
        from_attributes = True


class TaskRequest(BaseModel):
    user_id: int
    request: str
    context: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    task_id: int
    status: str
    message: str
    estimated_duration: Optional[int] = None


class TaskStatus(BaseModel):
    task_id: int
    status: str
    progress: float
    current_step: Optional[str] = None
    subtasks: List[Subtask]
    executions: List[AgentExecution]


class AgentMessage(BaseModel):
    agent_type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now() 