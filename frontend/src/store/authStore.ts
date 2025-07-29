import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, AuthState, LoginCredentials, LoginResponse } from '@/types/auth';

interface AuthStore extends AuthState {
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshAuthToken: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  
  // Session management
  checkSession: () => Promise<boolean>;
  isTokenExpired: () => boolean;
  getAuthHeader: () => string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  accessToken: null,
  refreshToken: null,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          // Make API call to login endpoint
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Login failed');
          }

          const loginResponse: LoginResponse = await response.json();
          
          set({
            user: loginResponse.user,
            isAuthenticated: true,
            accessToken: loginResponse.accessToken,
            refreshToken: loginResponse.refreshToken,
            isLoading: false,
            error: null,
          });

          // Announce successful login to screen readers
          if (typeof window !== 'undefined') {
            const announcement = `Successfully logged in as ${loginResponse.user.firstName} ${loginResponse.user.lastName}`;
            (window as any).announceToScreenReader?.(announcement);
          }

          // Dispatch login event for other components
          if (typeof document !== 'undefined') {
            document.dispatchEvent(new CustomEvent('user-login', {
              detail: { user: loginResponse.user }
            }));
          }

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
          
          set({
            isLoading: false,
            error: errorMessage,
            isAuthenticated: false,
            user: null,
            accessToken: null,
            refreshToken: null,
          });

          // Announce error to screen readers
          if (typeof window !== 'undefined') {
            const announcement = `Login failed: ${errorMessage}`;
            (window as any).announceToScreenReader?.(announcement);
          }

          // Dispatch error event
          if (typeof document !== 'undefined') {
            document.dispatchEvent(new CustomEvent('error-occurred', {
              detail: { message: errorMessage }
            }));
          }

          throw error;
        }
      },

      logout: () => {
        // Clear auth state
        set({
          ...initialState,
        });

        // Clear any cached data
        if (typeof localStorage !== 'undefined') {
          localStorage.removeItem('noxpanel-auth-storage');
        }

        // Announce logout to screen readers
        if (typeof window !== 'undefined') {
          const announcement = 'You have been logged out';
          (window as any).announceToScreenReader?.(announcement);
        }

        // Dispatch logout event
        if (typeof document !== 'undefined') {
          document.dispatchEvent(new CustomEvent('user-logout'));
        }

        // Redirect to login page
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      },

      refreshAuthToken: async () => {
        const { refreshToken: token } = get();
        
        if (!token) {
          get().logout();
          return;
        }

        try {
          const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Token refresh failed');
          }

          const loginResponse: LoginResponse = await response.json();
          
          set({
            user: loginResponse.user,
            accessToken: loginResponse.accessToken,
            refreshToken: loginResponse.refreshToken,
            error: null,
          });

        } catch (error) {
          console.error('Token refresh failed:', error);
          get().logout();
        }
      },

      updateUser: (userData: Partial<User>) => {
        const { user } = get();
        if (user) {
          set({
            user: { ...user, ...userData }
          });

          // Announce profile update to screen readers
          if (typeof window !== 'undefined') {
            const announcement = 'Profile updated successfully';
            (window as any).announceToScreenReader?.(announcement);
          }

          // Dispatch profile update event
          if (typeof document !== 'undefined') {
            document.dispatchEvent(new CustomEvent('profile-updated', {
              detail: { user: { ...user, ...userData } }
            }));
          }
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      checkSession: async () => {
        const { accessToken, refreshToken: token } = get();
        
        if (!accessToken || !token) {
          return false;
        }

        // Check if token is expired
        if (get().isTokenExpired()) {
          try {
            await get().refreshAuthToken();
            return true;
          } catch (error) {
            return false;
          }
        }

        return true;
      },

      isTokenExpired: () => {
        const { accessToken } = get();
        
        if (!accessToken) {
          return true;
        }

        try {
          // Decode JWT token to check expiration
          const payload = JSON.parse(atob(accessToken.split('.')[1]));
          const currentTime = Date.now() / 1000;
          
          // Check if token expires within the next 5 minutes
          return payload.exp < (currentTime + 300);
        } catch (error) {
          return true;
        }
      },

      getAuthHeader: () => {
        const { accessToken } = get();
        return accessToken ? `Bearer ${accessToken}` : null;
      },
    }),
    {
      name: 'noxpanel-auth-storage',
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state) => ({
        // Only persist specific fields for security
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
      migrate: (persistedState: any, version: number) => {
        if (version === 0) {
          return {
            ...initialState,
            ...persistedState,
          };
        }
        return persistedState;
      },
    }
  )
);

// Auto token refresh on app start
if (typeof window !== 'undefined') {
  const initAuth = async () => {
    const authStore = useAuthStore.getState();
    
    if (authStore.isAuthenticated && authStore.accessToken) {
      // Check session validity
      const isValid = await authStore.checkSession();
      
      if (!isValid) {
        authStore.logout();
      }
    }
  };
  
  // Initialize on app load
  initAuth();
  
  // Set up periodic token refresh (every 10 minutes)
  setInterval(() => {
    const authStore = useAuthStore.getState();
    
    if (authStore.isAuthenticated && authStore.isTokenExpired()) {
      authStore.refreshAuthToken().catch(() => {
        authStore.logout();
      });
    }
  }, 10 * 60 * 1000); // 10 minutes
}

// Intercept fetch requests to add auth headers
if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;
  
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const authStore = useAuthStore.getState();
    const authHeader = authStore.getAuthHeader();
    
    if (authHeader && init?.headers) {
      (init.headers as Record<string, string>)['Authorization'] = authHeader;
    } else if (authHeader) {
      init = {
        ...init,
        headers: {
          ...init?.headers,
          'Authorization': authHeader,
        },
      };
    }
    
    return originalFetch(input, init);
  };
}