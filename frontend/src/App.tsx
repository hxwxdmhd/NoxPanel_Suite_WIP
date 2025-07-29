import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';

// Context Providers
import { AuthProvider } from '@/contexts/AuthContext';
import { AccessibilityProvider } from '@/contexts/AccessibilityContext';
import { SocketProvider } from '@/contexts/SocketContext';
import { NotificationProvider } from '@/contexts/NotificationContext';

// Main Components
import AppRouter from '@/router/AppRouter';
import { createCustomTheme } from '@/styles/themes';
import { GlobalStyles } from '@/styles/GlobalStyles';

// Hooks
import { useThemeStore } from '@/store/themeStore';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const { currentTheme, isHighContrast, isReducedMotion } = useThemeStore();
  
  // Create theme with current settings
  const theme = createCustomTheme({
    mode: currentTheme,
    isHighContrast,
    isReducedMotion,
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <GlobalStyles />
        <AccessibilityProvider>
          <AuthProvider>
            <SocketProvider>
              <NotificationProvider>
                <Router>
                  <div className="App">
                    <AppRouter />
                    
                    {/* Global Toast Notifications */}
                    <Toaster
                      position="top-right"
                      toastOptions={{
                        duration: 4000,
                        style: {
                          background: theme.palette.background.paper,
                          color: theme.palette.text.primary,
                          border: `1px solid ${theme.palette.divider}`,
                          fontSize: '14px',
                          borderRadius: '8px',
                          boxShadow: theme.shadows[4],
                        },
                        success: {
                          iconTheme: {
                            primary: theme.palette.success.main,
                            secondary: theme.palette.success.contrastText,
                          },
                        },
                        error: {
                          iconTheme: {
                            primary: theme.palette.error.main,
                            secondary: theme.palette.error.contrastText,
                          },
                        },
                      }}
                    />
                  </div>
                </Router>
              </NotificationProvider>
            </SocketProvider>
          </AuthProvider>
        </AccessibilityProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;