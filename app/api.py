from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio

from app.database import get_db
from app.services import TaskService
from app.schemas import TaskRequest, TaskResponse, TaskStatus, UserCreate, User
from app.config import settings

app = FastAPI(
    title="MiniMind API",
    description="Personal AI Assistant Backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "MiniMind API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "minimind"}

# User endpoints
@app.post("/users", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    service = TaskService(db)
    result = await service.create_user(user.username, user.email)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    from app.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: int, 
    preferences: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    service = TaskService(db)
    result = await service.update_user_preferences(user_id, preferences)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

# Task endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest, db: Session = Depends(get_db)):
    """Create a new task and start the workflow"""
    service = TaskService(db)
    result = await service.create_task(task_request)
    
    if result.status == "error":
        raise HTTPException(status_code=400, detail=result.message)
    
    return result

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: int, db: Session = Depends(get_db)):
    """Get the current status of a task"""
    service = TaskService(db)
    result = await service.get_task_status(task_id)
    
    if result.status == "not_found":
        raise HTTPException(status_code=404, detail="Task not found")
    
    return result

@app.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: int, db: Session = Depends(get_db)):
    """Get detailed progress information for a task"""
    service = TaskService(db)
    result = await service.get_task_progress(task_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/users/{user_id}/tasks")
async def get_user_tasks(user_id: int, db: Session = Depends(get_db)):
    """Get all tasks for a user"""
    service = TaskService(db)
    result = await service.get_user_tasks(user_id)
    return result

# Memory endpoints
@app.post("/users/{user_id}/memories")
async def store_memory(
    user_id: int,
    memory_type: str,
    key: str,
    value: Dict[str, Any],
    importance: int = 5,
    db: Session = Depends(get_db)
):
    """Store a new memory"""
    service = TaskService(db)
    result = await service.store_memory(user_id, memory_type, key, value, importance)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/users/{user_id}/memories")
async def get_user_memories(
    user_id: int,
    memory_type: str = None,
    db: Session = Depends(get_db)
):
    """Get memories for a user"""
    service = TaskService(db)
    result = await service.get_user_memories(user_id, memory_type)
    return result

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates about task progress
            db = next(get_db())
            service = TaskService(db)
            progress = await service.get_task_progress(task_id)
            
            await websocket.send_text(json.dumps({
                "type": "progress_update",
                "task_id": task_id,
                "data": progress
            }))
            
            # Wait before sending next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Agent endpoints for direct interaction
@app.post("/agents/{agent_type}/execute")
async def execute_agent(
    agent_type: str,
    task_id: int,
    input_data: Dict[str, Any],
    subtask_id: int = None,
    db: Session = Depends(get_db)
):
    """Execute a specific agent directly"""
    from app.agents.planner import PlannerAgent
    from app.agents.research import ResearchAgent
    from app.agents.executor import ExecutorAgent
    from app.agents.memory import MemoryAgent
    
    agents = {
        "planner": PlannerAgent(),
        "research": ResearchAgent(),
        "executor": ExecutorAgent(),
        "memory": MemoryAgent()
    }
    
    if agent_type not in agents:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")
    
    agent = agents[agent_type]
    agent.set_db(db)
    
    try:
        result = await agent.execute(task_id, input_data, subtask_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

# Demo endpoints for testing
@app.post("/demo/create-user")
async def demo_create_user(db: Session = Depends(get_db)):
    """Create a demo user for testing"""
    service = TaskService(db)
    result = await service.create_user("demo_user", "demo1@example.com")
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/demo/task")
async def demo_create_task(db: Session = Depends(get_db)):
    """Create a demo task for testing"""
    # First create a user if needed
    service = TaskService(db)
    user_result = await service.create_user("demo_user", "demo1@example.com")
    
    if "error" in user_result:
        # Try to get existing user
        from app.models import User
        user = db.query(User).filter(User.username == "demo_user").first()
        if not user:
            raise HTTPException(status_code=400, detail="Failed to create or find demo user")
        user_id = user.id
    else:
        user_id = user_result["id"]
    
    # Create a demo task
    task_request = TaskRequest(
        user_id=user_id,
        request="Plan a weekend trip to NYC under $500",
        context={"budget": 500, "destination": "NYC", "duration": "weekend"}
    )
    
    result = await service.create_task(task_request)
    return result

@app.get("/demo/tasks/{task_id}")
async def demo_get_task_progress(task_id: int, db: Session = Depends(get_db)):
    """Get demo task progress"""
    service = TaskService(db)
    result = await service.get_task_progress(task_id)
    return result 