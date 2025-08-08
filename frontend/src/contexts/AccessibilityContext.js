import React, { createContext, useContext, useEffect, useState } from 'react';

// Create context
const AccessibilityContext = createContext();

// Hook to use the accessibility context
export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

// Default accessibility settings
const defaultSettings = {
  // Visual preferences
  highContrast: false,
  reduceMotion: false,
  largerText: false,
  
  // Focus and navigation
  focusIndicators: true,
  keyboardNavigation: true,
  
  // Cognitive support
  announcements: true,
  confirmDialogs: true,
  simplifiedUI: false,
  
  // Color and themes
  colorBlindSupport: false,
  customColors: null,
  
  // Timing and interaction
  extendedTimeouts: false,
  pauseAnimations: false,
  
  // Audio preferences
  soundEnabled: true,
  speechRate: 1.0,
  voiceVolume: 0.8,
};

// Accessibility Provider Component
export const AccessibilityProvider = ({ children }) => {
  const [settings, setSettings] = useState(() => {
    // Load from localStorage if available
    try {
      const saved = localStorage.getItem('noxpanel-accessibility');
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    } catch (error) {
      console.warn('Failed to load accessibility settings:', error);
      return defaultSettings;
    }
  });

  // Save to localStorage when settings change
  useEffect(() => {
    try {
      localStorage.setItem('noxpanel-accessibility', JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save accessibility settings:', error);
    }
  }, [settings]);

  // Apply system preferences on mount
  useEffect(() => {
    const mediaQueries = {
      prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)'),
      prefersHighContrast: window.matchMedia('(prefers-contrast: high)'),
      prefersDarkScheme: window.matchMedia('(prefers-color-scheme: dark)'),
    };

    // Check if user prefers reduced motion
    if (mediaQueries.prefersReducedMotion.matches && !settings.reduceMotion) {
      updateSetting('reduceMotion', true);
    }

    // Check if user prefers high contrast
    if (mediaQueries.prefersHighContrast.matches && !settings.highContrast) {
      updateSetting('highContrast', true);
    }

    // Listen for changes in system preferences
    const handleMotionChange = (e) => {
      if (e.matches) {
        updateSetting('reduceMotion', true);
        announceChange('Motion reduction enabled due to system preference');
      }
    };

    const handleContrastChange = (e) => {
      if (e.matches) {
        updateSetting('highContrast', true);
        announceChange('High contrast enabled due to system preference');
      }
    };

    mediaQueries.prefersReducedMotion.addEventListener('change', handleMotionChange);
    mediaQueries.prefersHighContrast.addEventListener('change', handleContrastChange);

    return () => {
      mediaQueries.prefersReducedMotion.removeEventListener('change', handleMotionChange);
      mediaQueries.prefersHighContrast.removeEventListener('change', handleContrastChange);
    };
  }, [settings.reduceMotion, settings.highContrast]);

  // Keyboard navigation setup
  useEffect(() => {
    if (settings.keyboardNavigation) {
      const handleKeyDown = (event) => {
        // Alt + 1-6 for quick navigation
        if (event.altKey && event.key >= '1' && event.key <= '6') {
          event.preventDefault();
          const routes = [
            '/dashboard',
            '/security', 
            '/plugins',
            '/analytics',
            '/settings',
            '/help'
          ];
          const routeIndex = parseInt(event.key) - 1;
          if (routes[routeIndex]) {
            announceChange(`Navigating to ${routes[routeIndex].substring(1)}`);
            // Navigation would be handled by router
            window.location.hash = routes[routeIndex];
          }
        }
        
        // Escape key to close modals/dialogs
        if (event.key === 'Escape') {
          const openDialog = document.querySelector('[role="dialog"][aria-hidden="false"]');
          if (openDialog) {
            event.preventDefault();
            announceChange('Dialog closed');
            // Close dialog logic would go here
          }
        }
        
        // Ctrl + K for search
        if (event.ctrlKey && event.key === 'k') {
          event.preventDefault();
          announceChange('Search activated');
          // Search activation logic would go here
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [settings.keyboardNavigation]);

  // Function to update a single setting
  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Function to update multiple settings
  const updateSettings = (newSettings) => {
    setSettings(prev => ({
      ...prev,
      ...newSettings
    }));
  };

  // Function to reset to defaults
  const resetSettings = () => {
    setSettings(defaultSettings);
    announceChange('Accessibility settings reset to defaults');
  };

  // Function to announce changes to screen readers
  const announceChange = (message) => {
    if (settings.announcements && 'speechSynthesis' in window) {
      // Create announcement for screen readers
      const announcement = new SpeechSynthesisUtterance(message);
      announcement.volume = settings.voiceVolume;
      announcement.rate = settings.speechRate;
      announcement.pitch = 1;
      
      // Use a subtle voice for announcements
      const voices = speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice => 
        voice.lang.startsWith('en') && voice.name.includes('Natural')
      ) || voices[0];
      
      if (preferredVoice) {
        announcement.voice = preferredVoice;
      }
      
      speechSynthesis.speak(announcement);
    }
    
    // Also create a live region announcement for screen readers
    const liveRegion = document.getElementById('accessibility-announcements');
    if (liveRegion) {
      liveRegion.textContent = message;
      setTimeout(() => {
        liveRegion.textContent = '';
      }, 1000);
    }
  };

  // Function to get contrast ratio for color combinations
  const getContrastRatio = (color1, color2) => {
    // Simplified contrast ratio calculation
    // In a real implementation, you'd use a proper color contrast library
    return settings.highContrast ? 'high' : 'normal';
  };

  // Function to check if an element should have focus indicators
  const shouldShowFocusIndicator = (element) => {
    return settings.focusIndicators && element.matches(':focus-visible');
  };

  // Value object to provide to context consumers
  const contextValue = {
    // Settings
    settings,
    updateSetting,
    updateSettings,
    resetSettings,
    
    // Utility functions
    announceChange,
    getContrastRatio,
    shouldShowFocusIndicator,
    
    // Computed values
    isHighContrast: settings.highContrast,
    hasReducedMotion: settings.reduceMotion,
    isLargerText: settings.largerText,
    hasFocusIndicators: settings.focusIndicators,
    hasAnnouncements: settings.announcements,
    
    // Quick access to common settings
    motionPreference: settings.reduceMotion ? 'reduce' : 'auto',
    contrastPreference: settings.highContrast ? 'high' : 'normal',
    textSizePreference: settings.largerText ? 'large' : 'normal',
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
      
      {/* Accessibility announcements live region */}
      <div
        id="accessibility-announcements"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: 'absolute',
          left: '-10000px',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
        }}
      />
      
      {/* Skip to main content link */}
      <a
        href="#main-content"
        style={{
          position: 'absolute',
          left: '-10000px',
          top: 'auto',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
          zIndex: 999999,
          padding: '8px 16px',
          background: settings.highContrast ? '#000000' : '#1976d2',
          color: '#ffffff',
          textDecoration: 'none',
          borderRadius: '4px',
          fontSize: '14px',
          fontWeight: 'bold',
          ...(settings.focusIndicators && {
            ':focus': {
              position: 'absolute',
              left: '6px',
              top: '6px',
              width: 'auto',
              height: 'auto',
              overflow: 'visible',
            }
          })
        }}
        onFocus={(e) => {
          if (settings.focusIndicators) {
            e.target.style.position = 'absolute';
            e.target.style.left = '6px';
            e.target.style.top = '6px';
            e.target.style.width = 'auto';
            e.target.style.height = 'auto';
            e.target.style.overflow = 'visible';
          }
        }}
        onBlur={(e) => {
          e.target.style.position = 'absolute';
          e.target.style.left = '-10000px';
          e.target.style.top = 'auto';
          e.target.style.width = '1px';
          e.target.style.height = '1px';
          e.target.style.overflow = 'hidden';
        }}
      >
        Skip to main content
      </a>
    </AccessibilityContext.Provider>
  );
};