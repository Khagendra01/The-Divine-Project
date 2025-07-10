#!/bin/bash

# MiniMind Startup Script

echo "🚀 Starting MiniMind Personal AI Assistant..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key"
    echo "   OPENAI_API_KEY=your_openai_api_key_here"
    exit 1
fi

# Load environment variables
source .env

# Check if OpenAI API key is set
if [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ Please set your OpenAI API key in the .env file"
    echo "   OPENAI_API_KEY=your_actual_api_key_here"
    exit 1
fi

echo "✅ Environment check passed"

# Start services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U minimind > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
    exit 1
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
    exit 1
fi

# Check FastAPI
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI is ready"
else
    echo "❌ FastAPI is not ready"
    exit 1
fi

echo ""
echo "🎉 MiniMind is now running!"
echo ""
echo "📡 API Endpoints:"
echo "   - Health Check: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Demo Task: http://localhost:8000/demo/task"
echo ""
echo "🧪 Test the setup:"
echo "   python test_setup.py"
echo ""
echo "📊 Monitor logs:"
echo "   docker-compose logs -f minimind-backend"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo "" 