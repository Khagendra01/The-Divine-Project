import asyncio
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models import Task, Subtask
from app.config import settings


class SubtaskPlan(BaseModel):
    title: str = Field(description="Clear, concise title for the subtask")
    description: str = Field(description="Detailed description of what needs to be done")
    agent_type: str = Field(description="Type of agent to handle this subtask: planner, research, executor, memory, controller")
    order_index: int = Field(description="Order in which this subtask should be executed (0-based)")
    estimated_duration: int = Field(description="Estimated duration in seconds")


class TaskPlan(BaseModel):
    subtasks: List[SubtaskPlan] = Field(description="List of subtasks needed to complete the main task")
    estimated_total_duration: int = Field(description="Total estimated duration in seconds")
    complexity_level: str = Field(description="Complexity level: simple, moderate, complex")


class PlannerAgent(BaseAgent):
    """Agent responsible for decomposing complex tasks into subtasks"""
    
    def __init__(self):
        super().__init__("planner")
        # Only initialize LLM if API key is available
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY
            )
            self.parser = PydanticOutputParser(pydantic_object=TaskPlan)
        else:
            self.llm = None
            self.parser = None
    
    async def execute(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int] = None) -> Dict[str, Any]:
        """Decompose a complex task into subtasks"""
        try:
            # Get task details
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Check if OpenAI API is available
            if not self.llm or not settings.OPENAI_API_KEY:
                return await self._create_fallback_subtasks(task_id, input_data, task)
            
            # Create planning prompt
            prompt = ChatPromptTemplate.from_template("""
            You are a task planning expert. Your job is to break down complex user requests into manageable subtasks.
            
            User Request: {request}
            Task Description: {description}
            
            Analyze this request and create a detailed plan with the following considerations:
            1. Break down the request into logical, sequential steps
            2. Assign appropriate agent types for each subtask
            3. Consider dependencies between subtasks
            4. Estimate realistic timeframes
            5. Ensure all aspects of the request are covered
            
            Available agent types:
            - planner: For high-level planning and coordination
            - research: For gathering information, searching, analyzing data
            - executor: For taking actions, creating content, making decisions
            - memory: For managing context, preferences, and historical data
            - controller: For orchestrating other agents and managing workflow
            
            {format_instructions}
            """)
            
            # Execute planning
            chain = prompt | self.llm | self.parser
            
            result = await chain.ainvoke({
                "request": input_data.get("request", task.title),
                "description": task.description,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Create subtasks in database
            created_subtasks = []
            for subtask_plan in result.subtasks:
                subtask = Subtask(
                    task_id=task_id,
                    title=subtask_plan.title,
                    description=subtask_plan.description,
                    agent_type=subtask_plan.agent_type,
                    order_index=subtask_plan.order_index,
                    status="pending"
                )
                self.db.add(subtask)
                created_subtasks.append(subtask)
            
            self.db.commit()
            
            # Update task status
            self.update_task_status(task_id, "planning")
            
            # Log execution
            output_data = {
                "subtasks_created": len(created_subtasks),
                "estimated_duration": result.estimated_total_duration,
                "complexity_level": result.complexity_level,
                "subtask_details": [
                    {
                        "title": st.title,
                        "agent_type": st.agent_type,
                        "order_index": st.order_index
                    } for st in created_subtasks
                ]
            }
            
            self.log_execution(task_id, input_data, output_data)
            
            return {
                "status": "success",
                "subtasks_created": len(created_subtasks),
                "estimated_duration": result.estimated_total_duration,
                "complexity_level": result.complexity_level,
                "message": f"Successfully decomposed task into {len(created_subtasks)} subtasks"
            }
            
        except Exception as e:
            error_msg = f"Planner agent failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _create_fallback_subtasks(self, task_id: int, input_data: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """Create basic subtasks when OpenAI API is not available"""
        try:
            request = input_data.get("request", task.title)
            
            # Create basic subtasks based on common patterns
            subtasks = []
            
            # Always start with memory/context loading
            subtasks.append(SubtaskPlan(
                title="Load User Context",
                description="Load user preferences and historical context",
                agent_type="memory",
                order_index=0,
                estimated_duration=30
            ))
            
            # Add research step for most tasks
            subtasks.append(SubtaskPlan(
                title="Research and Gather Information",
                description="Research relevant information for the task",
                agent_type="research",
                order_index=1,
                estimated_duration=120
            ))
            
            # Add execution step
            subtasks.append(SubtaskPlan(
                title="Execute Task",
                description="Execute the main task based on research",
                agent_type="executor",
                order_index=2,
                estimated_duration=180
            ))
            
            # Create subtasks in database
            created_subtasks = []
            for subtask_plan in subtasks:
                subtask = Subtask(
                    task_id=task_id,
                    title=subtask_plan.title,
                    description=subtask_plan.description,
                    agent_type=subtask_plan.agent_type,
                    order_index=subtask_plan.order_index,
                    status="pending"
                )
                self.db.add(subtask)
                created_subtasks.append(subtask)
            
            self.db.commit()
            
            # Update task status
            self.update_task_status(task_id, "planning")
            
            # Log execution
            output_data = {
                "subtasks_created": len(created_subtasks),
                "estimated_duration": 330,  # 5.5 minutes total
                "complexity_level": "simple",
                "subtask_details": [
                    {
                        "title": st.title,
                        "agent_type": st.agent_type,
                        "order_index": st.order_index
                    } for st in created_subtasks
                ],
                "fallback_mode": True
            }
            
            self.log_execution(task_id, input_data, output_data)
            
            return {
                "status": "success",
                "subtasks_created": len(created_subtasks),
                "estimated_duration": 330,
                "complexity_level": "simple",
                "message": f"Created {len(created_subtasks)} basic subtasks (fallback mode - no OpenAI API key)",
                "fallback_mode": True
            }
            
        except Exception as e:
            error_msg = f"Fallback subtask creation failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg)
            return {
                "status": "error",
                "message": error_msg
            } 