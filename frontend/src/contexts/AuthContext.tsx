import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useAuthStore } from '@/store/authStore';
import { User } from '@/types/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: { email: string; password: string; rememberMe?: boolean }) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  updateUser: (userData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
    updateUser,
    checkSession,
  } = useAuthStore();

  useEffect(() => {
    // Check session validity on mount
    if (isAuthenticated) {
      checkSession().catch(() => {
        logout();
      });
    }
  }, [isAuthenticated, checkSession, logout]);

  // ADHD-friendly: Auto-save user preferences
  useEffect(() => {
    if (user && isAuthenticated) {
      const handleAutoSave = () => {
        // Auto-save any pending changes
        const pendingChanges = sessionStorage.getItem('pending-user-changes');
        if (pendingChanges) {
          try {
            const changes = JSON.parse(pendingChanges);
            updateUser(changes);
            sessionStorage.removeItem('pending-user-changes');
            
            // Show auto-save indicator
            if (typeof document !== 'undefined') {
              document.dispatchEvent(new CustomEvent('auto-save-complete'));
            }
          } catch (error) {
            console.error('Auto-save failed:', error);
          }
        }
      };

      // Listen for auto-save events
      document.addEventListener('auto-save', handleAutoSave);
      
      // Auto-save on visibility change (user switching tabs)
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
          handleAutoSave();
        }
      });

      return () => {
        document.removeEventListener('auto-save', handleAutoSave);
      };
    }
  }, [user, isAuthenticated, updateUser]);

  // Error handling with screen reader announcements
  useEffect(() => {
    if (error) {
      // Announce error to screen readers
      if (typeof window !== 'undefined') {
        const announcement = `Authentication error: ${error}`;
        (window as any).announceToScreenReader?.(announcement);
      }
    }
  }, [error]);

  // Session timeout warning for ADHD users (more time to respond)
  useEffect(() => {
    if (isAuthenticated) {
      let timeoutWarning: NodeJS.Timeout;
      let sessionTimeout: NodeJS.Timeout;

      const resetTimers = () => {
        clearTimeout(timeoutWarning);
        clearTimeout(sessionTimeout);

        // Show warning 10 minutes before session expires (extended for ADHD users)
        timeoutWarning = setTimeout(() => {
          if (typeof window !== 'undefined') {
            const announcement = 'Your session will expire in 10 minutes. Any unsaved changes will be automatically saved.';
            (window as any).announceToScreenReader?.(announcement);
          }
          
          // Dispatch session warning event
          document.dispatchEvent(new CustomEvent('session-warning', {
            detail: { timeRemaining: 10 * 60 * 1000 }
          }));
        }, 50 * 60 * 1000); // 50 minutes (10 minutes before 60-minute session)

        // Auto-logout after session expires
        sessionTimeout = setTimeout(() => {
          logout();
        }, 60 * 60 * 1000); // 60 minutes
      };

      // Reset timers on user activity
      const activities = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
      
      const resetOnActivity = () => resetTimers();
      
      activities.forEach(activity => {
        document.addEventListener(activity, resetOnActivity, true);
      });

      // Initial timer setup
      resetTimers();

      return () => {
        clearTimeout(timeoutWarning);
        clearTimeout(sessionTimeout);
        activities.forEach(activity => {
          document.removeEventListener(activity, resetOnActivity, true);
        });
      };
    }
  }, [isAuthenticated, logout]);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};