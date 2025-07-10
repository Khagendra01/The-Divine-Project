import asyncio
import httpx
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models import Task, Subtask
from app.config import settings


class ResearchResult(BaseModel):
    findings: List[str] = Field(description="Key findings from the research")
    sources: List[str] = Field(description="Sources of information")
    recommendations: List[str] = Field(description="Recommendations based on findings")
    confidence_level: str = Field(description="Confidence level: low, medium, high")


class ResearchAgent(BaseAgent):
    """Agent responsible for gathering information and performing research"""
    
    def __init__(self):
        super().__init__("research")
        # Only initialize LLM if API key is available
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY
            )
            self.parser = PydanticOutputParser(pydantic_object=ResearchResult)
        else:
            self.llm = None
            self.parser = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int] = None) -> Dict[str, Any]:
        """Perform research based on the subtask requirements"""
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
                return await self._perform_fallback_research(task_id, input_data, subtask_id, task, subtask)
            
            # Create research prompt
            prompt = ChatPromptTemplate.from_template("""
            You are a research expert. Your job is to gather and analyze information based on the given requirements.
            
            Task: {task_title}
            Task Description: {task_description}
            Research Focus: {research_focus}
            
            Based on the research focus, provide:
            1. Key findings and insights
            2. Relevant sources of information
            3. Actionable recommendations
            4. Confidence level in your findings
            
            Consider:
            - Accuracy and reliability of information
            - Relevance to the task requirements
            - Practical applicability of findings
            - Current and up-to-date information
            
            {format_instructions}
            """)
            
            # Execute research
            chain = prompt | self.llm | self.parser
            
            research_focus = input_data.get("research_focus", subtask.title if subtask else "general research")
            
            result = await chain.ainvoke({
                "task_title": task.title,
                "task_description": task.description,
                "research_focus": research_focus,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Perform additional web research if needed
            web_results = await self._perform_web_research(research_focus)
            
            # Combine results
            combined_findings = result.findings + web_results.get("findings", [])
            combined_sources = result.sources + web_results.get("sources", [])
            
            # Log execution
            output_data = {
                "findings": combined_findings,
                "sources": combined_sources,
                "recommendations": result.recommendations,
                "confidence_level": result.confidence_level,
                "web_results": web_results
            }
            
            self.log_execution(task_id, input_data, output_data, subtask_id=subtask_id)
            
            # Update subtask status
            if subtask:
                self.update_subtask_status(subtask_id, "completed")
            
            return {
                "status": "success",
                "findings": combined_findings,
                "sources": combined_sources,
                "recommendations": result.recommendations,
                "confidence_level": result.confidence_level,
                "message": f"Research completed with {len(combined_findings)} findings"
            }
            
        except Exception as e:
            error_msg = f"Research agent failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            if subtask_id:
                self.update_subtask_status(subtask_id, "failed")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _perform_fallback_research(self, task_id: int, input_data: Dict[str, Any], subtask_id: Optional[int], task: Task, subtask: Optional[Subtask]) -> Dict[str, Any]:
        """Perform basic research when OpenAI API is not available"""
        try:
            research_focus = input_data.get("research_focus", subtask.title if subtask else "general research")
            
            # Perform basic web research
            web_results = await self._perform_web_research(research_focus)
            
            # Create basic findings based on the task
            basic_findings = [
                f"Basic research completed for: {research_focus}",
                "Information gathered from available sources",
                "Recommendations based on general knowledge"
            ]
            
            basic_recommendations = [
                "Consider user preferences and context",
                "Apply best practices for the given task",
                "Monitor progress and adjust as needed"
            ]
            
            # Log execution
            output_data = {
                "findings": basic_findings + web_results.get("findings", []),
                "sources": web_results.get("sources", []),
                "recommendations": basic_recommendations,
                "confidence_level": "medium",
                "web_results": web_results,
                "fallback_mode": True
            }
            
            self.log_execution(task_id, input_data, output_data, subtask_id=subtask_id)
            
            # Update subtask status
            if subtask:
                self.update_subtask_status(subtask_id, "completed")
            
            return {
                "status": "success",
                "findings": basic_findings + web_results.get("findings", []),
                "sources": web_results.get("sources", []),
                "recommendations": basic_recommendations,
                "confidence_level": "medium",
                "message": f"Basic research completed (fallback mode - no OpenAI API key)",
                "fallback_mode": True
            }
            
        except Exception as e:
            error_msg = f"Fallback research failed: {str(e)}"
            self.log_execution(task_id, input_data, {}, "failed", error_msg, subtask_id)
            if subtask_id:
                self.update_subtask_status(subtask_id, "failed")
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def _perform_web_research(self, query: str) -> Dict[str, Any]:
        """Perform web research using mock API calls (in real implementation, use actual search APIs)"""
        try:
            # Mock web research - in real implementation, use actual search APIs
            # For demo purposes, we'll simulate web research
            await asyncio.sleep(1)  # Simulate API call delay
            
            return {
                "findings": [
                    f"Web research finding for: {query}",
                    "Additional context from online sources",
                    "Current market trends and data"
                ],
                "sources": [
                    "https://example.com/research1",
                    "https://example.com/research2"
                ]
            }
        except Exception as e:
            return {
                "findings": [],
                "sources": [],
                "error": str(e)
            }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose() 