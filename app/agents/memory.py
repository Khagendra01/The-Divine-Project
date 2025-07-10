import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.models import Memory, User, Task, AgentExecution


class MemoryAgent(BaseAgent):
    """Agent responsible for managing context and user preferences"""
    
    def __init__(self):
        super().__init__("memory")
    
    async def execute(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int] = None) -> Dict[str, Any]:
        """Manage memory and context for the task"""
        try:
            # Get task details
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Get user context
            user_context = await self._get_user_context(task.user_id)
            
            # Get task history
            task_history = await self._get_task_history(task.user_id)
            
            # Get relevant memories
            relevant_memories = await self._get_relevant_memories(task.user_id, input_data.get("context_key", "general"))
            
            # Store new context if provided
            if "context_data" in input_data:
                await self._store_context(task.user_id, input_data["context_data"])
            
            # Update memory access times
            await self._update_memory_access(relevant_memories)
            
            # Compile context summary
            context_summary = {
                "user_preferences": user_context.get("preferences", {}),
                "task_history": task_history,
                "relevant_memories": relevant_memories,
                "current_task_context": {
                    "task_id": task_id,
                    "task_type": self._categorize_task(task.title),
                    "user_id": task.user_id
                }
            }
            
            # Log execution
            output_data = {
                "context_summary": context_summary,
                "memories_accessed": len(relevant_memories),
                "user_context_loaded": bool(user_context),
                "task_history_loaded": len(task_history)
            }
            
            self.log_execution(task_id, input_data, output_data, subtask_id=subtask_id)
            
            return {
                "status": "success",
                "context_summary": context_summary,
                "memories_accessed": len(relevant_memories),
                "message": f"Memory context loaded with {len(relevant_memories)} relevant memories"
            }
            
        except Exception as e:
            error_msg = f"Memory agent failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user context and preferences"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Get user preferences
            preferences = user.preferences or {}
            
            # Get recent memories
            recent_memories = self.db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.memory_type == "preference"
            ).order_by(Memory.last_accessed.desc()).limit(10).all()
            
            context = {
                "user_id": user_id,
                "username": user.username,
                "preferences": preferences,
                "recent_preferences": [m.value for m in recent_memories]
            }
            
            return context
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_task_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's task history"""
        try:
            # Get recent completed tasks
            recent_tasks = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == "completed"
            ).order_by(Task.completed_at.desc()).limit(5).all()
            
            task_history = []
            for task in recent_tasks:
                task_history.append({
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "category": self._categorize_task(task.title)
                })
            
            return task_history
            
        except Exception as e:
            return []
    
    async def _get_relevant_memories(self, user_id: int, context_key: str) -> List[Dict[str, Any]]:
        """Get memories relevant to the current context"""
        try:
            # Get memories by type and key
            memories = self.db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.key.like(f"%{context_key}%")
            ).order_by(Memory.importance.desc(), Memory.last_accessed.desc()).limit(10).all()
            
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "id": memory.id,
                    "type": memory.memory_type,
                    "key": memory.key,
                    "value": memory.value,
                    "importance": memory.importance,
                    "last_accessed": memory.last_accessed.isoformat()
                })
            
            return memory_list
            
        except Exception as e:
            return []
    
    async def _store_context(self, user_id: int, context_data: Dict[str, Any]):
        """Store new context in memory"""
        try:
            for key, value in context_data.items():
                memory = Memory(
                    user_id=user_id,
                    memory_type="context",
                    key=key,
                    value=value,
                    importance=5,  # Default importance
                    created_at=datetime.now(),
                    last_accessed=datetime.now()
                )
                self.db.add(memory)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def _update_memory_access(self, memories: List[Dict[str, Any]]):
        """Update last accessed time for memories"""
        try:
            for memory_data in memories:
                memory_id = memory_data.get("id")
                if memory_id:
                    memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
                    if memory:
                        memory.last_accessed = datetime.now()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _categorize_task(self, task_title: str) -> str:
        """Categorize task based on title"""
        title_lower = task_title.lower()
        
        if any(word in title_lower for word in ["trip", "travel", "vacation", "flight", "hotel"]):
            return "travel"
        elif any(word in title_lower for word in ["meeting", "agenda", "presentation"]):
            return "meeting"
        elif any(word in title_lower for word in ["learn", "study", "course", "education"]):
            return "learning"
        elif any(word in title_lower for word in ["event", "party", "celebration"]):
            return "event"
        elif any(word in title_lower for word in ["research", "analysis", "report"]):
            return "research"
        else:
            return "general" 