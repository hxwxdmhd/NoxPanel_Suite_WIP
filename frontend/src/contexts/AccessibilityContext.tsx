import React, { createContext, useContext, useEffect, ReactNode, useCallback } from 'react';
import { useThemeStore } from '@/store/themeStore';

interface AccessibilityContextType {
  // Current accessibility settings
  isHighContrast: boolean;
  isReducedMotion: boolean;
  isFocusMode: boolean;
  autoSave: boolean;
  keyboardNavigation: boolean;
  screenReaderMode: boolean;
  largeText: boolean;
  soundEnabled: boolean;
  
  // Actions
  toggleHighContrast: () => void;
  toggleReducedMotion: () => void;
  toggleFocusMode: () => void;
  toggleAutoSave: () => void;
  toggleKeyboardNavigation: () => void;
  toggleScreenReaderMode: () => void;
  toggleLargeText: () => void;
  toggleSound: () => void;
  resetToDefaults: () => void;
  
  // Utility functions
  announceToScreenReader: (message: string) => void;
  playSound: (soundType: 'success' | 'error' | 'notification' | 'focus') => void;
  showAutoSaveIndicator: () => void;
  manageFocus: (element: HTMLElement | null) => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | null>(null);

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

interface AccessibilityProviderProps {
  children: ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const {
    isHighContrast,
    isReducedMotion,
    isFocusMode,
    autoSave,
    keyboardNavigation,
    screenReaderMode,
    largeText,
    soundEnabled,
    toggleHighContrast,
    toggleReducedMotion,
    toggleFocusMode,
    toggleAutoSave,
    toggleKeyboardNavigation,
    toggleScreenReaderMode,
    toggleLargeText,
    toggleSound,
    resetToDefaults,
  } = useThemeStore();

  // Announce messages to screen readers
  const announceToScreenReader = useCallback((message: string) => {
    if (!screenReaderMode && !keyboardNavigation) return;

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
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }, [screenReaderMode, keyboardNavigation]);

  // Play accessibility sounds
  const playSound = useCallback((soundType: 'success' | 'error' | 'notification' | 'focus') => {
    if (!soundEnabled) return;

    // Create audio context for accessibility sounds
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Different frequencies for different sound types
      const frequencies = {
        success: 523.25, // C5
        error: 261.63,   // C4
        notification: 440, // A4
        focus: 349.23,   // F4
      };

      oscillator.frequency.setValueAtTime(frequencies[soundType], audioContext.currentTime);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.warn('Audio not supported for accessibility sounds:', error);
    }
  }, [soundEnabled]);

  // Show auto-save indicator
  const showAutoSaveIndicator = useCallback(() => {
    if (!autoSave) return;

    let indicator = document.querySelector('.auto-save-indicator') as HTMLElement;
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'auto-save-indicator';
      indicator.textContent = 'Auto-saved';
      indicator.setAttribute('aria-live', 'polite');
      document.body.appendChild(indicator);
    }

    indicator.classList.add('show');
    
    setTimeout(() => {
      indicator.classList.remove('show');
    }, 2000);

    // Play success sound
    playSound('success');
    
    // Announce to screen readers
    announceToScreenReader('Changes auto-saved');
  }, [autoSave, playSound, announceToScreenReader]);

  // Enhanced focus management for ADHD users
  const manageFocus = useCallback((element: HTMLElement | null) => {
    if (!element || !keyboardNavigation) return;

    // Apply enhanced focus styling
    element.classList.add('keyboard-navigation-active');
    
    // Remove focus styling after a delay
    setTimeout(() => {
      element.classList.remove('keyboard-navigation-active');
    }, 3000);

    // Scroll element into view with smooth animation
    element.scrollIntoView({
      behavior: isReducedMotion ? 'auto' : 'smooth',
      block: 'center',
      inline: 'nearest'
    });

    // Play focus sound
    playSound('focus');
  }, [keyboardNavigation, isReducedMotion, playSound]);

  // Set up accessibility event listeners
  useEffect(() => {
    const handleKeyboardNavigation = (event: KeyboardEvent) => {
      if (!keyboardNavigation) return;

      // Tab navigation enhancement
      if (event.key === 'Tab') {
        document.body.classList.add('keyboard-navigation-active');
        
        // Remove after 3 seconds of no tab usage
        clearTimeout((window as any).keyboardTimeout);
        (window as any).keyboardTimeout = setTimeout(() => {
          document.body.classList.remove('keyboard-navigation-active');
        }, 3000);
      }

      // Escape key functionality
      if (event.key === 'Escape') {
        event.preventDefault();
        document.dispatchEvent(new CustomEvent('close-modal'));
        announceToScreenReader('Modal or overlay closed');
      }

      // ADHD-friendly shortcuts (Alt + key)
      if (event.altKey) {
        switch (event.key) {
          case 'h':
            event.preventDefault();
            toggleHighContrast();
            break;
          case 'f':
            event.preventDefault();
            toggleFocusMode();
            break;
          case '1':
          case '2':
          case '3':
          case '4':
          case '5':
          case '6':
            event.preventDefault();
            const routes = ['/', '/security', '/plugins', '/analytics', '/settings', '/help'];
            const index = parseInt(event.key) - 1;
            if (routes[index]) {
              window.location.hash = routes[index];
              announceToScreenReader(`Navigating to ${routes[index].replace('/', '')} page`);
            }
            break;
        }
      }
    };

    // Auto-save functionality
    const handleAutoSave = () => {
      if (autoSave) {
        // Trigger auto-save for form data
        const forms = document.querySelectorAll('form[data-auto-save]');
        forms.forEach(form => {
          const formData = new FormData(form as HTMLFormElement);
          const data: Record<string, any> = {};
          
          // Convert FormData to plain object
          formData.forEach((value, key) => {
            data[key] = value;
          });
          
          // Store in session storage for recovery
          sessionStorage.setItem(`auto-save-${form.id || 'form'}`, JSON.stringify({
            data,
            timestamp: Date.now()
          }));
        });
        
        showAutoSaveIndicator();
      }
    };

    // Focus trap for modals
    const handleFocusTrap = (event: FocusEvent) => {
      const modal = document.querySelector('.focus-trap');
      if (modal && keyboardNavigation) {
        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
        
        if (event.target === lastElement && event.relatedTarget === null) {
          firstElement.focus();
        }
      }
    };

    // Event listeners
    document.addEventListener('keydown', handleKeyboardNavigation);
    document.addEventListener('auto-save', handleAutoSave);
    document.addEventListener('focusin', handleFocusTrap);
    
    // Auto-save timer
    const autoSaveInterval = setInterval(handleAutoSave, 30000); // Every 30 seconds

    return () => {
      document.removeEventListener('keydown', handleKeyboardNavigation);
      document.removeEventListener('auto-save', handleAutoSave);
      document.removeEventListener('focusin', handleFocusTrap);
      clearInterval(autoSaveInterval);
    };
  }, [
    keyboardNavigation,
    autoSave,
    toggleHighContrast,
    toggleFocusMode,
    announceToScreenReader,
    showAutoSaveIndicator
  ]);

  // Apply accessibility classes to document
  useEffect(() => {
    const root = document.documentElement;
    
    root.classList.toggle('high-contrast', isHighContrast);
    root.classList.toggle('reduced-motion', isReducedMotion);
    root.classList.toggle('large-text', largeText);
    root.classList.toggle('screen-reader-mode', screenReaderMode);
    root.classList.toggle('keyboard-navigation-enabled', keyboardNavigation);
    
    document.body.classList.toggle('focus-mode', isFocusMode);
  }, [isHighContrast, isReducedMotion, largeText, screenReaderMode, keyboardNavigation, isFocusMode]);

  // Make announceToScreenReader available globally
  useEffect(() => {
    (window as any).announceToScreenReader = announceToScreenReader;
  }, [announceToScreenReader]);

  const value: AccessibilityContextType = {
    isHighContrast,
    isReducedMotion,
    isFocusMode,
    autoSave,
    keyboardNavigation,
    screenReaderMode,
    largeText,
    soundEnabled,
    toggleHighContrast,
    toggleReducedMotion,
    toggleFocusMode,
    toggleAutoSave,
    toggleKeyboardNavigation,
    toggleScreenReaderMode,
    toggleLargeText,
    toggleSound,
    resetToDefaults,
    announceToScreenReader,
    playSound,
    showAutoSaveIndicator,
    manageFocus,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
};