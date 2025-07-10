from celery import shared_task
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services import TaskService
from app.agents.controller import ControllerAgent
from typing import Dict, Any


@shared_task
def execute_task_workflow(task_id: int, input_data: Dict[str, Any]):
    """Background task to execute the complete workflow for a task"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        controller = ControllerAgent()
        controller.set_db(db)
        
        # Execute the workflow
        result = controller.execute(task_id, input_data)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@shared_task
def cleanup_old_tasks():
    """Background task to cleanup old completed tasks"""
    db = SessionLocal()
    try:
        from app.models import Task
        from datetime import datetime, timedelta
        
        # Delete tasks older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        old_tasks = db.query(Task).filter(
            Task.status.in_(["completed", "failed"]),
            Task.created_at < cutoff_date
        ).all()
        
        for task in old_tasks:
            db.delete(task)
        
        db.commit()
        return {"deleted_tasks": len(old_tasks)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@shared_task
def update_task_progress(task_id: int):
    """Background task to update task progress"""
    db = SessionLocal()
    try:
        service = TaskService(db)
        progress = service.get_task_progress(task_id)
        return progress
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close() 