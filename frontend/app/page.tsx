'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api'
import type { Task, TaskStatus } from '@/lib/types'
import { Play, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [newTaskRequest, setNewTaskRequest] = useState('')
  const [selectedTask, setSelectedTask] = useState<TaskStatus | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  // Demo user ID (in a real app, this would come from authentication)
  const demoUserId = 1

  useEffect(() => {
    // Check API health on mount
    checkApiHealth()
    loadTasks()
  }, [])

  const checkApiHealth = async () => {
    try {
      await apiClient.health()
      setIsConnected(true)
    } catch (error) {
      console.error('API not connected:', error)
      setIsConnected(false)
    }
  }

  const loadTasks = async () => {
    try {
      const userTasks = await apiClient.getUserTasks(demoUserId)
      setTasks(userTasks)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const createDemoUser = async () => {
    setLoading(true)
    try {
      await apiClient.demoCreateUser()
      await loadTasks()
    } catch (error) {
      console.error('Failed to create demo user:', error)
    } finally {
      setLoading(false)
    }
  }

  const createDemoTask = async () => {
    setLoading(true)
    try {
      await apiClient.demoCreateTask()
      await loadTasks()
    } catch (error) {
      console.error('Failed to create demo task:', error)
    } finally {
      setLoading(false)
    }
  }

  const createTask = async () => {
    if (!newTaskRequest.trim()) return

    setLoading(true)
    try {
      await apiClient.createTask({
        user_id: demoUserId,
        request: newTaskRequest,
      })
      setNewTaskRequest('')
      await loadTasks()
    } catch (error) {
      console.error('Failed to create task:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTaskStatus = async (taskId: number) => {
    try {
      const status = await apiClient.getTaskStatus(taskId)
      setSelectedTask(status)
    } catch (error) {
      console.error('Failed to get task status:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'text-green-600'
      case 'running':
        return 'text-blue-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">Egent</h1>
          <p className="text-muted-foreground">AI Task Manager</p>
          <div className="flex items-center gap-2 mt-4">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-muted-foreground">
              {isConnected ? 'Connected to API' : 'API not connected'}
            </span>
          </div>
        </div>

        {/* Demo Controls */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Quick Start</CardTitle>
            <CardDescription>
              Create a demo user and task to get started
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-4">
            <Button onClick={createDemoUser} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Create Demo User
            </Button>
            <Button onClick={createDemoTask} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Create Demo Task
            </Button>
          </CardContent>
        </Card>

        {/* Create New Task */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create New Task</CardTitle>
            <CardDescription>
              Describe what you want the AI to help you with
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="e.g., Help me plan a vacation to Japan, research the best restaurants in Tokyo, and create a budget spreadsheet"
              value={newTaskRequest}
              onChange={(e) => setNewTaskRequest(e.target.value)}
              rows={3}
            />
            <Button onClick={createTask} disabled={loading || !newTaskRequest.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
              Create Task
            </Button>
          </CardContent>
        </Card>

        {/* Tasks List */}
        <div className="grid gap-6">
          <h2 className="text-2xl font-semibold">Your Tasks</h2>
          {tasks.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">No tasks yet. Create a demo task to get started.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {tasks.map((task) => (
                <Card key={task.id} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(task.status)}
                        <CardTitle className="text-lg">{task.title}</CardTitle>
                      </div>
                      <span className={`text-sm font-medium ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    <CardDescription>{task.description}</CardDescription>
                  </CardHeader>
                  <CardFooter className="flex justify-between">
                    <div className="text-sm text-muted-foreground">
                      Created: {new Date(task.created_at).toLocaleDateString()}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => getTaskStatus(task.id)}
                    >
                      View Details
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Task Details Modal */}
        {selectedTask && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Task Details</CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedTask(null)}
                  >
                    ×
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Progress</h4>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${selectedTask.progress}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {Math.round(selectedTask.progress)}% complete
                  </p>
                </div>

                {selectedTask.current_step && (
                  <div>
                    <h4 className="font-medium mb-2">Current Step</h4>
                    <p className="text-sm text-muted-foreground">{selectedTask.current_step}</p>
                  </div>
                )}

                {selectedTask.subtasks.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Subtasks</h4>
                    <div className="space-y-2">
                      {selectedTask.subtasks.map((subtask) => (
                        <div key={subtask.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                          {getStatusIcon(subtask.status)}
                          <span className="text-sm">{subtask.title}</span>
                          <span className="text-xs text-muted-foreground ml-auto">
                            {subtask.agent_type}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTask.executions.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Agent Executions</h4>
                    <div className="space-y-2">
                      {selectedTask.executions.map((execution) => (
                        <div key={execution.id} className="p-2 bg-gray-50 rounded">
                          <div className="flex items-center gap-2 mb-1">
                            {getStatusIcon(execution.status)}
                            <span className="text-sm font-medium">{execution.agent_type}</span>
                          </div>
                          {execution.error_message && (
                            <p className="text-xs text-red-600">{execution.error_message}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
} 