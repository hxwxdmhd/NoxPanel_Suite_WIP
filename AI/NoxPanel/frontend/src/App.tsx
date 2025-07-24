import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { ThemeProvider as StyledThemeProvider } from 'styled-components';
import { Toaster } from 'react-hot-toast';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import { ThemeProvider } from './contexts/ThemeContext';
import GlobalStyles from './styles/GlobalStyles';
import Navigation from './components/Navigation/Navigation';
import Dashboard from './components/Dashboard/Dashboard';
import ScriptManager from './components/ScriptManager/ScriptManager';
import ThemeSelector from './components/ThemeSelector/ThemeSelector';
import { api } from './services/api';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5000,
      cacheTime: 10000,
    },
  },
});

const App: React.FC = () => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Check API connection on startup
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = await api.testConnection();
        setIsConnected(connected);
      } catch (error) {
        console.error('Connection check failed:', error);
        setIsConnected(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkConnection();
  }, []);

  // Connection status component
  const ConnectionStatus = () => {
    if (isLoading) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: 'var(--background-color)',
          color: 'var(--text-color)',
          fontSize: '1.2rem'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              width: '50px',
              height: '50px',
              border: '3px solid rgba(255,255,255,0.3)',
              borderTop: '3px solid var(--primary-color)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 1rem'
            }}></div>
            Connecting to NoxPanel...
          </div>
        </div>
      );
    }

    if (!isConnected) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: 'var(--background-color)',
          color: 'var(--text-color)',
          fontSize: '1.2rem'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>❌</div>
            <h2 style={{ color: '#dc3545', marginBottom: '1rem' }}>
              Connection Failed
            </h2>
            <p style={{ marginBottom: '2rem', opacity: 0.8 }}>
              Unable to connect to NoxPanel backend at http://127.0.0.1:5002
            </p>
            <button
              style={{
                background: 'var(--primary-color)',
                color: 'white',
                border: 'none',
                padding: '1rem 2rem',
                borderRadius: '8px',
                fontSize: '1rem',
                cursor: 'pointer'
              }}
              onClick={() => window.location.reload()}
            >
              Retry Connection
            </button>
            <div style={{ marginTop: '2rem', fontSize: '0.9rem', opacity: 0.7 }}>
              <p>Make sure the NoxPanel backend is running:</p>
              <code style={{
                background: 'rgba(255,255,255,0.1)',
                padding: '0.5rem',
                borderRadius: '4px',
                display: 'inline-block',
                marginTop: '0.5rem'
              }}>
                python ultra_optimized_noxpanel.py
              </code>
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Router>
          <GlobalStyles />

          {/* Toast notifications */}
          <Toaster
            position="top-right"
            reverseOrder={false}
            gutter={8}
            containerClassName=""
            containerStyle={{}}
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--surface-color)',
                color: 'var(--text-color)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              },
              success: {
                style: {
                  borderLeft: '4px solid #28a745',
                },
              },
              error: {
                style: {
                  borderLeft: '4px solid #dc3545',
                },
              },
            }}
          />

          <ConnectionStatus />

          {isConnected && (
            <div style={{ display: 'flex', minHeight: '100vh' }}>
              <Navigation />

              <main style={{
                flex: 1,
                marginLeft: '250px',
                background: 'var(--background-color)',
                minHeight: '100vh',
                transition: 'all var(--transition-duration) ease'
              }}>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/scripts" element={<ScriptManager />} />
                  <Route path="/themes" element={<ThemeSelector />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </main>

              {/* Floating theme selector */}
              <div style={{
                position: 'fixed',
                bottom: '2rem',
                right: '2rem',
                zIndex: 1000
              }}>
                <ThemeSelector compact />
              </div>
            </div>
          )}

          {/* React Query Devtools - only in development */}
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
