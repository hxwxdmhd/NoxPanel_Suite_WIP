import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, CircularProgress, Alert } from '@mui/material';
import { Toaster } from 'react-hot-toast';

// Contexts
import { AccessibilityProvider } from './contexts/AccessibilityContext';
import { SocketProvider } from './contexts/SocketContext';

// Components
import Dashboard from './components/Dashboard/Dashboard';
import SecurityCenter from './components/Security/SecurityCenter';
import PluginManager from './components/Plugins/PluginManager';
import CrawlerVisualizer from './components/Analytics/CrawlerVisualizer';
import Login from './components/Auth/Login';
import Layout from './components/Layout/Layout';
import AccessibilitySettings from './components/Settings/AccessibilitySettings';

// Services and Stores
import { useAuthStore } from './store/authStore';
import { useThemeStore } from './store/themeStore';
import { adhdFriendlyTheme } from './styles/theme';

function App() {
  const [appLoading, setAppLoading] = useState(true);
  const [error, setError] = useState(null);

  // Mock authentication and theme for now
  const isAuthenticated = false;
  const themeMode = 'light';
  const accessibility = {
    reduceMotion: false,
    announcements: true,
    highContrast: false
  };

  // Create ADHD-friendly theme
  const theme = React.useMemo(() => {
    return createTheme(adhdFriendlyTheme(themeMode, accessibility));
  }, [themeMode, accessibility]);

  // Initialize app
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Mock initialization
        setTimeout(() => {
          setAppLoading(false);
        }, 1000);
      } catch (err) {
        console.error('App initialization failed:', err);
        setError('Failed to initialize application');
        setAppLoading(false);
      }
    };

    initializeApp();
  }, []);

  // Loading screen with ADHD-friendly design
  if (appLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100vh',
            bgcolor: 'background.default',
            gap: 3
          }}
        >
          <CircularProgress 
            size={60} 
            thickness={4}
            sx={{ 
              color: 'primary.main',
              filter: accessibility.reduceMotion ? 'none' : 'drop-shadow(0 0 8px currentColor)'
            }}
          />
          <Box sx={{ 
            textAlign: 'center', 
            color: 'text.primary',
            fontSize: '1.2rem',
            fontWeight: 500
          }}>
            {accessibility.reduceMotion ? 'Loading NoxPanel...' : 'Initializing NoxPanel...'}
          </Box>
        </Box>
      </ThemeProvider>
    );
  }

  // Error screen
  if (error) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ p: 3 }}>
          <Alert severity="error" sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
            {error}
          </Alert>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AccessibilityProvider>
        <Router>
          {isAuthenticated ? (
            <SocketProvider>
              <Layout>
                <Routes>
                  {/* Main Dashboard */}
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  
                  {/* Security Center */}
                  <Route path="/security" element={<SecurityCenter />} />
                  
                  {/* Plugin Management */}
                  <Route path="/plugins" element={<PluginManager />} />
                  
                  {/* Analytics & Crawler */}
                  <Route path="/analytics" element={<CrawlerVisualizer />} />
                  <Route path="/crawler" element={<CrawlerVisualizer />} />
                  
                  {/* Settings */}
                  <Route path="/settings" element={<AccessibilitySettings />} />
                  <Route path="/settings/accessibility" element={<AccessibilitySettings />} />
                  
                  {/* Catch all - redirect to dashboard */}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </Layout>
            </SocketProvider>
          ) : (
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          )}
        </Router>
      </AccessibilityProvider>
      
      {/* Toast notifications with ADHD-friendly styling */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        containerStyle={{
          top: 80, // Account for app bar
        }}
        toastOptions={{
          duration: accessibility.announcements ? 6000 : 4000,
          style: {
            background: theme.palette.mode === 'dark' ? '#2d2d2d' : '#ffffff',
            color: theme.palette.text.primary,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: theme.shape.borderRadius,
            fontSize: '0.95rem',
            padding: '12px 16px',
            maxWidth: '400px',
            boxShadow: theme.shadows[8],
          },
          success: {
            iconTheme: {
              primary: '#4caf50',
              secondary: '#ffffff',
            },
          },
          error: {
            duration: accessibility.announcements ? 8000 : 5000,
            iconTheme: {
              primary: '#f44336',
              secondary: '#ffffff',
            },
          },
        }}
      />
    </ThemeProvider>
  );
}

export default App;