import asyncio
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models import Task, Subtask
from app.config import settings
from app.models import AgentExecution


class ExecutionResult(BaseModel):
    actions_taken: List[str] = Field(description="List of actions that were executed")
    content_created: List[str] = Field(description="Content or deliverables created")
    decisions_made: List[str] = Field(description="Decisions made during execution")
    status: str = Field(description="Execution status: success, partial, failed")
    next_steps: List[str] = Field(description="Recommended next steps")


class ExecutorAgent(BaseAgent):
    """Agent responsible for taking actions and creating content"""
    
    def __init__(self):
        super().__init__("executor")
        # Only initialize LLM if API key is available
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.2,
                api_key=settings.OPENAI_API_KEY
            )
            self.parser = PydanticOutputParser(pydantic_object=ExecutionResult)
        else:
            self.llm = None
            self.parser = None
    
    async def execute(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int] = None) -> Dict[str, Any]:
        """Execute actions and create content based on the subtask requirements"""
        try:
            # Get subtask details
            subtask = None
            if subtask_id:
                subtask = self.db.query(Subtask).filter(Subtask.id == subtask_id).first()
            
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Update subtask status
            if subtask:
                self.update_subtask_status(subtask_id, "executing")
            
            # Check if OpenAI API is available
            if not self.llm or not settings.OPENAI_API_KEY:
                return await self._perform_fallback_execution(task_id, input_data, subtask_id, task, subtask)
            
            # Get context from previous executions
            context = await self._get_execution_context(task_id, subtask_id)
            
            # Create execution prompt
            prompt = ChatPromptTemplate.from_template("""
            You are an execution expert. Your job is to take actions and create content based on the given requirements.
            
            Task: {task_title}
            Task Description: {task_description}
            Execution Focus: {execution_focus}
            Context from Previous Steps: {context}
            
            Based on the execution focus, provide:
            1. Specific actions to take
            2. Content or deliverables to create
            3. Decisions to make
            4. Next steps for continuation
            
            Consider:
            - Practical feasibility of actions
            - Quality and completeness of deliverables
            - Alignment with task objectives
            - Dependencies on previous steps
            
            {format_instructions}
            """)
            
            # Execute actions
            chain = prompt | self.llm | self.parser
            
            execution_focus = input_data.get("execution_focus", subtask.title if subtask else "general execution")
            
            result = await chain.ainvoke({
                "task_title": task.title,
                "task_description": task.description,
                "execution_focus": execution_focus,
                "context": context,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Simulate actual execution (in real implementation, this would call external APIs)
            execution_results = await self._simulate_execution(result.actions_taken, result.content_created)
            
            # Log execution
            output_data = {
                "actions_taken": result.actions_taken,
                "content_created": result.content_created,
                "decisions_made": result.decisions_made,
                "status": result.status,
                "next_steps": result.next_steps,
                "execution_results": execution_results
            }
            
            self.log_execution(task_id, input_data, output_data, subtask_id=subtask_id)
            
            # Update subtask status
            if subtask:
                self.update_subtask_status(subtask_id, "completed")
            
            return {
                "status": "success",
                "actions_taken": result.actions_taken,
                "content_created": result.content_created,
                "decisions_made": result.decisions_made,
                "execution_status": result.status,
                "next_steps": result.next_steps,
                "message": f"Execution completed with {len(result.actions_taken)} actions"
            }
            
        except Exception as e:
            error_msg = f"Executor agent failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            if subtask_id:
                self.update_subtask_status(subtask_id, "failed")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _perform_fallback_execution(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int], task: Task, subtask: Optional[Subtask]) -> Dict[str, Any]:
        """Perform basic execution when OpenAI API is not available"""
        try:
            execution_focus = input_data.get("execution_focus", subtask.title if subtask else "general execution")
            
            # Create basic execution results
            basic_actions = [
                f"Executed task: {execution_focus}",
                "Applied standard procedures",
                "Completed basic requirements"
            ]
            
            basic_content = [
                f"Created content for: {execution_focus}",
                "Generated basic deliverables"
            ]
            
            basic_decisions = [
                "Used standard approach for task execution",
                "Applied best practices"
            ]
            
            basic_next_steps = [
                "Review completed work",
                "Prepare for next phase if needed"
            ]
            
            # Simulate execution
            execution_results = await self._simulate_execution(basic_actions, basic_content)
            
            # Log execution
            output_data = {
                "actions_taken": basic_actions,
                "content_created": basic_content,
                "decisions_made": basic_decisions,
                "status": "success",
                "next_steps": basic_next_steps,
                "execution_results": execution_results,
                "fallback_mode": True
            }
            
            self.log_execution(task_id, input_data, output_data, subtask_id=subtask_id)
            
            # Update subtask status
            if subtask:
                self.update_subtask_status(subtask_id, "completed")
            
            return {
                "status": "success",
                "actions_taken": basic_actions,
                "content_created": basic_content,
                "decisions_made": basic_decisions,
                "execution_status": "success",
                "next_steps": basic_next_steps,
                "message": f"Basic execution completed (fallback mode - no OpenAI API key)",
                "fallback_mode": True
            }
            
        except Exception as e:
            error_msg = f"Fallback execution failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            if subtask_id:
                self.update_subtask_status(subtask_id, "failed")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _get_execution_context(self, task_id: int, subtask_id: Optional[int] = None) -> str:
        """Get context from previous agent executions"""
        try:
            # Get previous executions for this task
            previous_executions = self.db.query(AgentExecution).filter(
                AgentExecution.task_id == task_id,
                AgentExecution.status == "completed"
            ).order_by(AgentExecution.started_at.desc()).limit(5).all()
            
            context_parts = []
            for execution in previous_executions:
                if execution.output_data:
                    context_parts.append(f"{execution.agent_type}: {execution.output_data}")
            
            return "\n".join(context_parts) if context_parts else "No previous context available"
            
        except Exception as e:
            return f"Error getting context: {str(e)}"
    
    async def _simulate_execution(self, actions: List[str], content: List[str]) -> Dict[str, Any]:
        """Simulate actual execution of actions (in real implementation, this would call external APIs)"""
        try:
            # Simulate execution delay
            await asyncio.sleep(2)
            
            execution_results = {}
            
            # Simulate action execution
            for action in actions:
                execution_results[action] = {
                    "status": "completed",
                    "result": f"Successfully executed: {action}",
                    "timestamp": asyncio.get_event_loop().time()
                }
            
            # Simulate content creation
            for content_item in content:
                execution_results[f"create_{content_item}"] = {
                    "status": "completed",
                    "result": f"Created: {content_item}",
                    "content": f"Sample content for {content_item}",
                    "timestamp": asyncio.get_event_loop().time()
                }
            
            return execution_results
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            } 