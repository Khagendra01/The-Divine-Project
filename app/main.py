import uvicorn
from fastapi import FastAPI
from app.api import app
from app.database import engine
from app.models import Base
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    ) 