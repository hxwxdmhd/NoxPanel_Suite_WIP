// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
  timestamp: string;
  requestId: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  field?: string;
  statusCode: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
  filters?: Record<string, any>;
}

// HTTP Methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

// API Request Configuration
export interface ApiRequestConfig {
  method: HttpMethod;
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

// File Upload Types
export interface FileUploadResponse {
  fileId: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  url: string;
  thumbnail?: string;
  metadata?: Record<string, any>;
}

export interface FileUploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  speed: number;
  timeRemaining: number;
}

// Validation Types
export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: any;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

// Cache Types
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

export interface CacheOptions {
  ttl?: number;
  force?: boolean;
  background?: boolean;
}

// Rate Limiting
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
  retryAfter?: number;
}

// Health Check
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  services: ServiceHealth[];
  metrics: SystemMetrics;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime: number;
  lastCheck: string;
  error?: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    inbound: number;
    outbound: number;
  };
}

// WebSocket Types
export interface WebSocketMessage<T = any> {
  id: string;
  type: string;
  data: T;
  timestamp: string;
  sender?: string;
  target?: string;
}

export interface WebSocketEvent {
  type: string;
  payload: any;
  timestamp: Date;
}

export interface WebSocketConnection {
  id: string;
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  url: string;
  protocols?: string[];
  lastPing?: Date;
  lastPong?: Date;
}

// Search Types
export interface SearchParams {
  query: string;
  filters?: SearchFilter[];
  sort?: SearchSort[];
  pagination?: PaginationParams;
  facets?: string[];
}

export interface SearchFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'contains' | 'startsWith' | 'endsWith';
  value: any;
  type?: 'string' | 'number' | 'boolean' | 'date' | 'array';
}

export interface SearchSort {
  field: string;
  order: 'asc' | 'desc';
  priority?: number;
}

export interface SearchResult<T> {
  items: T[];
  total: number;
  facets?: SearchFacet[];
  suggestions?: string[];
  executionTime: number;
}

export interface SearchFacet {
  field: string;
  values: SearchFacetValue[];
}

export interface SearchFacetValue {
  value: string;
  count: number;
  selected: boolean;
}

// Export/Import Types
export interface ExportRequest {
  format: 'csv' | 'xlsx' | 'json' | 'pdf';
  filters?: Record<string, any>;
  fields?: string[];
  options?: ExportOptions;
}

export interface ExportOptions {
  includeHeaders?: boolean;
  dateFormat?: string;
  timezone?: string;
  delimiter?: string;
  encoding?: string;
}

export interface ExportResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  filename?: string;
  size?: number;
  createdAt: string;
  completedAt?: string;
  error?: string;
}

// Audit Types
export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  success: boolean;
  error?: string;
}

export interface AuditFilter {
  userId?: string;
  action?: string;
  resource?: string;
  startDate?: Date;
  endDate?: Date;
  success?: boolean;
}