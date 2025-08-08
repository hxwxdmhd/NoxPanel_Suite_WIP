import React, { createContext, useContext, useEffect, useRef, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { useAccessibility } from './AccessibilityContext';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  connectionError: string | null;
  emit: (event: string, data?: any) => void;
  on: (event: string, callback: (data: any) => void) => () => void;
  off: (event: string, callback?: (data: any) => void) => void;
  connect: () => void;
  disconnect: () => void;
}

const SocketContext = createContext<SocketContextType | null>(null);

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

interface SocketProviderProps {
  children: ReactNode;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);
  const [connectionError, setConnectionError] = React.useState<string | null>(null);
  
  const { isAuthenticated, user } = useAuth();
  const { announceToScreenReader, playSound } = useAccessibility();

  const connect = React.useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    try {
      const socketUrl = process.env.REACT_APP_SOCKET_URL || 'ws://localhost:5001';
      
      socketRef.current = io(socketUrl, {
        transports: ['websocket', 'polling'],
        timeout: 20000,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        auth: {
          userId: user?.id,
          token: localStorage.getItem('accessToken'),
        },
        forceNew: false,
      });

      const socket = socketRef.current;

      socket.on('connect', () => {
        setIsConnected(true);
        setConnectionError(null);
        
        announceToScreenReader('Connected to real-time updates');
        playSound('success');
        
        // Join user-specific room for notifications
        if (user?.id) {
          socket.emit('join-user-room', user.id);
        }
      });

      socket.on('disconnect', (reason) => {
        setIsConnected(false);
        console.log('Socket disconnected:', reason);
        
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, try to reconnect
          socket.connect();
        }
        
        announceToScreenReader('Disconnected from real-time updates');
      });

      socket.on('connect_error', (error) => {
        setConnectionError(error.message);
        setIsConnected(false);
        console.error('Socket connection error:', error);
        
        announceToScreenReader('Connection error occurred');
        playSound('error');
      });

      socket.on('reconnect', (attemptNumber) => {
        setIsConnected(true);
        setConnectionError(null);
        
        announceToScreenReader(`Reconnected to real-time updates after ${attemptNumber} attempts`);
        playSound('success');
      });

      socket.on('reconnect_failed', () => {
        setConnectionError('Failed to reconnect after multiple attempts');
        announceToScreenReader('Failed to reconnect to real-time updates');
        playSound('error');
      });

      // Real-time event handlers for ADHD-friendly notifications
      socket.on('security-alert', (data) => {
        // High priority security alerts
        announceToScreenReader(`Security alert: ${data.message}`);
        playSound('error');
        
        // Dispatch event for UI components
        document.dispatchEvent(new CustomEvent('security-alert', { detail: data }));
      });

      socket.on('system-notification', (data) => {
        // General system notifications
        announceToScreenReader(`System notification: ${data.message}`);
        playSound('notification');
        
        document.dispatchEvent(new CustomEvent('system-notification', { detail: data }));
      });

      socket.on('plugin-status-change', (data) => {
        // Plugin status updates
        announceToScreenReader(`Plugin ${data.plugin} is now ${data.status}`);
        
        document.dispatchEvent(new CustomEvent('plugin-status-change', { detail: data }));
      });

      socket.on('dashboard-update', (data) => {
        // Dashboard metric updates
        document.dispatchEvent(new CustomEvent('dashboard-update', { detail: data }));
      });

      socket.on('user-activity', (data) => {
        // Other user activity (for admin users)
        if (user?.role?.name === 'admin') {
          document.dispatchEvent(new CustomEvent('user-activity', { detail: data }));
        }
      });

    } catch (error) {
      console.error('Socket initialization error:', error);
      setConnectionError('Failed to initialize connection');
    }
  }, [user, announceToScreenReader, playSound]);

  const disconnect = React.useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
      setConnectionError(null);
      
      announceToScreenReader('Disconnected from real-time updates');
    }
  }, [announceToScreenReader]);

  const emit = React.useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot emit event:', event);
    }
  }, []);

  const on = React.useCallback((event: string, callback: (data: any) => void) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback);
      
      // Return cleanup function
      return () => {
        socketRef.current?.off(event, callback);
      };
    }
    
    return () => {}; // No-op cleanup
  }, []);

  const off = React.useCallback((event: string, callback?: (data: any) => void) => {
    if (socketRef.current) {
      socketRef.current.off(event, callback);
    }
  }, []);

  // Connect when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, user, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Handle page visibility for ADHD users (reconnect when tab becomes active)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && isAuthenticated && !isConnected) {
        // Try to reconnect when user returns to tab
        setTimeout(connect, 1000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, isConnected, connect]);

  // Network status handling
  useEffect(() => {
    const handleOnline = () => {
      if (isAuthenticated && !isConnected) {
        announceToScreenReader('Network connection restored, reconnecting...');
        connect();
      }
    };

    const handleOffline = () => {
      announceToScreenReader('Network connection lost');
      setConnectionError('Network connection lost');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isAuthenticated, isConnected, connect, announceToScreenReader]);

  const value: SocketContextType = {
    socket: socketRef.current,
    isConnected,
    connectionError,
    emit,
    on,
    off,
    connect,
    disconnect,
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};