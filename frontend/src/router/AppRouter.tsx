import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useAccessibility } from '@/contexts/AccessibilityContext';
import ProtectedRoute from './ProtectedRoute';
import PublicRoute from './PublicRoute';

// Lazy load components for better performance
const Dashboard = lazy(() => import('@/components/organisms/Dashboard'));
const Security = lazy(() => import('@/components/organisms/Security'));
const PluginManager = lazy(() => import('@/components/organisms/PluginManager'));
const Analytics = lazy(() => import('@/components/organisms/Analytics'));
const Settings = lazy(() => import('@/components/organisms/Settings'));
const Login = lazy(() => import('@/components/pages/Login'));
const NotFound = lazy(() => import('@/components/pages/NotFound'));

// Loading component with ADHD-friendly design
const LoadingFallback: React.FC<{ message?: string }> = ({ message = 'Loading...' }) => (
  <div 
    className="loading-container"
    role="status"
    aria-live="polite"
    aria-label={message}
  >
    <div className="loading-spinner" aria-hidden="true" />
    <h2>{message}</h2>
    <p>Please wait while we load your content</p>
  </div>
);

const AppRouter: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { announceToScreenReader } = useAccessibility();
  const location = useLocation();

  // Announce route changes to screen readers
  React.useEffect(() => {
    const routeNames: Record<string, string> = {
      '/': 'Dashboard',
      '/dashboard': 'Dashboard',
      '/security': 'Security Monitoring',
      '/plugins': 'Plugin Management',
      '/analytics': 'Analytics and Reports',
      '/settings': 'Settings',
      '/login': 'Login',
    };

    const routeName = routeNames[location.pathname] || 'Page';
    announceToScreenReader(`Navigated to ${routeName} page`);

    // Dispatch route change event
    document.dispatchEvent(new CustomEvent('route-change', {
      detail: { 
        path: location.pathname,
        routeName 
      }
    }));

    // Update page title for ADHD users
    document.title = `${routeName} - NoxPanel Suite`;

    // Reset focus to main content for keyboard users
    const mainContent = document.querySelector('main');
    if (mainContent) {
      mainContent.focus();
    }
  }, [location.pathname, announceToScreenReader]);

  // Skip link for accessibility
  const SkipLink = () => (
    <a 
      href="#main-content" 
      className="skip-link"
      onClick={(e) => {
        e.preventDefault();
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
          mainContent.focus();
          mainContent.scrollIntoView({ behavior: 'smooth' });
        }
      }}
    >
      Skip to main content
    </a>
  );

  return (
    <>
      <SkipLink />
      <main id="main-content" tabIndex={-1}>
        <Suspense fallback={<LoadingFallback message="Loading application..." />}>
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Suspense fallback={<LoadingFallback message="Loading login page..." />}>
                    <Login />
                  </Suspense>
                </PublicRoute>
              }
            />

            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              }
            />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingFallback message="Loading dashboard..." />}>
                    <Dashboard />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="/security"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingFallback message="Loading security monitoring..." />}>
                    <Security />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="/plugins"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingFallback message="Loading plugin manager..." />}>
                    <PluginManager />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingFallback message="Loading analytics..." />}>
                    <Analytics />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<LoadingFallback message="Loading settings..." />}>
                    <Settings />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            {/* Catch all route */}
            <Route
              path="*"
              element={
                <Suspense fallback={<LoadingFallback message="Loading page..." />}>
                  <NotFound />
                </Suspense>
              }
            />
          </Routes>
        </Suspense>
      </main>

      {/* Live region for dynamic announcements */}
      <div
        id="live-region"
        className="live-region"
        aria-live="polite"
        aria-atomic="true"
      />
    </>
  );
};

export default AppRouter;