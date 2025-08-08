// Authentication Types
export interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  permissions: Permission[];
  avatar?: string;
  lastLogin?: Date;
  isActive: boolean;
  preferences: UserPreferences;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserRole {
  id: string;
  name: string;
  level: number;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  accessibility: AccessibilityPreferences;
  notifications: NotificationPreferences;
  dashboard: DashboardPreferences;
}

export interface AccessibilityPreferences {
  highContrast: boolean;
  reducedMotion: boolean;
  largeText: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
  autoSave: boolean;
  focusMode: boolean;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  desktop: boolean;
  sound: boolean;
  securityAlerts: boolean;
  systemUpdates: boolean;
  maintenanceNotices: boolean;
}

export interface DashboardPreferences {
  layout: 'grid' | 'list';
  compactMode: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  defaultView: string;
  pinnedWidgets: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
  twoFactorCode?: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  accessToken: string | null;
  refreshToken: string | null;
}

// Session Management
export interface Session {
  id: string;
  userId: string;
  deviceInfo: DeviceInfo;
  ipAddress: string;
  userAgent: string;
  isActive: boolean;
  lastActivity: Date;
  createdAt: Date;
  expiresAt: Date;
}

export interface DeviceInfo {
  type: 'desktop' | 'mobile' | 'tablet';
  os: string;
  browser: string;
  location?: GeoLocation;
}

export interface GeoLocation {
  country: string;
  region: string;
  city: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

// Password Management
export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface PasswordChangeRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}