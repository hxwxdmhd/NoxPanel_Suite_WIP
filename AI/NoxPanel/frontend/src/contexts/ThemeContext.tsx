import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../services/api';

export interface Theme {
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
  };
  animations: {
    speed: string;
    hover_scale: string;
    transition_duration: string;
  };
  spacing: {
    padding: string;
    margins: string;
  };
  accessibility: {
    high_contrast: boolean;
    focus_indicators: string;
    animation_reduced: boolean;
  };
}

export interface ThemeContextType {
  currentTheme: string;
  themeConfig: Theme | null;
  availableThemes: string[];
  switchTheme: (themeName: string) => Promise<void>;
  isLoading: boolean;
  preferences: UserPreferences;
  updatePreferences: (prefs: Partial<UserPreferences>) => Promise<void>;
}

export interface UserPreferences {
  animation_speed: 'slow' | 'normal' | 'fast';
  contrast: 'low' | 'normal' | 'high';
  font_size: 'small' | 'normal' | 'large';
  compact_mode: boolean;
  auto_theme: boolean;
  notifications: boolean;
}

const defaultPreferences: UserPreferences = {
  animation_speed: 'normal',
  contrast: 'normal',
  font_size: 'normal',
  compact_mode: false,
  auto_theme: false,
  notifications: true,
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState<string>('steady');
  const [themeConfig, setThemeConfig] = useState<Theme | null>(null);
  const [availableThemes, setAvailableThemes] = useState<string[]>(['spicy', 'steady']);
  const [isLoading, setIsLoading] = useState(true);
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);

  // Load theme configuration on mount
  useEffect(() => {
    loadThemeConfig();
  }, [currentTheme]);

  // Apply CSS variables when theme changes
  useEffect(() => {
    if (themeConfig) {
      applyThemeToDOM(themeConfig);
    }
  }, [themeConfig]);

  const loadThemeConfig = async () => {
    try {
      setIsLoading(true);

      // Get current theme from API
      const themeResponse = await api.get('/api/theme');
      const currentThemeName = themeResponse.data.theme;
      setCurrentTheme(currentThemeName);

      // Get theme configuration
      const configResponse = await api.get('/ui/theme/config');
      setThemeConfig(configResponse.data.config);
      setAvailableThemes(configResponse.data.available_themes);

      // Get user preferences
      const profileResponse = await api.get('/api/profile');
      setPreferences({ ...defaultPreferences, ...profileResponse.data.profile.preferences });

    } catch (error) {
      console.error('Failed to load theme configuration:', error);
      // Use fallback theme
      setCurrentTheme('steady');
    } finally {
      setIsLoading(false);
    }
  };

  const switchTheme = async (themeName: string): Promise<void> => {
    try {
      setIsLoading(true);

      // Update theme on server
      await api.post('/api/theme', { theme: themeName });

      // Get new theme configuration
      const configResponse = await api.get(`/ui/theme/preview/${themeName}`);

      setCurrentTheme(themeName);
      setThemeConfig(configResponse.data.config);

      // Show success message
      if (window.toast) {
        window.toast.success(`Switched to ${themeName} mode`);
      }

    } catch (error) {
      console.error('Failed to switch theme:', error);
      if (window.toast) {
        window.toast.error('Failed to switch theme');
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const updatePreferences = async (prefs: Partial<UserPreferences>): Promise<void> => {
    try {
      const updatedPreferences = { ...preferences, ...prefs };

      // Update on server
      await api.post('/api/profile', { preferences: updatedPreferences });

      // Update local state
      setPreferences(updatedPreferences);

      // Apply preference-based styling
      applyPreferencesToDOM(updatedPreferences);

      if (window.toast) {
        window.toast.success('Preferences updated');
      }

    } catch (error) {
      console.error('Failed to update preferences:', error);
      if (window.toast) {
        window.toast.error('Failed to update preferences');
      }
      throw error;
    }
  };

  const applyThemeToDOM = (theme: Theme) => {
    const root = document.documentElement;

    // Apply color variables
    root.style.setProperty('--primary-color', theme.colors.primary);
    root.style.setProperty('--secondary-color', theme.colors.secondary);
    root.style.setProperty('--accent-color', theme.colors.accent);
    root.style.setProperty('--background-color', theme.colors.background);
    root.style.setProperty('--surface-color', theme.colors.surface);
    root.style.setProperty('--text-color', theme.colors.text);

    // Apply animation variables
    root.style.setProperty('--animation-speed', theme.animations.speed);
    root.style.setProperty('--hover-scale', theme.animations.hover_scale);
    root.style.setProperty('--transition-duration', theme.animations.transition_duration);

    // Apply theme class
    document.body.className = `${currentTheme}-mode`;

    // Apply accessibility settings
    if (theme.accessibility.animation_reduced) {
      root.style.setProperty('--animation-duration', '0.1s');
    }

    if (theme.accessibility.high_contrast) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
  };

  const applyPreferencesToDOM = (prefs: UserPreferences) => {
    const root = document.documentElement;

    // Font size
    const fontSizeMap = {
      small: '0.875rem',
      normal: '1rem',
      large: '1.125rem'
    };
    root.style.setProperty('--base-font-size', fontSizeMap[prefs.font_size]);

    // Animation speed
    const animationSpeedMap = {
      slow: '0.5s',
      normal: '0.3s',
      fast: '0.15s'
    };
    root.style.setProperty('--animation-duration', animationSpeedMap[prefs.animation_speed]);

    // Contrast
    if (prefs.contrast === 'high') {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }

    // Compact mode
    if (prefs.compact_mode) {
      document.body.classList.add('compact-mode');
    } else {
      document.body.classList.remove('compact-mode');
    }
  };

  const contextValue: ThemeContextType = {
    currentTheme,
    themeConfig,
    availableThemes,
    switchTheme,
    isLoading,
    preferences,
    updatePreferences,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Extend window interface for toast notifications
declare global {
  interface Window {
    toast: {
      success: (message: string) => void;
      error: (message: string) => void;
      info: (message: string) => void;
    };
  }
}
