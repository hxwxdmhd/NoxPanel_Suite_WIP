/*
Progressive Web App (PWA) Configuration with Offline Support
Enterprise-grade frontend persistence and offline capabilities
*/

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { toast } from 'react-toastify';

// Types for PWA state management
interface PWAState {
  isOnline: boolean;
  isInstallable: boolean;
  isInstalled: boolean;
  updateAvailable: boolean;
  syncQueue: SyncAction[];
  offlineActions: OfflineAction[];
  lastSync: Date | null;
  installPrompt: any;
}

interface SyncAction {
  id: string;
  type: string;
  data: any;
  timestamp: Date;
  retryCount: number;
}

interface OfflineAction {
  id: string;
  endpoint: string;
  method: string;
  data: any;
  timestamp: Date;
}

// PWA Actions
type PWAAction =
  | { type: 'SET_ONLINE'; payload: boolean }
  | { type: 'SET_INSTALLABLE'; payload: boolean }
  | { type: 'SET_INSTALLED'; payload: boolean }
  | { type: 'SET_UPDATE_AVAILABLE'; payload: boolean }
  | { type: 'ADD_SYNC_ACTION'; payload: SyncAction }
  | { type: 'REMOVE_SYNC_ACTION'; payload: string }
  | { type: 'ADD_OFFLINE_ACTION'; payload: OfflineAction }
  | { type: 'CLEAR_OFFLINE_ACTIONS' }
  | { type: 'SET_LAST_SYNC'; payload: Date }
  | { type: 'SET_INSTALL_PROMPT'; payload: any };

// PWA Reducer
const pwaReducer = (state: PWAState, action: PWAAction): PWAState => {
  switch (action.type) {
    case 'SET_ONLINE':
      return { ...state, isOnline: action.payload };
    case 'SET_INSTALLABLE':
      return { ...state, isInstallable: action.payload };
    case 'SET_INSTALLED':
      return { ...state, isInstalled: action.payload };
    case 'SET_UPDATE_AVAILABLE':
      return { ...state, updateAvailable: action.payload };
    case 'ADD_SYNC_ACTION':
      return {
        ...state,
        syncQueue: [...state.syncQueue, action.payload]
      };
    case 'REMOVE_SYNC_ACTION':
      return {
        ...state,
        syncQueue: state.syncQueue.filter(item => item.id !== action.payload)
      };
    case 'ADD_OFFLINE_ACTION':
      return {
        ...state,
        offlineActions: [...state.offlineActions, action.payload]
      };
    case 'CLEAR_OFFLINE_ACTIONS':
      return { ...state, offlineActions: [] };
    case 'SET_LAST_SYNC':
      return { ...state, lastSync: action.payload };
    case 'SET_INSTALL_PROMPT':
      return { ...state, installPrompt: action.payload };
    default:
      return state;
  }
};

// Initial PWA state
const initialPWAState: PWAState = {
  isOnline: navigator.onLine,
  isInstallable: false,
  isInstalled: false,
  updateAvailable: false,
  syncQueue: [],
  offlineActions: [],
  lastSync: null,
  installPrompt: null
};

// PWA Context
const PWAContext = createContext<{
  state: PWAState;
  dispatch: React.Dispatch<PWAAction>;
  installApp: () => Promise<void>;
  updateApp: () => void;
  syncOfflineActions: () => Promise<void>;
  addOfflineAction: (action: OfflineAction) => void;
} | null>(null);

// PWA Provider Component
export const PWAProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(pwaReducer, initialPWAState);

  // Initialize PWA features
  useEffect(() => {
    initializePWA();
  }, []);

  // Online/Offline detection
  useEffect(() => {
    const handleOnline = () => {
      dispatch({ type: 'SET_ONLINE', payload: true });
      toast.success('🌐 Back online! Syncing data...', {
        position: 'top-right',
        autoClose: 3000
      });
      syncOfflineActions();
    };

    const handleOffline = () => {
      dispatch({ type: 'SET_ONLINE', payload: false });
      toast.warning('📱 You are offline. Changes will be saved locally.', {
        position: 'top-right',
        autoClose: 5000
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Service Worker registration and updates
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      registerServiceWorker();
    }
  }, []);

  const initializePWA = async () => {
    // Check if app is already installed
    if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) {
      dispatch({ type: 'SET_INSTALLED', payload: true });
    }

    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      dispatch({ type: 'SET_INSTALLABLE', payload: true });
      dispatch({ type: 'SET_INSTALL_PROMPT', payload: e });
    });

    // Check for app installation
    window.addEventListener('appinstalled', () => {
      dispatch({ type: 'SET_INSTALLED', payload: true });
      dispatch({ type: 'SET_INSTALLABLE', payload: false });
      toast.success('🎉 NoxPanel installed successfully!', {
        position: 'top-center',
        autoClose: 5000
      });
    });

    // Load offline actions from localStorage
    loadOfflineActions();
  };

  const registerServiceWorker = async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');

      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;

        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              dispatch({ type: 'SET_UPDATE_AVAILABLE', payload: true });
              toast.info('🔄 App update available!', {
                position: 'top-center',
                autoClose: false,
                closeOnClick: false,
                onClick: updateApp
              });
            }
          });
        }
      });

      console.log('✅ Service Worker registered successfully');
    } catch (error) {
      console.error('❌ Service Worker registration failed:', error);
    }
  };

  const installApp = async (): Promise<void> => {
    if (!state.installPrompt) {
      toast.error('App installation not available');
      return;
    }

    try {
      const result = await state.installPrompt.prompt();

      if (result.outcome === 'accepted') {
        dispatch({ type: 'SET_INSTALLABLE', payload: false });
        dispatch({ type: 'SET_INSTALL_PROMPT', payload: null });
      }
    } catch (error) {
      console.error('❌ App installation failed:', error);
      toast.error('Failed to install app');
    }
  };

  const updateApp = (): void => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      });
    }
  };

  const loadOfflineActions = (): void => {
    try {
      const storedActions = localStorage.getItem('noxpanel_offline_actions');
      if (storedActions) {
        const actions: OfflineAction[] = JSON.parse(storedActions);
        actions.forEach(action => {
          dispatch({ type: 'ADD_OFFLINE_ACTION', payload: action });
        });
      }
    } catch (error) {
      console.error('❌ Failed to load offline actions:', error);
    }
  };

  const saveOfflineActions = (actions: OfflineAction[]): void => {
    try {
      localStorage.setItem('noxpanel_offline_actions', JSON.stringify(actions));
    } catch (error) {
      console.error('❌ Failed to save offline actions:', error);
    }
  };

  const addOfflineAction = (action: OfflineAction): void => {
    dispatch({ type: 'ADD_OFFLINE_ACTION', payload: action });

    // Save to localStorage
    const updatedActions = [...state.offlineActions, action];
    saveOfflineActions(updatedActions);
  };

  const syncOfflineActions = async (): Promise<void> => {
    if (!state.isOnline || state.offlineActions.length === 0) {
      return;
    }

    try {
      toast.info('🔄 Syncing offline changes...', {
        position: 'top-right',
        autoClose: 2000
      });

      const syncPromises = state.offlineActions.map(async (action) => {
        try {
          const response = await fetch(action.endpoint, {
            method: action.method,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: action.data ? JSON.stringify(action.data) : undefined
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }

          return { success: true, actionId: action.id };
        } catch (error) {
          console.error(`❌ Failed to sync action ${action.id}:`, error);
          return { success: false, actionId: action.id };
        }
      });

      const results = await Promise.all(syncPromises);
      const successfulSyncs = results.filter(r => r.success);

      if (successfulSyncs.length > 0) {
        dispatch({ type: 'CLEAR_OFFLINE_ACTIONS' });
        saveOfflineActions([]);
        dispatch({ type: 'SET_LAST_SYNC', payload: new Date() });

        toast.success(`✅ Synced ${successfulSyncs.length} offline changes`, {
          position: 'top-right',
          autoClose: 3000
        });
      }

    } catch (error) {
      console.error('❌ Sync failed:', error);
      toast.error('Failed to sync offline changes');
    }
  };

  return (
    <PWAContext.Provider
      value={{
        state,
        dispatch,
        installApp,
        updateApp,
        syncOfflineActions,
        addOfflineAction
      }}
    >
      {children}
    </PWAContext.Provider>
  );
};

// PWA Hook
export const usePWA = () => {
  const context = useContext(PWAContext);
  if (!context) {
    throw new Error('usePWA must be used within a PWAProvider');
  }
  return context;
};

// PWA Status Component
export const PWAStatus: React.FC = () => {
  const { state, installApp, updateApp } = usePWA();

  return (
    <div className="pwa-status">
      {/* Online/Offline Indicator */}
      <div className={`connection-status ${state.isOnline ? 'online' : 'offline'}`}>
        <span className="status-icon">
          {state.isOnline ? '🌐' : '📱'}
        </span>
        <span className="status-text">
          {state.isOnline ? 'Online' : 'Offline'}
        </span>
      </div>

      {/* Install App Button */}
      {state.isInstallable && !state.isInstalled && (
        <button
          className="install-button"
          onClick={installApp}
          title="Install NoxPanel as an app"
        >
          📱 Install App
        </button>
      )}

      {/* Update Available Button */}
      {state.updateAvailable && (
        <button
          className="update-button"
          onClick={updateApp}
          title="Update to latest version"
        >
          🔄 Update Available
        </button>
      )}

      {/* Offline Actions Counter */}
      {state.offlineActions.length > 0 && (
        <div className="offline-actions-counter">
          <span className="counter-icon">📋</span>
          <span className="counter-text">
            {state.offlineActions.length} pending
          </span>
        </div>
      )}

      {/* Last Sync Time */}
      {state.lastSync && (
        <div className="last-sync">
          <span className="sync-icon">🔄</span>
          <span className="sync-text">
            Last sync: {state.lastSync.toLocaleTimeString()}
          </span>
        </div>
      )}
    </div>
  );
};

// Offline-capable API hook
export const useOfflineAPI = () => {
  const { state, addOfflineAction } = usePWA();

  const makeRequest = async (
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> => {
    if (state.isOnline) {
      // Online - make normal request
      return fetch(endpoint, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          ...options.headers
        }
      });
    } else {
      // Offline - queue action for later sync
      const offlineAction: OfflineAction = {
        id: `offline_${Date.now()}_${Math.random()}`,
        endpoint,
        method: options.method || 'GET',
        data: options.body ? JSON.parse(options.body as string) : null,
        timestamp: new Date()
      };

      addOfflineAction(offlineAction);

      // Return a mock response for optimistic updates
      return new Response(JSON.stringify({
        success: true,
        offline: true,
        message: 'Action queued for sync when online'
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  };

  return { makeRequest, isOnline: state.isOnline };
};

// PWA manifest data
export const PWA_MANIFEST = {
  name: 'NoxPanel - Network Management',
  short_name: 'NoxPanel',
  description: 'Enterprise network monitoring and management dashboard',
  start_url: '/',
  display: 'standalone',
  background_color: '#1a1a2e',
  theme_color: '#0f3460',
  orientation: 'portrait-primary',
  icons: [
    {
      src: '/icons/icon-72x72.png',
      sizes: '72x72',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-96x96.png',
      sizes: '96x96',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-128x128.png',
      sizes: '128x128',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-144x144.png',
      sizes: '144x144',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-152x152.png',
      sizes: '152x152',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-192x192.png',
      sizes: '192x192',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-384x384.png',
      sizes: '384x384',
      type: 'image/png',
      purpose: 'maskable any'
    },
    {
      src: '/icons/icon-512x512.png',
      sizes: '512x512',
      type: 'image/png',
      purpose: 'maskable any'
    }
  ],
  screenshots: [
    {
      src: '/screenshots/dashboard-wide.png',
      sizes: '1280x720',
      type: 'image/png',
      form_factor: 'wide'
    },
    {
      src: '/screenshots/dashboard-mobile.png',
      sizes: '390x844',
      type: 'image/png',
      form_factor: 'narrow'
    }
  ],
  categories: ['productivity', 'utilities', 'business'],
  lang: 'en-US',
  dir: 'ltr'
};

// Service Worker installation helper
export const installServiceWorker = async (): Promise<void> => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      console.log('✅ Service Worker registered:', registration);
    } catch (error) {
      console.error('❌ Service Worker registration failed:', error);
    }
  }
};

// PWA Styles
export const PWA_STYLES = `
.pwa-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: var(--surface-color);
  border-radius: 8px;
  font-size: 0.875rem;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 16px;
  font-weight: 500;
}

.connection-status.online {
  background: rgba(34, 197, 94, 0.1);
  color: rgb(34, 197, 94);
}

.connection-status.offline {
  background: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
}

.install-button,
.update-button {
  padding: 0.5rem 1rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.install-button:hover,
.update-button:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.update-button {
  background: rgb(245, 158, 11);
}

.update-button:hover {
  background: rgb(217, 119, 6);
}

.offline-actions-counter,
.last-sync {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.offline-actions-counter {
  background: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

@media (max-width: 768px) {
  .pwa-status {
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.5rem;
  }

  .install-button,
  .update-button {
    padding: 0.375rem 0.75rem;
    font-size: 0.8rem;
  }
}
`;
