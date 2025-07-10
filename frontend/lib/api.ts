import axios from 'axios';
import type { 
  User, 
  UserCreate, 
  Task, 
  TaskRequest, 
  TaskResponse, 
  TaskStatus,
  Memory 
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Health check
  health: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // User endpoints
  createUser: async (user: UserCreate): Promise<User> => {
    const response = await api.post('/users', user);
    return response.data;
  },

  getUser: async (userId: number): Promise<User> => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },

  updateUserPreferences: async (userId: number, preferences: Record<string, any>) => {
    const response = await api.put(`/users/${userId}/preferences`, preferences);
    return response.data;
  },

  // Task endpoints
  createTask: async (taskRequest: TaskRequest): Promise<TaskResponse> => {
    const response = await api.post('/tasks', taskRequest);
    return response.data;
  },

  getTaskStatus: async (taskId: number): Promise<TaskStatus> => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  getTaskProgress: async (taskId: number) => {
    const response = await api.get(`/tasks/${taskId}/progress`);
    return response.data;
  },

  getUserTasks: async (userId: number): Promise<Task[]> => {
    const response = await api.get(`/users/${userId}/tasks`);
    return response.data;
  },

  // Memory endpoints
  storeMemory: async (
    userId: number,
    memoryType: string,
    key: string,
    value: Record<string, any>,
    importance: number = 5
  ) => {
    const response = await api.post(`/users/${userId}/memories`, {
      memory_type: memoryType,
      key,
      value,
      importance,
    });
    return response.data;
  },

  getUserMemories: async (userId: number, memoryType?: string): Promise<Memory[]> => {
    const params = memoryType ? { memory_type: memoryType } : {};
    const response = await api.get(`/users/${userId}/memories`, { params });
    return response.data;
  },

  // Demo endpoints
  demoCreateUser: async () => {
    const response = await api.post('/demo/create-user');
    return response.data;
  },

  demoCreateTask: async () => {
    const response = await api.post('/demo/task');
    return response.data;
  },

  demoGetTaskProgress: async (taskId: number) => {
    const response = await api.get(`/demo/tasks/${taskId}`);
    return response.data;
  },
};

export default apiClient; 