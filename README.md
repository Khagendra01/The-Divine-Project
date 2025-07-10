# MiniMind - Personal AI Assistant Backend

A sophisticated personal AI assistant that can break down complex user requests into subtasks, plan execution steps, and carry them out autonomously using a multi-agent architecture.

## 🚀 Features

- **Natural Language Task Processing** - Submit complex requests like "Plan a weekend trip to NYC under $500"
- **Autonomous Task Decomposition** - AI breaks requests into research, planning, execution, etc.
- **Multi-Agent Coordination** - Specialized agents handle different aspects
- **Real-time Progress Tracking** - See the AI "thinking" and executing steps
- **Memory & Context** - Remembers user preferences and past interactions

## 🏗️ Architecture

```
User Request → Planner Agent → Task Graph → Specialized Agents → Results
                ↓
Memory Agent (context) → Controller Agent → Real-time Updates
```

### Core Agents

- **Planner Agent** - Decomposes tasks and creates execution plans
- **Research Agent** - Gathers information using web search, APIs
- **Memory Agent** - Manages context and user preferences
- **Executor Agent** - Coordinates actions and tool usage
- **Controller Agent** - Orchestrates the entire workflow

## 🛠️ Tech Stack

- **Backend**: FastAPI with gRPC for inter-service communication
- **AI Framework**: LangChain + LangGraph for agent orchestration
- **Database**: PostgreSQL for persistent memory and task state
- **Message Queue**: Redis + Celery for background tasks
- **Real-time**: WebSocket for live updates

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- OpenAI API Key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd minimind
```

### 2. Environment Setup

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://minimind:minimind123@localhost:5432/minimind
REDIS_URL=redis://localhost:6379
```

### 3. Run with Docker

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f minimind-backend
```

### 4. Manual Setup (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Run migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.celery_app worker --loglevel=info
```

## 📡 API Endpoints

### Core Endpoints

- `POST /tasks` - Create a new task
- `GET /tasks/{task_id}` - Get task status
- `GET /tasks/{task_id}/progress` - Get detailed progress
- `GET /users/{user_id}/tasks` - Get user's tasks

### Demo Endpoints

- `POST /demo/task` - Create a demo task
- `GET /demo/tasks/{task_id}` - Get demo task progress

### WebSocket

- `WS /ws/{task_id}` - Real-time task updates

## 🧪 Testing

### Create a Demo Task

```bash
# Create a demo task
curl -X POST "http://localhost:8000/demo/task"

# Get task progress
curl -X GET "http://localhost:8000/demo/tasks/1"
```

### Manual API Testing

```bash
# Create a user
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'

# Create a task
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "request": "Plan a weekend trip to NYC under $500",
    "context": {"budget": 500, "destination": "NYC"}
  }'

# Check task status
curl -X GET "http://localhost:8000/tasks/1"
```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `DEBUG` - Enable debug mode (default: True)

### Agent Settings

- `MAX_TASK_DURATION` - Maximum task execution time (default: 300s)
- `MAX_SUBTASKS` - Maximum number of subtasks per task (default: 10)

## 📊 Demo Scenarios

### 1. Trip Planning
- Research flights and hotels
- Create budget breakdown
- Generate itinerary
- Check weather forecast

### 2. Meeting Preparation
- Research participants
- Create agenda
- Prepare materials
- Schedule follow-ups

### 3. Learning Path
- Assess current knowledge
- Create personalized study plan
- Find relevant resources
- Set milestones

### 4. Event Organization
- Research venues
- Create guest list
- Plan logistics
- Send invitations

## 🏗️ Project Structure

```
minimind/
├── app/
│   ├── agents/           # AI agents
│   │   ├── base.py      # Base agent class
│   │   ├── planner.py   # Task decomposition
│   │   ├── research.py  # Information gathering
│   │   ├── executor.py  # Action execution
│   │   ├── memory.py    # Context management
│   │   └── controller.py # Workflow orchestration
│   ├── api.py           # FastAPI routes
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── services.py      # Business logic
│   ├── tasks.py         # Celery tasks
│   └── main.py          # Application entry
├── alembic/             # Database migrations
├── docker-compose.yml   # Docker services
├── Dockerfile          # Container setup
└── requirements.txt    # Dependencies
```

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Status
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U minimind -d minimind

# Check tables
\dt
```

### Celery Status
```bash
# Check Celery workers
docker-compose exec minimind-backend celery -A app.celery_app inspect active
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables**
   ```env
   DEBUG=False
   OPENAI_API_KEY=your_production_key
   DATABASE_URL=your_production_db_url
   REDIS_URL=your_production_redis_url
   ```

2. **Database Migration**
   ```bash
   alembic upgrade head
   ```

3. **Start Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Scaling

- **Horizontal Scaling**: Add more Celery workers
- **Database**: Use connection pooling
- **Redis**: Configure clustering for high availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints

---

**MiniMind** - Your Personal AI Assistant 🤖 