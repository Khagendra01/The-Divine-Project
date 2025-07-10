export interface User {
  id: number;
  username: string;
  email: string;
  preferences: Record<string, any>;
  created_at: string;
}

export interface UserCreate {
  username: string;
  email: string;
}

export interface Task {
  id: number;
  user_id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface TaskRequest {
  user_id: number;
  request: string;
  context?: Record<string, any>;
}

export interface TaskResponse {
  task_id: number;
  status: string;
  message: string;
  estimated_duration?: number;
}

export interface TaskStatus {
  task_id: number;
  status: string;
  progress: number;
  current_step?: string;
  subtasks: Subtask[];
  executions: AgentExecution[];
}

export interface Subtask {
  id: number;
  task_id: number;
  title: string;
  description: string;
  agent_type: string;
  order_index: number;
  status: string;
  created_at: string;
  completed_at?: string;
}

export interface AgentExecution {
  id: number;
  task_id: number;
  subtask_id?: number;
  agent_type: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  status: string;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface Memory {
  id: number;
  user_id: number;
  memory_type: string;
  key: string;
  value: Record<string, any>;
  importance: number;
  created_at: string;
  last_accessed: string;
} 