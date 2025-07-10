import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.executor import ExecutorAgent
from app.agents.memory import MemoryAgent
from app.models import Task, Subtask, AgentExecution
from app.config import settings


class ControllerAgent(BaseAgent):
    """Agent responsible for orchestrating the entire workflow"""
    
    def __init__(self):
        super().__init__("controller")
        self.agents = {
            "planner": PlannerAgent(),
            "research": ResearchAgent(),
            "executor": ExecutorAgent(),
            "memory": MemoryAgent()
        }
    
    async def execute(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int] = None) -> Dict[str, Any]:
        """Orchestrate the complete task execution workflow"""
        try:
            # Set database session for all agents
            for agent in self.agents.values():
                agent.set_db(self.db)
            
            # Get task details
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Step 1: Load context and memory
            memory_result = await self._execute_memory_agent(task_id, input_data)
            if memory_result["status"] == "error":
                return memory_result
            
            # Step 2: Plan the task (if not already planned)
            if not subtask_id:
                planning_result = await self._execute_planner_agent(task_id, input_data)
                if planning_result["status"] == "error":
                    return planning_result
            
            # Step 3: Execute subtasks in order
            execution_result = await self._execute_subtasks(task_id, input_data)
            
            # Step 4: Update task status
            await self._update_task_completion(task_id, execution_result)
            
            # Log execution
            output_data = {
                "memory_result": memory_result,
                "planning_result": planning_result if not subtask_id else None,
                "execution_result": execution_result,
                "workflow_completed": True
            }
            
            self.log_execution(task_id, input_data, output_data, subtask_id=subtask_id)
            
            return {
                "status": "success",
                "workflow_completed": True,
                "total_subtasks": execution_result.get("total_subtasks", 0),
                "completed_subtasks": execution_result.get("completed_subtasks", 0),
                "message": "Task workflow completed successfully"
            }
            
        except Exception as e:
            error_msg = f"Controller agent failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _execute_memory_agent(self, task_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory agent to load context"""
        try:
            memory_agent = self.agents["memory"]
            return await memory_agent.execute(task_id, {
                **input_data,
                "context_key": "general"
            })
        except Exception as e:
            return {
                "status": "error",
                "message": f"Memory agent execution failed: {str(e)}"
            }
    
    async def _execute_planner_agent(self, task_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planner agent to create subtasks"""
        try:
            planner_agent = self.agents["planner"]
            return await planner_agent.execute(task_id, input_data)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Planner agent execution failed: {str(e)}"
            }
    
    async def _execute_subtasks(self, task_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all subtasks in order"""
        try:
            # Get all subtasks for this task
            subtasks = self.db.query(Subtask).filter(
                Subtask.task_id == task_id
            ).order_by(Subtask.order_index).all()
            
            completed_subtasks = 0
            failed_subtasks = 0
            
            for subtask in subtasks:
                try:
                    # Determine which agent to use
                    agent_type = subtask.agent_type
                    if agent_type not in self.agents:
                        # Default to executor for unknown agent types
                        agent_type = "executor"
                    
                    agent = self.agents[agent_type]
                    
                    # Execute the subtask
                    result = await agent.execute(task_id, {
                        **input_data,
                        "subtask_title": subtask.title,
                        "subtask_description": subtask.description,
                        "agent_type": agent_type
                    }, subtask.id)
                    
                    if result["status"] == "success":
                        completed_subtasks += 1
                        self.update_subtask_status(subtask.id, "completed")
                    else:
                        failed_subtasks += 1
                        self.update_subtask_status(subtask.id, "failed")
                    
                    # Add delay between subtasks to simulate real processing
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    failed_subtasks += 1
                    self.update_subtask_status(subtask.id, "failed")
                    print(f"Subtask {subtask.id} failed: {str(e)}")
            
            return {
                "total_subtasks": len(subtasks),
                "completed_subtasks": completed_subtasks,
                "failed_subtasks": failed_subtasks,
                "success_rate": completed_subtasks / len(subtasks) if subtasks else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Subtask execution failed: {str(e)}",
                "total_subtasks": 0,
                "completed_subtasks": 0,
                "failed_subtasks": 0
            }
    
    async def _update_task_completion(self, task_id: int, execution_result: Dict[str, Any]):
        """Update task completion status"""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return
            
            success_rate = execution_result.get("success_rate", 0)
            
            if success_rate >= 0.8:  # 80% success threshold
                task.status = "completed"
                task.completed_at = datetime.now()
            elif success_rate >= 0.5:  # 50% success threshold
                task.status = "partial"
            else:
                task.status = "failed"
            
            task.updated_at = datetime.now()
            self.db.commit()
            
        except Exception as e:
            print(f"Error updating task completion: {str(e)}")
    
    async def get_task_progress(self, task_id: int) -> Dict[str, Any]:
        """Get current progress of a task"""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"error": "Task not found"}
            
            subtasks = self.db.query(Subtask).filter(
                Subtask.task_id == task_id
            ).order_by(Subtask.order_index).all()
            
            executions = self.db.query(AgentExecution).filter(
                AgentExecution.task_id == task_id
            ).order_by(AgentExecution.started_at).all()
            
            completed_subtasks = sum(1 for st in subtasks if st.status == "completed")
            total_subtasks = len(subtasks)
            
            progress = {
                "task_id": task_id,
                "task_status": task.status,
                "total_subtasks": total_subtasks,
                "completed_subtasks": completed_subtasks,
                "progress_percentage": (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0,
                "current_step": self._get_current_step(subtasks),
                "recent_executions": [
                    {
                        "agent_type": ex.agent_type,
                        "status": ex.status,
                        "started_at": ex.started_at.isoformat(),
                        "completed_at": ex.completed_at.isoformat() if ex.completed_at else None
                    } for ex in executions[-5:]  # Last 5 executions
                ]
            }
            
            return progress
            
        except Exception as e:
            return {"error": f"Error getting progress: {str(e)}"}
    
    def _get_current_step(self, subtasks: List[Subtask]) -> Optional[str]:
        """Get the current step being executed"""
        for subtask in subtasks:
            if subtask.status == "executing":
                return subtask.title
            elif subtask.status == "pending":
                return f"Next: {subtask.title}"
        
        return "Completed" if all(st.status == "completed" for st in subtasks) else "Unknown" 