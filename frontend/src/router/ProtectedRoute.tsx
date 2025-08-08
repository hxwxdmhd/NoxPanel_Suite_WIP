import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useAccessibility } from '@/contexts/AccessibilityContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole, 
  requiredPermission 
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const { announceToScreenReader } = useAccessibility();
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div 
        className="loading-container"
        role="status"
        aria-live="polite"
        aria-label="Checking authentication..."
      >
        <div className="loading-spinner" aria-hidden="true" />
        <h2>Verifying Access...</h2>
        <p>Please wait while we verify your authentication</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    announceToScreenReader('Access denied. Please log in to continue.');
    
    return (
      <Navigate 
        to="/login" 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Check role-based access
  if (requiredRole && user.role?.name !== requiredRole) {
    announceToScreenReader(`Access denied. ${requiredRole} role required.`);
    
    return (
      <div 
        className="access-denied-container"
        role="alert"
        aria-live="assertive"
      >
        <h1>Access Denied</h1>
        <p>
          You don't have permission to access this page. 
          Your current role is: {user.role?.name || 'Unknown'}
        </p>
        <p>Required role: {requiredRole}</p>
        <button
          onClick={() => window.history.back()}
          className="btn btn-primary"
          style={{
            marginTop: '16px',
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            background: '#3b82f6',
            color: '#ffffff',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
          }}
        >
          Go Back
        </button>
      </div>
    );
  }

  // Check permission-based access
  if (requiredPermission) {
    const hasPermission = user.permissions?.some(
      permission => permission.name === requiredPermission
    );

    if (!hasPermission) {
      announceToScreenReader(`Access denied. ${requiredPermission} permission required.`);
      
      return (
        <div 
          className="access-denied-container"
          role="alert"
          aria-live="assertive"
        >
          <h1>Permission Required</h1>
          <p>
            You don't have the necessary permission to access this page.
          </p>
          <p>Required permission: {requiredPermission}</p>
          <p>
            Your permissions: {user.permissions?.map(p => p.name).join(', ') || 'None'}
          </p>
          <button
            onClick={() => window.history.back()}
            className="btn btn-primary"
            style={{
              marginTop: '16px',
              padding: '12px 24px',
              borderRadius: '8px',
              border: 'none',
              background: '#3b82f6',
              color: '#ffffff',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
            }}
          >
            Go Back
          </button>
        </div>
      );
    }
  }

  // User is authenticated and authorized
  return <>{children}</>;
};

export default ProtectedRoute;