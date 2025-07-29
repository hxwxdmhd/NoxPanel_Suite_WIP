import React, { createContext, useContext, ReactNode, useCallback } from 'react';
import { toast, Toaster } from 'react-hot-toast';
import { useAccessibility } from './AccessibilityContext';

interface NotificationContextType {
  // Basic notifications
  showSuccess: (message: string, options?: NotificationOptions) => void;
  showError: (message: string, options?: NotificationOptions) => void;
  showWarning: (message: string, options?: NotificationOptions) => void;
  showInfo: (message: string, options?: NotificationOptions) => void;
  
  // ADHD-friendly notifications
  showPersistent: (message: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
  showAutoSave: (message?: string) => void;
  showSecurityAlert: (message: string, severity?: 'low' | 'medium' | 'high' | 'critical') => void;
  
  // Notification management
  dismiss: (toastId?: string) => void;
  dismissAll: () => void;
  
  // Queue management for ADHD users
  showQueuedNotification: (message: string, type: 'success' | 'error' | 'warning' | 'info', delay?: number) => void;
  clearQueue: () => void;
}

interface NotificationOptions {
  duration?: number;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  persistent?: boolean;
  sound?: boolean;
  screenReader?: boolean;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const { announceToScreenReader, playSound, soundEnabled } = useAccessibility();
  
  // Queue for managing multiple notifications (ADHD-friendly)
  const [notificationQueue, setNotificationQueue] = React.useState<Array<{
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    delay: number;
  }>>([]);

  // Process notification queue with delays
  React.useEffect(() => {
    if (notificationQueue.length > 0) {
      const [first, ...rest] = notificationQueue;
      
      const timer = setTimeout(() => {
        // Show the notification
        showBasicNotification(first.message, first.type);
        
        // Remove from queue
        setNotificationQueue(rest);
      }, first.delay);

      return () => clearTimeout(timer);
    }
  }, [notificationQueue]);

  const showBasicNotification = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info') => {
    const toastOptions = {
      duration: 4000,
      position: 'top-right' as const,
      style: {
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '500',
        padding: '12px 16px',
        maxWidth: '400px',
      },
    };

    switch (type) {
      case 'success':
        toast.success(message, {
          ...toastOptions,
          icon: '✅',
          style: {
            ...toastOptions.style,
            background: '#10b981',
            color: '#ffffff',
          },
        });
        if (soundEnabled) playSound('success');
        break;
        
      case 'error':
        toast.error(message, {
          ...toastOptions,
          duration: 6000, // Longer duration for errors
          icon: '❌',
          style: {
            ...toastOptions.style,
            background: '#ef4444',
            color: '#ffffff',
          },
        });
        if (soundEnabled) playSound('error');
        break;
        
      case 'warning':
        toast(message, {
          ...toastOptions,
          duration: 5000,
          icon: '⚠️',
          style: {
            ...toastOptions.style,
            background: '#f59e0b',
            color: '#ffffff',
          },
        });
        if (soundEnabled) playSound('notification');
        break;
        
      case 'info':
        toast(message, {
          ...toastOptions,
          icon: 'ℹ️',
          style: {
            ...toastOptions.style,
            background: '#3b82f6',
            color: '#ffffff',
          },
        });
        if (soundEnabled) playSound('notification');
        break;
    }

    // Announce to screen readers
    announceToScreenReader(`${type}: ${message}`);
  }, [announceToScreenReader, playSound, soundEnabled]);

  const showSuccess = useCallback((message: string, options: NotificationOptions = {}) => {
    if (options.persistent) {
      toast.success(message, { duration: Infinity });
    } else {
      showBasicNotification(message, 'success');
    }
    
    if (options.screenReader !== false) {
      announceToScreenReader(`Success: ${message}`);
    }
  }, [showBasicNotification, announceToScreenReader]);

  const showError = useCallback((message: string, options: NotificationOptions = {}) => {
    if (options.persistent) {
      toast.error(message, { duration: Infinity });
    } else {
      showBasicNotification(message, 'error');
    }
    
    if (options.screenReader !== false) {
      announceToScreenReader(`Error: ${message}`);
    }
  }, [showBasicNotification, announceToScreenReader]);

  const showWarning = useCallback((message: string, options: NotificationOptions = {}) => {
    if (options.persistent) {
      toast(message, { 
        duration: Infinity,
        icon: '⚠️',
        style: { background: '#f59e0b', color: '#ffffff' }
      });
    } else {
      showBasicNotification(message, 'warning');
    }
    
    if (options.screenReader !== false) {
      announceToScreenReader(`Warning: ${message}`);
    }
  }, [showBasicNotification, announceToScreenReader]);

  const showInfo = useCallback((message: string, options: NotificationOptions = {}) => {
    if (options.persistent) {
      toast(message, { 
        duration: Infinity,
        icon: 'ℹ️',
        style: { background: '#3b82f6', color: '#ffffff' }
      });
    } else {
      showBasicNotification(message, 'info');
    }
    
    if (options.screenReader !== false) {
      announceToScreenReader(`Information: ${message}`);
    }
  }, [showBasicNotification, announceToScreenReader]);

  const showPersistent = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    const styles = {
      success: { background: '#10b981', color: '#ffffff' },
      error: { background: '#ef4444', color: '#ffffff' },
      warning: { background: '#f59e0b', color: '#ffffff' },
      info: { background: '#3b82f6', color: '#ffffff' },
    };

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
    };

    toast(message, {
      duration: Infinity,
      icon: icons[type],
      style: {
        ...styles[type],
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '500',
        padding: '12px 16px',
        maxWidth: '400px',
      },
    });

    announceToScreenReader(`Persistent ${type}: ${message}`);
    if (soundEnabled) playSound(type === 'success' ? 'success' : type === 'error' ? 'error' : 'notification');
  }, [announceToScreenReader, playSound, soundEnabled]);

  const showAutoSave = useCallback((message: string = 'Changes saved automatically') => {
    toast(message, {
      duration: 2000,
      icon: '💾',
      style: {
        background: '#10b981',
        color: '#ffffff',
        borderRadius: '8px',
        fontSize: '12px',
        padding: '8px 12px',
      },
      position: 'bottom-right',
    });

    announceToScreenReader(message);
    if (soundEnabled) playSound('success');
  }, [announceToScreenReader, playSound, soundEnabled]);

  const showSecurityAlert = useCallback((message: string, severity: 'low' | 'medium' | 'high' | 'critical' = 'medium') => {
    const colors = {
      low: '#3b82f6',     // Blue
      medium: '#f59e0b',  // Orange
      high: '#ef4444',    // Red
      critical: '#dc2626', // Dark Red
    };

    const icons = {
      low: '🔒',
      medium: '⚠️',
      high: '🚨',
      critical: '🚨',
    };

    const duration = severity === 'critical' ? Infinity : severity === 'high' ? 10000 : 6000;

    toast(message, {
      duration,
      icon: icons[severity],
      style: {
        background: colors[severity],
        color: '#ffffff',
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '600',
        padding: '16px',
        maxWidth: '500px',
        border: '2px solid #ffffff',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
      },
      position: 'top-center',
    });

    // High priority screen reader announcement
    announceToScreenReader(`Security alert, ${severity} priority: ${message}`);
    
    // Play error sound for medium and above
    if (soundEnabled && ['medium', 'high', 'critical'].includes(severity)) {
      playSound('error');
    }

    // Dispatch security alert event
    document.dispatchEvent(new CustomEvent('security-alert-shown', {
      detail: { message, severity }
    }));
  }, [announceToScreenReader, playSound, soundEnabled]);

  const dismiss = useCallback((toastId?: string) => {
    if (toastId) {
      toast.dismiss(toastId);
    } else {
      toast.dismiss();
    }
  }, []);

  const dismissAll = useCallback(() => {
    toast.dismiss();
    setNotificationQueue([]);
    announceToScreenReader('All notifications dismissed');
  }, [announceToScreenReader]);

  const showQueuedNotification = useCallback((
    message: string, 
    type: 'success' | 'error' | 'warning' | 'info', 
    delay: number = 0
  ) => {
    const id = Math.random().toString(36).substring(7);
    
    setNotificationQueue(prev => [...prev, {
      id,
      message,
      type,
      delay,
    }]);
  }, []);

  const clearQueue = useCallback(() => {
    setNotificationQueue([]);
    announceToScreenReader('Notification queue cleared');
  }, [announceToScreenReader]);

  // Global keyboard shortcut to dismiss all notifications (ADHD-friendly)
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+Shift+D to dismiss all notifications
      if (event.ctrlKey && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        dismissAll();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [dismissAll]);

  const value: NotificationContextType = {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showPersistent,
    showAutoSave,
    showSecurityAlert,
    dismiss,
    dismissAll,
    showQueuedNotification,
    clearQueue,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};