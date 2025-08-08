import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface PublicRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ 
  children, 
  redirectTo = '/dashboard' 
}) => {
  const { isAuthenticated, isLoading } = useAuth();

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
        <h2>Loading...</h2>
        <p>Please wait while we check your authentication status</p>
      </div>
    );
  }

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  // Show public content
  return <>{children}</>;
};

export default PublicRoute;