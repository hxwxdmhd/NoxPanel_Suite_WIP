import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// Import service worker for PWA functionality
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

// Performance monitoring
import { reportWebVitals } from './reportWebVitals';

const container = document.getElementById('root');
if (!container) throw new Error('Failed to find the root element');

const root = createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker for offline functionality
serviceWorkerRegistration.register();

// Performance monitoring with Web Vitals
reportWebVitals(console.log);

// ADHD-Friendly keyboard shortcuts setup
document.addEventListener('keydown', (event) => {
  // Alt + H: Toggle High Contrast
  if (event.altKey && event.key === 'h') {
    event.preventDefault();
    document.dispatchEvent(new CustomEvent('toggle-high-contrast'));
  }
  
  // Alt + F: Toggle Focus Mode
  if (event.altKey && event.key === 'f') {
    event.preventDefault();
    document.dispatchEvent(new CustomEvent('toggle-focus-mode'));
  }
  
  // Alt + 1-6: Navigation shortcuts
  if (event.altKey && ['1', '2', '3', '4', '5', '6'].includes(event.key)) {
    event.preventDefault();
    const routes = ['/', '/security', '/plugins', '/analytics', '/settings', '/help'];
    const index = parseInt(event.key) - 1;
    if (routes[index]) {
      window.location.hash = routes[index];
    }
  }
  
  // Escape: Close modals/overlays
  if (event.key === 'Escape') {
    document.dispatchEvent(new CustomEvent('close-modal'));
  }
});

// Auto-save functionality for ADHD users
let autoSaveTimeout: NodeJS.Timeout;

document.addEventListener('input', () => {
  clearTimeout(autoSaveTimeout);
  autoSaveTimeout = setTimeout(() => {
    document.dispatchEvent(new CustomEvent('auto-save'));
  }, 2000); // Auto-save after 2 seconds of inactivity
});

// Accessibility announcements
const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

// Global accessibility event listeners
document.addEventListener('route-change', (event: any) => {
  announceToScreenReader(`Navigated to ${event.detail.routeName}`);
});

document.addEventListener('error-occurred', (event: any) => {
  announceToScreenReader(`Error: ${event.detail.message}`);
});

document.addEventListener('success-action', (event: any) => {
  announceToScreenReader(`Success: ${event.detail.message}`);
});

// Export announce function for use in components
(window as any).announceToScreenReader = announceToScreenReader;