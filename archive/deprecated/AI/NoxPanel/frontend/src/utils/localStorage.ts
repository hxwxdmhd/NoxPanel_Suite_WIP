/*
Theme Persistence and User Preferences Storage
Enterprise-grade localStorage management with ADHD-optimized themes
*/

// Theme types and interfaces
export interface ADHDTheme {
  id: string;
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  typography: {
    fontFamily: string;
    fontSize: string;
    lineHeight: string;
    fontWeight: string;
  };
  spacing: {
    compact: boolean;
    borderRadius: string;
    padding: string;
    margin: string;
  };
  animations: {
    enabled: boolean;
    duration: string;
    easing: string;
  };
  accessibility: {
    highContrast: boolean;
    focusVisible: boolean;
    reducedMotion: boolean;
  };
}

export interface UserPreferences {
  selectedTheme: string;
  customTheme?: Partial<ADHDTheme>;
  dashboard: {
    layout: 'grid' | 'list' | 'compact';
    refreshInterval: number;
    autoRefresh: boolean;
    showNotifications: boolean;
  };
  accessibility: {
    fontSize: 'small' | 'medium' | 'large' | 'extra-large';
    highContrast: boolean;
    reducedMotion: boolean;
    screenReader: boolean;
  };
  performance: {
    enableAnimations: boolean;
    enableCharts: boolean;
    maxDataPoints: number;
    cacheTimeout: number;
  };
  notifications: {
    desktop: boolean;
    sound: boolean;
    email: boolean;
    criticalOnly: boolean;
  };
  privacy: {
    analyticsEnabled: boolean;
    crashReporting: boolean;
    usageStatistics: boolean;
  };
  lastUpdated: string;
  version: string;
}

// Default ADHD-optimized themes
export const DEFAULT_THEMES: Record<string, ADHDTheme> = {
  focus_blue: {
    id: 'focus_blue',
    name: 'Focus Blue',
    description: 'Calming blue tones for deep focus and concentration',
    colors: {
      primary: '#0369a1',
      secondary: '#0284c7',
      accent: '#0ea5e9',
      background: '#f8fafc',
      surface: '#ffffff',
      text: '#1e293b',
      textSecondary: '#64748b',
      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      info: '#0284c7'
    },
    typography: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '16px',
      lineHeight: '1.6',
      fontWeight: '400'
    },
    spacing: {
      compact: false,
      borderRadius: '8px',
      padding: '1rem',
      margin: '1rem'
    },
    animations: {
      enabled: true,
      duration: '200ms',
      easing: 'ease-in-out'
    },
    accessibility: {
      highContrast: false,
      focusVisible: true,
      reducedMotion: false
    }
  },

  energy_orange: {
    id: 'energy_orange',
    name: 'Energy Orange',
    description: 'Vibrant orange palette for motivation and energy',
    colors: {
      primary: '#ea580c',
      secondary: '#f97316',
      accent: '#fb923c',
      background: '#fffbeb',
      surface: '#ffffff',
      text: '#1c1917',
      textSecondary: '#78716c',
      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      info: '#0284c7'
    },
    typography: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '16px',
      lineHeight: '1.5',
      fontWeight: '500'
    },
    spacing: {
      compact: false,
      borderRadius: '12px',
      padding: '1.25rem',
      margin: '1rem'
    },
    animations: {
      enabled: true,
      duration: '150ms',
      easing: 'ease-out'
    },
    accessibility: {
      highContrast: false,
      focusVisible: true,
      reducedMotion: false
    }
  },

  calm_green: {
    id: 'calm_green',
    name: 'Calm Green',
    description: 'Soothing green theme for stress reduction',
    colors: {
      primary: '#059669',
      secondary: '#10b981',
      accent: '#34d399',
      background: '#f0fdf4',
      surface: '#ffffff',
      text: '#1f2937',
      textSecondary: '#6b7280',
      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      info: '#0284c7'
    },
    typography: {
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      fontSize: '15px',
      lineHeight: '1.7',
      fontWeight: '400'
    },
    spacing: {
      compact: true,
      borderRadius: '6px',
      padding: '0.875rem',
      margin: '0.75rem'
    },
    animations: {
      enabled: true,
      duration: '300ms',
      easing: 'ease-in-out'
    },
    accessibility: {
      highContrast: false,
      focusVisible: true,
      reducedMotion: false
    }
  },

  high_contrast: {
    id: 'high_contrast',
    name: 'High Contrast',
    description: 'Maximum contrast for better visibility and focus',
    colors: {
      primary: '#000000',
      secondary: '#333333',
      accent: '#0066cc',
      background: '#ffffff',
      surface: '#f8f9fa',
      text: '#000000',
      textSecondary: '#333333',
      success: '#006600',
      warning: '#cc6600',
      error: '#cc0000',
      info: '#0066cc'
    },
    typography: {
      fontFamily: '"SF Pro Text", -apple-system, BlinkMacSystemFont, sans-serif',
      fontSize: '18px',
      lineHeight: '1.8',
      fontWeight: '600'
    },
    spacing: {
      compact: false,
      borderRadius: '4px',
      padding: '1.5rem',
      margin: '1.25rem'
    },
    animations: {
      enabled: false,
      duration: '0ms',
      easing: 'linear'
    },
    accessibility: {
      highContrast: true,
      focusVisible: true,
      reducedMotion: true
    }
  },

  dark_mode: {
    id: 'dark_mode',
    name: 'Dark Focus',
    description: 'Dark theme optimized for low-light environments',
    colors: {
      primary: '#3b82f6',
      secondary: '#6366f1',
      accent: '#8b5cf6',
      background: '#0f172a',
      surface: '#1e293b',
      text: '#f1f5f9',
      textSecondary: '#94a3b8',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6'
    },
    typography: {
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      fontSize: '16px',
      lineHeight: '1.6',
      fontWeight: '400'
    },
    spacing: {
      compact: false,
      borderRadius: '8px',
      padding: '1rem',
      margin: '1rem'
    },
    animations: {
      enabled: true,
      duration: '200ms',
      easing: 'ease-in-out'
    },
    accessibility: {
      highContrast: false,
      focusVisible: true,
      reducedMotion: false
    }
  }
};

// Default user preferences
export const DEFAULT_PREFERENCES: UserPreferences = {
  selectedTheme: 'focus_blue',
  dashboard: {
    layout: 'grid',
    refreshInterval: 30000,
    autoRefresh: true,
    showNotifications: true
  },
  accessibility: {
    fontSize: 'medium',
    highContrast: false,
    reducedMotion: false,
    screenReader: false
  },
  performance: {
    enableAnimations: true,
    enableCharts: true,
    maxDataPoints: 1000,
    cacheTimeout: 300000
  },
  notifications: {
    desktop: true,
    sound: false,
    email: false,
    criticalOnly: false
  },
  privacy: {
    analyticsEnabled: true,
    crashReporting: true,
    usageStatistics: true
  },
  lastUpdated: new Date().toISOString(),
  version: '1.0.0'
};

// Storage keys
const STORAGE_KEYS = {
  USER_PREFERENCES: 'noxpanel_user_preferences',
  THEME_CUSTOMIZATIONS: 'noxpanel_theme_customizations',
  SESSION_DATA: 'noxpanel_session_data',
  OFFLINE_DATA: 'noxpanel_offline_data',
  CACHE_TIMESTAMPS: 'noxpanel_cache_timestamps'
} as const;

// Storage management class
class LocalStorageManager {
  private static instance: LocalStorageManager;
  private listeners: Map<string, Array<(data: any) => void>> = new Map();

  static getInstance(): LocalStorageManager {
    if (!LocalStorageManager.instance) {
      LocalStorageManager.instance = new LocalStorageManager();
    }
    return LocalStorageManager.instance;
  }

  // Generic storage methods with error handling
  setItem<T>(key: string, value: T): boolean {
    try {
      const serialized = JSON.stringify({
        data: value,
        timestamp: Date.now(),
        version: DEFAULT_PREFERENCES.version
      });

      localStorage.setItem(key, serialized);
      this.notifyListeners(key, value);
      return true;
    } catch (error) {
      console.error(`Failed to save to localStorage (${key}):`, error);

      // Try to free up space by clearing old cache
      this.clearExpiredCache();

      // Retry once
      try {
        const serialized = JSON.stringify({
          data: value,
          timestamp: Date.now(),
          version: DEFAULT_PREFERENCES.version
        });
        localStorage.setItem(key, serialized);
        this.notifyListeners(key, value);
        return true;
      } catch (retryError) {
        console.error(`Retry failed for localStorage (${key}):`, retryError);
        return false;
      }
    }
  }

  getItem<T>(key: string, defaultValue: T): T {
    try {
      const stored = localStorage.getItem(key);
      if (!stored) {
        return defaultValue;
      }

      const parsed = JSON.parse(stored);

      // Check version compatibility
      if (parsed.version && parsed.version !== DEFAULT_PREFERENCES.version) {
        console.warn(`Version mismatch for ${key}, using default`);
        return defaultValue;
      }

      return parsed.data as T;
    } catch (error) {
      console.error(`Failed to load from localStorage (${key}):`, error);
      return defaultValue;
    }
  }

  removeItem(key: string): boolean {
    try {
      localStorage.removeItem(key);
      this.notifyListeners(key, null);
      return true;
    } catch (error) {
      console.error(`Failed to remove from localStorage (${key}):`, error);
      return false;
    }
  }

  // Theme management
  saveUserPreferences(preferences: UserPreferences): boolean {
    const updatedPreferences = {
      ...preferences,
      lastUpdated: new Date().toISOString(),
      version: DEFAULT_PREFERENCES.version
    };

    return this.setItem(STORAGE_KEYS.USER_PREFERENCES, updatedPreferences);
  }

  getUserPreferences(): UserPreferences {
    return this.getItem(STORAGE_KEYS.USER_PREFERENCES, DEFAULT_PREFERENCES);
  }

  saveThemeCustomizations(customizations: Record<string, Partial<ADHDTheme>>): boolean {
    return this.setItem(STORAGE_KEYS.THEME_CUSTOMIZATIONS, customizations);
  }

  getThemeCustomizations(): Record<string, Partial<ADHDTheme>> {
    return this.getItem(STORAGE_KEYS.THEME_CUSTOMIZATIONS, {});
  }

  // Session data management
  saveSessionData(sessionData: any): boolean {
    return this.setItem(STORAGE_KEYS.SESSION_DATA, sessionData);
  }

  getSessionData(): any {
    return this.getItem(STORAGE_KEYS.SESSION_DATA, {});
  }

  // Offline data management
  saveOfflineData(data: any): boolean {
    const currentData = this.getOfflineData();
    const updatedData = {
      ...currentData,
      ...data,
      lastUpdated: new Date().toISOString()
    };

    return this.setItem(STORAGE_KEYS.OFFLINE_DATA, updatedData);
  }

  getOfflineData(): any {
    return this.getItem(STORAGE_KEYS.OFFLINE_DATA, {});
  }

  // Cache management
  setCacheData(key: string, data: any, ttl: number = 300000): boolean {
    const cacheKey = `cache_${key}`;
    const expiresAt = Date.now() + ttl;

    const success = this.setItem(cacheKey, { data, expiresAt });

    if (success) {
      // Update cache timestamps
      const timestamps = this.getCacheTimestamps();
      timestamps[key] = expiresAt;
      this.setItem(STORAGE_KEYS.CACHE_TIMESTAMPS, timestamps);
    }

    return success;
  }

  getCacheData(key: string): any | null {
    const cacheKey = `cache_${key}`;
    const cached = this.getItem<{ data: any; expiresAt: number } | null>(cacheKey, null);

    if (!cached) {
      return null;
    }

    if (Date.now() > cached.expiresAt) {
      this.removeItem(cacheKey);
      return null;
    }

    return cached.data;
  }

  getCacheTimestamps(): Record<string, number> {
    return this.getItem(STORAGE_KEYS.CACHE_TIMESTAMPS, {});
  }

  clearExpiredCache(): void {
    const timestamps = this.getCacheTimestamps();
    const now = Date.now();
    const updatedTimestamps: Record<string, number> = {};

    Object.entries(timestamps).forEach(([key, expiresAt]) => {
      if (now > expiresAt) {
        this.removeItem(`cache_${key}`);
      } else {
        updatedTimestamps[key] = expiresAt;
      }
    });

    this.setItem(STORAGE_KEYS.CACHE_TIMESTAMPS, updatedTimestamps);
  }

  // Storage info and cleanup
  getStorageInfo(): {
    used: number;
    available: number;
    quota: number;
    usage: number;
  } {
    let used = 0;

    try {
      // Calculate used storage
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          const value = localStorage.getItem(key);
          used += key.length + (value?.length || 0);
        }
      }

      // Estimate quota (5MB is typical for localStorage)
      const quota = 5 * 1024 * 1024; // 5MB in bytes
      const available = quota - used;
      const usage = (used / quota) * 100;

      return { used, available, quota, usage };
    } catch (error) {
      console.error('Failed to calculate storage info:', error);
      return { used: 0, available: 0, quota: 0, usage: 0 };
    }
  }

  clearAllData(): boolean {
    try {
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });

      // Clear cache data
      const timestamps = this.getCacheTimestamps();
      Object.keys(timestamps).forEach(key => {
        localStorage.removeItem(`cache_${key}`);
      });

      console.log('✅ All NoxPanel data cleared from localStorage');
      return true;
    } catch (error) {
      console.error('❌ Failed to clear localStorage:', error);
      return false;
    }
  }

  // Event listeners for storage changes
  addEventListener(key: string, callback: (data: any) => void): void {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key)!.push(callback);
  }

  removeEventListener(key: string, callback: (data: any) => void): void {
    const keyListeners = this.listeners.get(key);
    if (keyListeners) {
      const index = keyListeners.indexOf(callback);
      if (index > -1) {
        keyListeners.splice(index, 1);
      }
    }
  }

  private notifyListeners(key: string, data: any): void {
    const keyListeners = this.listeners.get(key);
    if (keyListeners) {
      keyListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Storage listener error for ${key}:`, error);
        }
      });
    }
  }
}

// Singleton instance
export const storageManager = LocalStorageManager.getInstance();

// React hooks for storage integration
export const useLocalStorage = <T>(
  key: string,
  defaultValue: T
): [T, (value: T) => void] => {
  const [storedValue, setStoredValue] = React.useState<T>(() => {
    return storageManager.getItem(key, defaultValue);
  });

  const setValue = (value: T) => {
    try {
      setStoredValue(value);
      storageManager.setItem(key, value);
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  React.useEffect(() => {
    const handleStorageChange = (newValue: T) => {
      setStoredValue(newValue || defaultValue);
    };

    storageManager.addEventListener(key, handleStorageChange);

    return () => {
      storageManager.removeEventListener(key, handleStorageChange);
    };
  }, [key, defaultValue]);

  return [storedValue, setValue];
};

// Theme persistence hook
export const useThemePersistence = () => {
  const [preferences, setPreferences] = useLocalStorage(
    STORAGE_KEYS.USER_PREFERENCES,
    DEFAULT_PREFERENCES
  );

  const updateTheme = (themeId: string) => {
    const updatedPreferences = {
      ...preferences,
      selectedTheme: themeId,
      lastUpdated: new Date().toISOString()
    };
    setPreferences(updatedPreferences);
  };

  const updatePreferences = (updates: Partial<UserPreferences>) => {
    const updatedPreferences = {
      ...preferences,
      ...updates,
      lastUpdated: new Date().toISOString()
    };
    setPreferences(updatedPreferences);
  };

  const getCurrentTheme = (): ADHDTheme => {
    const baseTheme = DEFAULT_THEMES[preferences.selectedTheme] || DEFAULT_THEMES.focus_blue;
    const customizations = storageManager.getThemeCustomizations();
    const themeCustomization = customizations[preferences.selectedTheme];

    if (themeCustomization) {
      return {
        ...baseTheme,
        ...themeCustomization,
        colors: { ...baseTheme.colors, ...(themeCustomization.colors || {}) },
        typography: { ...baseTheme.typography, ...(themeCustomization.typography || {}) },
        spacing: { ...baseTheme.spacing, ...(themeCustomization.spacing || {}) },
        animations: { ...baseTheme.animations, ...(themeCustomization.animations || {}) },
        accessibility: { ...baseTheme.accessibility, ...(themeCustomization.accessibility || {}) }
      };
    }

    return baseTheme;
  };

  const saveThemeCustomization = (themeId: string, customization: Partial<ADHDTheme>) => {
    const currentCustomizations = storageManager.getThemeCustomizations();
    const updatedCustomizations = {
      ...currentCustomizations,
      [themeId]: customization
    };
    storageManager.saveThemeCustomizations(updatedCustomizations);
  };

  return {
    preferences,
    updateTheme,
    updatePreferences,
    getCurrentTheme,
    saveThemeCustomization,
    availableThemes: DEFAULT_THEMES
  };
};

// Cache hook for API data
export const useCache = () => {
  const setCacheData = (key: string, data: any, ttl: number = 300000) => {
    return storageManager.setCacheData(key, data, ttl);
  };

  const getCacheData = (key: string) => {
    return storageManager.getCacheData(key);
  };

  const clearCache = () => {
    storageManager.clearExpiredCache();
  };

  const getStorageInfo = () => {
    return storageManager.getStorageInfo();
  };

  return {
    setCacheData,
    getCacheData,
    clearCache,
    getStorageInfo
  };
};

// Export storage manager and default values
export { storageManager as default, STORAGE_KEYS };

// Add React import for hooks
import React from 'react';
