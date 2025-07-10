import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Task, Subtask, User, AgentExecution, Memory
from app.schemas import TaskRequest, TaskResponse, TaskStatus
from app.agents.controller import ControllerAgent
from app.database import get_db


class TaskService:
    """Service for managing tasks and orchestrating agent workflows"""
    
    def __init__(self, db: Session):
        self.db = db
        self.controller_agent = ControllerAgent()
        self.controller_agent.set_db(db)
    
    async def create_task(self, task_request: TaskRequest) -> TaskResponse:
        """Create a new task and start the workflow"""
        try:
            # Create the task
            task = Task(
                user_id=task_request.user_id,
                title=task_request.request,
                description=task_request.request,
                status="pending"
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            # Start the controller agent workflow
            input_data = {
                "request": task_request.request,
                "context": task_request.context or {},
                "user_id": task_request.user_id
            }
            
            # Execute the workflow asynchronously
            asyncio.create_task(self._execute_workflow(task.id, input_data))
            
            return TaskResponse(
                task_id=task.id,
                status="started",
                message="Task created and workflow started",
                estimated_duration=300  # 5 minutes default
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=0,
                status="error",
                message=f"Failed to create task: {str(e)}"
            )
    
    async def _execute_workflow(self, task_id: int, input_data: Dict[str, Any]):
        """Execute the complete workflow for a task"""
        try:
            result = await self.controller_agent.execute(task_id, input_data)
            print(f"Workflow completed for task {task_id}: {result}")
        except Exception as e:
            print(f"Workflow failed for task {task_id}: {str(e)}")
    
    async def get_task_status(self, task_id: int) -> TaskStatus:
        """Get the current status of a task"""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return TaskStatus(
                    task_id=task_id,
                    status="not_found",
                    progress=0,
                    subtasks=[],
                    executions=[]
                )
            
            # Get subtasks
            subtasks = self.db.query(Subtask).filter(
                Subtask.task_id == task_id
            ).order_by(Subtask.order_index).all()
            
            # Get executions
            executions = self.db.query(AgentExecution).filter(
                AgentExecution.task_id == task_id
            ).order_by(AgentExecution.started_at).all()
            
            # Calculate progress
            total_subtasks = len(subtasks)
            completed_subtasks = sum(1 for st in subtasks if st.status == "completed")
            progress = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0
            
            # Get current step
            current_step = None
            for subtask in subtasks:
                if subtask.status == "executing":
                    current_step = subtask.title
                    break
                elif subtask.status == "pending":
                    current_step = f"Next: {subtask.title}"
                    break
            
            return TaskStatus(
                task_id=task_id,
                status=task.status,
                progress=progress,
                current_step=current_step,
                subtasks=subtasks,
                executions=executions
            )
            
        except Exception as e:
            return TaskStatus(
                task_id=task_id,
                status="error",
                progress=0,
                current_step=f"Error: {str(e)}",
                subtasks=[],
                executions=[]
            )
    
    async def get_task_progress(self, task_id: int) -> Dict[str, Any]:
        """Get detailed progress information for a task"""
        try:
            return await self.controller_agent.get_task_progress(task_id)
        except Exception as e:
            return {"error": f"Failed to get progress: {str(e)}"}
    
    async def get_user_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a user"""
        try:
            tasks = self.db.query(Task).filter(
                Task.user_id == user_id
            ).order_by(Task.created_at.desc()).all()
            
            task_list = []
            for task in tasks:
                # Get subtask count
                subtask_count = self.db.query(Subtask).filter(
                    Subtask.task_id == task.id
                ).count()
                
                # Get completed subtask count
                completed_subtasks = self.db.query(Subtask).filter(
                    Subtask.task_id == task.id,
                    Subtask.status == "completed"
                ).count()
                
                task_list.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "subtask_count": subtask_count,
                    "completed_subtasks": completed_subtasks,
                    "progress": (completed_subtasks / subtask_count * 100) if subtask_count > 0 else 0
                })
            
            return task_list
            
        except Exception as e:
            return []
    
    async def create_user(self, username: str, email: str) -> Dict[str, Any]:
        """Create a new user"""
        try:
            user = User(
                username=username,
                email=email,
                preferences={}
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to create user: {str(e)}"}
    
    async def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            user.preferences = preferences
            self.db.commit()
            
            return {
                "id": user.id,
                "preferences": user.preferences
            }
            
        except Exception as e:
            return {"error": f"Failed to update preferences: {str(e)}"}
    
    async def store_memory(self, user_id: int, memory_type: str, key: str, value: Dict[str, Any], importance: int = 5) -> Dict[str, Any]:
        """Store a new memory"""
        try:
            memory = Memory(
                user_id=user_id,
                memory_type=memory_type,
                key=key,
                value=value,
                importance=importance
            )
            self.db.add(memory)
            self.db.commit()
            self.db.refresh(memory)
            
            return {
                "id": memory.id,
                "type": memory.memory_type,
                "key": memory.key,
                "value": memory.value,
                "importance": memory.importance
            }
            
        except Exception as e:
            return {"error": f"Failed to store memory: {str(e)}"}
    
    async def get_user_memories(self, user_id: int, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get memories for a user"""
        try:
            query = self.db.query(Memory).filter(Memory.user_id == user_id)
            
            if memory_type:
                query = query.filter(Memory.memory_type == memory_type)
            
            memories = query.order_by(Memory.importance.desc(), Memory.last_accessed.desc()).all()
            
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "id": memory.id,
                    "type": memory.memory_type,
                    "key": memory.key,
                    "value": memory.value,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                    "last_accessed": memory.last_accessed.isoformat()
                })
            
            return memory_list
            
        except Exception as e:
            return [] 