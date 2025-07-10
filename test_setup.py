#!/usr/bin/env python3
"""
Test script for MiniMind setup verification
"""

import asyncio
import httpx
import json
from typing import Dict, Any


async def test_api_health():
    """Test API health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ API Health Check: PASSED")
                return True
            else:
                print("❌ API Health Check: FAILED")
                return False
    except Exception as e:
        print(f"❌ API Health Check: ERROR - {str(e)}")
        return False


async def test_demo_user_creation():
    """Test demo user creation"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8000/demo/create-user")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Demo User Creation: PASSED - User ID: {data.get('id')}")
                return data.get('id')
            else:
                print(f"❌ Demo User Creation: FAILED - Status: {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Demo User Creation: ERROR - {str(e)}")
        return None


async def test_demo_task_creation():
    """Test demo task creation"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8000/demo/task")
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                print(f"✅ Demo Task Creation: PASSED - Task ID: {task_id}")
                return task_id
            else:
                print(f"❌ Demo Task Creation: FAILED - Status: {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Demo Task Creation: ERROR - {str(e)}")
        return None


async def test_task_progress(task_id: int):
    """Test task progress monitoring"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/demo/tasks/{task_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Task Progress Check: PASSED")
                print(f"   Task Status: {data.get('task_status', 'unknown')}")
                print(f"   Progress: {data.get('progress_percentage', 0):.1f}%")
                print(f"   Current Step: {data.get('current_step', 'unknown')}")
                return True
            else:
                print(f"❌ Task Progress Check: FAILED - Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Task Progress Check: ERROR - {str(e)}")
        return False


async def test_manual_task_creation():
    """Test manual task creation with custom request"""
    try:
        async with httpx.AsyncClient() as client:
            # Create a user first
            user_response = await client.post("http://localhost:8000/users", json={
                "username": "testuser",
                "email": "test@example.com"
            })
            
            if user_response.status_code != 200:
                print("❌ Manual Task Creation: FAILED - Could not create user")
                return None
            
            user_data = user_response.json()
            user_id = user_data.get('id')
            
            # Create a task
            task_response = await client.post("http://localhost:8000/tasks", json={
                "user_id": user_id,
                "request": "Research the best restaurants in San Francisco",
                "context": {
                    "location": "San Francisco",
                    "cuisine": "any",
                    "budget": "moderate"
                }
            })
            
            if task_response.status_code == 200:
                task_data = task_response.json()
                task_id = task_data.get('task_id')
                print(f"✅ Manual Task Creation: PASSED - Task ID: {task_id}")
                return task_id
            else:
                print(f"❌ Manual Task Creation: FAILED - Status: {task_response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Manual Task Creation: ERROR - {str(e)}")
        return None


async def test_websocket_connection(task_id: int):
    """Test WebSocket connection for real-time updates"""
    try:
        import websockets
        uri = f"ws://localhost:8000/ws/{task_id}"
        
        async with websockets.connect(uri) as websocket:
            # Wait for a message
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(message)
            
            if data.get('type') == 'progress_update':
                print("✅ WebSocket Connection: PASSED")
                return True
            else:
                print("❌ WebSocket Connection: FAILED - Unexpected message format")
                return False
    except Exception as e:
        print(f"❌ WebSocket Connection: ERROR - {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting MiniMind Setup Tests...\n")
    
    # Test 1: API Health
    health_ok = await test_api_health()
    if not health_ok:
        print("\n❌ API is not running. Please start the application first.")
        return
    
    print()
    
    # Test 2: Demo User Creation
    user_id = await test_demo_user_creation()
    print()
    
    # Test 3: Demo Task Creation
    task_id = await test_demo_task_creation()
    if task_id:
        print()
        
        # Test 4: Task Progress
        await test_task_progress(task_id)
        print()
        
        # Test 5: WebSocket (optional)
        try:
            await test_websocket_connection(task_id)
        except ImportError:
            print("⚠️  WebSocket test skipped (websockets library not installed)")
        print()
    
    # Test 6: Manual Task Creation
    manual_task_id = await test_manual_task_creation()
    if manual_task_id:
        print()
        await test_task_progress(manual_task_id)
    
    print("\n🎉 MiniMind Setup Tests Completed!")
    print("\n📋 Next Steps:")
    print("1. Check the API documentation at: http://localhost:8000/docs")
    print("2. Monitor task progress using the demo endpoints")
    print("3. Create your own tasks with custom requests")
    print("4. Explore the multi-agent architecture in the codebase")


if __name__ == "__main__":
    asyncio.run(main()) 