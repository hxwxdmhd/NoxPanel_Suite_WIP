import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// API configuration
const API_BASE_URL = 'http://127.0.0.1:5002';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Important for session-based auth
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add any auth tokens or additional headers here
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private handleApiError(error: any) {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.error || error.response.statusText;

      switch (status) {
        case 401:
          toast.error('Authentication required');
          // Redirect to login if needed
          break;
        case 403:
          toast.error('Access forbidden');
          break;
        case 404:
          toast.error('Resource not found');
          break;
        case 500:
          toast.error('Server error occurred');
          break;
        default:
          toast.error(`Error: ${message}`);
      }
    } else if (error.request) {
      // Request made but no response
      toast.error('Network error - check your connection');
    } else {
      // Something else happened
      toast.error('An unexpected error occurred');
    }
  }

  // Generic API methods
  async get<T = any>(url: string, params?: any): Promise<AxiosResponse<T>> {
    return this.api.get(url, { params });
  }

  async post<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.api.post(url, data);
  }

  async put<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.api.put(url, data);
  }

  async delete<T = any>(url: string): Promise<AxiosResponse<T>> {
    return this.api.delete(url);
  }

  // Specific API endpoints
  async getDashboard() {
    return this.get('/api/dashboard');
  }

  async getStatus() {
    return this.get('/api/status');
  }

  async getScripts() {
    return this.get('/api/scripts');
  }

  async executeScript(scriptPath: string, args: string[] = []) {
    return this.post('/api/scripts/execute', {
      script_path: scriptPath,
      args: args,
    });
  }

  async getExecutionHistory(limit: number = 20) {
    return this.get('/api/scripts/history', { limit });
  }

  async getMetrics() {
    return this.get('/api/metrics');
  }

  async getMetricsHistory(hours: number = 24) {
    return this.get('/api/metrics/history', { hours });
  }

  async getTheme() {
    return this.get('/api/theme');
  }

  async setTheme(theme: string) {
    return this.post('/api/theme', { theme });
  }

  async getProfile() {
    return this.get('/api/profile');
  }

  async updateProfile(data: any) {
    return this.post('/api/profile', data);
  }

  async askLLM(question: string, context: string = '', model: string = 'llama2') {
    return this.post('/api/llm/ask', {
      question,
      context,
      model,
    });
  }

  async getSystemInfo() {
    return this.get('/api/system/info');
  }

  async optimizeSystem() {
    return this.post('/api/system/optimize');
  }

  async getSecurityEvents(limit: number = 100) {
    return this.get('/api/security/events', { limit });
  }

  async getThemeConfig() {
    return this.get('/ui/theme/config');
  }

  async previewTheme(themeName: string) {
    return this.get(`/ui/theme/preview/${themeName}`);
  }

  async updatePreferences(preferences: any) {
    return this.post('/ui/preferences/update', preferences);
  }

  // WebSocket connection for real-time data
  createWebSocket(endpoint: string): WebSocket {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + endpoint;
    return new WebSocket(wsUrl);
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.get('/status');
      return response.data;
    } catch (error) {
      return { status: 'offline', error: error.message };
    }
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const api = new ApiService();

// Export types for use in components
export interface Script {
  name: string;
  path: string;
  type: string;
  size: number;
  modified: string;
  description: string;
  tags: string[];
}

export interface ExecutionResult {
  success: boolean;
  output: string;
  error?: string;
  execution_time: number;
  timestamp: string;
  user: string;
  args: string[];
}

export interface SystemMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_usage: number;
  active_connections: number;
  uptime: string;
  network_io: {
    bytes_sent: number;
    bytes_recv: number;
  };
}

export interface SecurityEvent {
  timestamp: string;
  event_type: string;
  severity: string;
  description: string;
  source_ip: string;
  user_agent: string;
  action_taken: string;
}

export interface LLMResponse {
  success: boolean;
  response: string;
  model: string;
  timestamp: string;
  error?: string;
  fallback_response?: string;
}

export interface DashboardStats {
  cpu_usage: number;
  memory_usage: number;
  active_connections: number;
  scripts_executed: number;
  uptime: string;
}

export interface ActivityItem {
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  timestamp: string;
}

export interface SystemHealth {
  database: 'good' | 'warning' | 'critical';
  network: 'good' | 'warning' | 'critical';
  storage: 'good' | 'warning' | 'critical';
  services: 'good' | 'warning' | 'critical';
}

export interface DashboardData {
  stats: DashboardStats;
  recent_activity: ActivityItem[];
}

export interface StatusData {
  health: SystemHealth;
  version: string;
  last_updated: string;
}

export default api;
