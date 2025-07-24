import axios from 'axios';
import toast from 'react-hot-toast';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5001',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      toast.error('Rate limit exceeded. Please try again later.');
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please check your connection.');
    } else if (!error.response) {
      toast.error('Network error. Please check your connection.');
    }
    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Authentication
  login: (credentials) => apiClient.post('/api/v1/auth/login', credentials),
  register: (userData) => apiClient.post('/api/v1/auth/register', userData),
  getProfile: () => apiClient.get('/api/v1/auth/profile'),
  
  // System
  getHealth: () => apiClient.get('/api/v1/health'),
  getMetrics: () => apiClient.get('/api/v1/metrics'),
  getCacheStats: () => apiClient.get('/api/v1/cache/stats'),
  
  // Prometheus
  getPrometheusMetrics: () => apiClient.get('/api/v1/prometheus'),
};

export { apiClient };
export default api;
