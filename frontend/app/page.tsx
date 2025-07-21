'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api'
import type { Task, TaskStatus } from '@/lib/types'
import { Play, Clock, CheckCircle, AlertCircle, Loader2, ChevronDown, ChevronRight, FileText, Code, Database, Search, Brain, Settings, RefreshCw } from 'lucide-react'

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [newTaskRequest, setNewTaskRequest] = useState('')
  const [selectedTask, setSelectedTask] = useState<TaskStatus | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [expandedExecutions, setExpandedExecutions] = useState<Set<number>>(new Set())
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Demo user ID (in a real app, this would come from authentication)
  const demoUserId = 1

  useEffect(() => {
    // Check API health on mount
    checkApiHealth()
    loadTasks()
  }, [])

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh && selectedTask) {
      const startPolling = () => {
        pollingIntervalRef.current = setInterval(async () => {
          if (selectedTask && selectedTask.status !== 'completed' && selectedTask.status !== 'error') {
            try {
              setRefreshing(true)
              const updatedStatus = await apiClient.getTaskStatus(selectedTask.task_id)
              setSelectedTask(updatedStatus)
              
              // Stop polling if task is completed or failed
              if (updatedStatus.status === 'completed' || updatedStatus.status === 'error') {
                setAutoRefresh(false)
                if (pollingIntervalRef.current) {
                  clearInterval(pollingIntervalRef.current)
                  pollingIntervalRef.current = null
                }
              }
            } catch (error) {
              console.error('Failed to refresh task status:', error)
            } finally {
              setRefreshing(false)
            }
          }
        }, 2000) // Poll every 2 seconds
      }

      startPolling()

      return () => {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
      }
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [autoRefresh, selectedTask])

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
      // Auto-enable refresh for running tasks
      if (status.status === 'running' || status.status === 'executing') {
        setAutoRefresh(true)
      }
    } catch (error) {
      console.error('Failed to get task status:', error)
    }
  }

  const refreshTaskStatus = async () => {
    if (!selectedTask) return
    
    try {
      setRefreshing(true)
      const updatedStatus = await apiClient.getTaskStatus(selectedTask.task_id)
      setSelectedTask(updatedStatus)
      
      // Stop auto-refresh if task is completed
      if (updatedStatus.status === 'completed' || updatedStatus.status === 'error') {
        setAutoRefresh(false)
      }
    } catch (error) {
      console.error('Failed to refresh task status:', error)
    } finally {
      setRefreshing(false)
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

  const getAgentIcon = (agentType: string) => {
    switch (agentType.toLowerCase()) {
      case 'planner':
        return <Settings className="h-4 w-4 text-blue-500" />
      case 'research':
        return <Search className="h-4 w-4 text-green-500" />
      case 'executor':
        return <Code className="h-4 w-4 text-purple-500" />
      case 'memory':
        return <Brain className="h-4 w-4 text-orange-500" />
      case 'controller':
        return <Database className="h-4 w-4 text-indigo-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const toggleExecutionExpansion = (executionId: number) => {
    const newExpanded = new Set(expandedExecutions)
    if (newExpanded.has(executionId)) {
      newExpanded.delete(executionId)
    } else {
      newExpanded.add(executionId)
    }
    setExpandedExecutions(newExpanded)
  }

  const formatJsonData = (data: any) => {
    if (!data) return 'No data available'
    try {
      return JSON.stringify(data, null, 2)
    } catch {
      return String(data)
    }
  }

  const renderExecutionDetails = (execution: any) => {
    const isExpanded = expandedExecutions.has(execution.id)
    
    return (
      <Card key={execution.id} className="mb-3 border-l-4 border-l-blue-500">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getAgentIcon(execution.agent_type)}
              <span className="font-medium text-sm">{execution.agent_type}</span>
              {getStatusIcon(execution.status)}
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${getStatusColor(execution.status)}`}>
                {execution.status}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleExecutionExpansion(execution.id)}
                className="h-6 w-6 p-0"
              >
                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          <div className="text-xs text-muted-foreground">
            Started: {new Date(execution.started_at).toLocaleTimeString()}
            {execution.completed_at && (
              <> • Completed: {new Date(execution.completed_at).toLocaleTimeString()}</>
            )}
          </div>
        </CardHeader>
        
        {isExpanded && (
          <CardContent className="pt-0 space-y-4">
            {/* Input Data */}
            {execution.input_data && (
              <div>
                <h5 className="text-sm font-medium mb-2 text-blue-600">Input Data</h5>
                <pre className="text-xs bg-gray-50 p-3 rounded border overflow-x-auto">
                  {formatJsonData(execution.input_data)}
                </pre>
              </div>
            )}

            {/* Output Data */}
            {execution.output_data && (
              <div>
                <h5 className="text-sm font-medium mb-2 text-green-600">Output Data</h5>
                <pre className="text-xs bg-gray-50 p-3 rounded border overflow-x-auto">
                  {formatJsonData(execution.output_data)}
                </pre>
              </div>
            )}

            {/* Error Message */}
            {execution.error_message && (
              <div>
                <h5 className="text-sm font-medium mb-2 text-red-600">Error</h5>
                <div className="text-xs bg-red-50 p-3 rounded border text-red-700">
                  {execution.error_message}
                </div>
              </div>
            )}

            {/* Tool Calls */}
            {execution.output_data?.tool_calls && (
              <div>
                <h5 className="text-sm font-medium mb-2 text-purple-600">Tool Calls</h5>
                <div className="space-y-2">
                  {execution.output_data.tool_calls.map((toolCall: any, index: number) => (
                    <div key={index} className="bg-purple-50 p-3 rounded border">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-medium text-purple-700">Tool: {toolCall.name}</span>
                        <span className="text-xs text-purple-600">Function Call</span>
                      </div>
                      {toolCall.arguments && (
                        <div className="mb-2">
                          <span className="text-xs font-medium text-purple-700">Arguments:</span>
                          <pre className="text-xs bg-white p-2 rounded mt-1 overflow-x-auto">
                            {formatJsonData(toolCall.arguments)}
                          </pre>
                        </div>
                      )}
                      {toolCall.result && (
                        <div>
                          <span className="text-xs font-medium text-purple-700">Result:</span>
                          <pre className="text-xs bg-white p-2 rounded mt-1 overflow-x-auto">
                            {formatJsonData(toolCall.result)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    )
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
                        {/* Live indicator for running tasks */}
                        {(task.status === 'running' || task.status === 'executing') && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            LIVE
                          </div>
                        )}
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

        {/* Enhanced Task Details Modal */}
        {selectedTask && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              <CardHeader className="sticky top-0 bg-background z-10 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl">Task Details</CardTitle>
                    <CardDescription>
                      Task ID: {selectedTask.task_id} • Status: {selectedTask.status}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Auto-refresh toggle */}
                    {(selectedTask.status === 'running' || selectedTask.status === 'executing') && (
                      <Button
                        variant={autoRefresh ? "default" : "outline"}
                        size="sm"
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        className="flex items-center gap-2"
                      >
                        <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
                        {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                      </Button>
                    )}
                    
                    {/* Manual refresh */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={refreshTaskStatus}
                      disabled={refreshing}
                    >
                      {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedTask(null)
                        setAutoRefresh(false)
                      }}
                    >
                      ×
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-6">
                {/* Progress Section */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-3 text-blue-900">Progress Overview</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Overall Progress</span>
                      <span className="text-sm font-bold text-blue-600">{Math.round(selectedTask.progress)}%</span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-3">
                      <div
                        className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${selectedTask.progress}%` }}
                      />
                    </div>
                    {selectedTask.current_step && (
                      <div className="text-sm text-blue-700">
                        <span className="font-medium">Current Step:</span> {selectedTask.current_step}
                      </div>
                    )}
                  </div>
                </div>

                {/* Subtasks Section */}
                {selectedTask.subtasks.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-gray-900">Subtasks ({selectedTask.subtasks.length})</h4>
                    <div className="space-y-2">
                      {selectedTask.subtasks.map((subtask) => (
                        <div key={subtask.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                          {getStatusIcon(subtask.status)}
                          <div className="flex-1">
                            <div className="font-medium text-sm">{subtask.title}</div>
                            <div className="text-xs text-gray-600">{subtask.description}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getAgentIcon(subtask.agent_type)}
                            <span className="text-xs text-gray-500">{subtask.agent_type}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Agent Executions Section */}
                {selectedTask.executions.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-gray-900">
                      Agent Executions ({selectedTask.executions.length})
                    </h4>
                    <div className="space-y-2">
                      {selectedTask.executions.map((execution) => renderExecutionDetails(execution))}
                    </div>
                  </div>
                )}

                {/* Final Results Section */}
                {selectedTask.status === 'completed' && (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-3 text-green-900">Final Results</h4>
                    <div className="space-y-3">
                      <div className="text-sm text-green-700">
                        Task completed successfully! Here are the results:
                      </div>
                      
                      {/* Show final execution results */}
                      {selectedTask.executions.length > 0 && (
                        <div className="space-y-3">
                          {selectedTask.executions
                            .filter(exec => exec.status === 'completed' && exec.output_data)
                            .map((execution, index) => (
                              <div key={execution.id} className="bg-white p-3 rounded border">
                                <div className="flex items-center gap-2 mb-2">
                                  {getAgentIcon(execution.agent_type)}
                                  <span className="text-sm font-medium text-green-800">
                                    {execution.agent_type} Results
                                  </span>
                                </div>
                                
                                {/* Display structured results */}
                                {execution.output_data?.result && (
                                  <div className="mb-2">
                                    <span className="text-xs font-medium text-green-700">Result:</span>
                                    <div className="text-sm bg-green-50 p-2 rounded mt-1">
                                      {typeof execution.output_data.result === 'string' 
                                        ? execution.output_data.result 
                                        : formatJsonData(execution.output_data.result)
                                      }
                                    </div>
                                  </div>
                                )}
                                
                                {/* Display tool call results */}
                                {execution.output_data?.tool_calls && (
                                  <div>
                                    <span className="text-xs font-medium text-green-700">Tool Results:</span>
                                    <div className="space-y-2 mt-1">
                                      {execution.output_data.tool_calls.map((toolCall: any, toolIndex: number) => (
                                        <div key={toolIndex} className="bg-green-50 p-2 rounded">
                                          <div className="text-xs font-medium text-green-700 mb-1">
                                            {toolCall.name}
                                          </div>
                                          {toolCall.result && (
                                            <div className="text-xs text-green-600">
                                              {typeof toolCall.result === 'string' 
                                                ? toolCall.result 
                                                : formatJsonData(toolCall.result)
                                              }
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Fallback to raw output data */}
                                {!execution.output_data?.result && !execution.output_data?.tool_calls && (
                                  <div className="text-xs text-green-600">
                                    <pre className="bg-green-50 p-2 rounded overflow-x-auto">
                                      {formatJsonData(execution.output_data)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            ))}
                        </div>
                      )}
                      
                      {/* Summary */}
                      <div className="text-xs text-green-600 mt-3 pt-3 border-t border-green-200">
                        <div className="flex items-center justify-between">
                          <span>Total Executions: {selectedTask.executions.length}</span>
                          <span>Completed: {selectedTask.executions.filter(e => e.status === 'completed').length}</span>
                          <span>Progress: {Math.round(selectedTask.progress)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Summary */}
                {selectedTask.status === 'error' && (
                  <div className="bg-red-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-3 text-red-900">Error Summary</h4>
                    <div className="space-y-3">
                      <div className="text-sm text-red-700">
                        Task encountered errors. Here are the details:
                      </div>
                      
                      {/* Show error details */}
                      {selectedTask.executions.filter(exec => exec.status === 'failed' || exec.error_message).length > 0 && (
                        <div className="space-y-2">
                          {selectedTask.executions
                            .filter(exec => exec.status === 'failed' || exec.error_message)
                            .map((execution) => (
                              <div key={execution.id} className="bg-white p-3 rounded border border-red-200">
                                <div className="flex items-center gap-2 mb-2">
                                  {getAgentIcon(execution.agent_type)}
                                  <span className="text-sm font-medium text-red-800">
                                    {execution.agent_type} Error
                                  </span>
                                </div>
                                {execution.error_message && (
                                  <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                                    {execution.error_message}
                                  </div>
                                )}
                              </div>
                            ))}
                        </div>
                      )}
                      
                      {/* Summary */}
                      <div className="text-xs text-red-600 mt-3 pt-3 border-t border-red-200">
                        <div className="flex items-center justify-between">
                          <span>Total Executions: {selectedTask.executions.length}</span>
                          <span>Failed: {selectedTask.executions.filter(e => e.status === 'failed').length}</span>
                          <span>Progress: {Math.round(selectedTask.progress)}%</span>
                        </div>
                      </div>
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