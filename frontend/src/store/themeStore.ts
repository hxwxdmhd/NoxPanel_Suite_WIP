import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface ThemeState {
  // Theme settings
  currentTheme: 'light' | 'dark' | 'auto';
  isHighContrast: boolean;
  isReducedMotion: boolean;
  isFocusMode: boolean;
  
  // ADHD-friendly settings
  autoSave: boolean;
  keyboardNavigation: boolean;
  screenReaderMode: boolean;
  largeText: boolean;
  soundEnabled: boolean;
  
  // Actions
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  toggleHighContrast: () => void;
  toggleReducedMotion: () => void;
  toggleFocusMode: () => void;
  toggleAutoSave: () => void;
  toggleKeyboardNavigation: () => void;
  toggleScreenReaderMode: () => void;
  toggleLargeText: () => void;
  toggleSound: () => void;
  resetToDefaults: () => void;
  
  // System preference detection
  systemPrefersDark: boolean;
  systemPrefersReducedMotion: boolean;
  systemPrefersHighContrast: boolean;
  setSystemPreferences: (preferences: {
    prefersDark: boolean;
    prefersReducedMotion: boolean;
    prefersHighContrast: boolean;
  }) => void;
}

// Default values for ADHD-friendly design
const defaultThemeState = {
  currentTheme: 'auto' as const,
  isHighContrast: false,
  isReducedMotion: false,
  isFocusMode: false,
  autoSave: true, // Enable by default for ADHD users
  keyboardNavigation: true, // Enable by default
  screenReaderMode: false,
  largeText: false,
  soundEnabled: false,
  systemPrefersDark: false,
  systemPrefersReducedMotion: false,
  systemPrefersHighContrast: false,
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      ...defaultThemeState,
      
      setTheme: (theme) => {
        set({ currentTheme: theme });
        // Announce theme change to screen readers
        if (typeof window !== 'undefined') {
          const announcement = `Theme changed to ${theme} mode`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleHighContrast: () => {
        const newValue = !get().isHighContrast;
        set({ isHighContrast: newValue });
        
        // Update CSS custom property for immediate effect
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('adhd-high-contrast', newValue);
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `High contrast mode ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleReducedMotion: () => {
        const newValue = !get().isReducedMotion;
        set({ isReducedMotion: newValue });
        
        // Update CSS custom property
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('adhd-reduced-motion', newValue);
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Reduced motion ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleFocusMode: () => {
        const newValue = !get().isFocusMode;
        set({ isFocusMode: newValue });
        
        // Update body class for focus mode
        if (typeof document !== 'undefined') {
          document.body.classList.toggle('adhd-focus-mode', newValue);
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Focus mode ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleAutoSave: () => {
        const newValue = !get().autoSave;
        set({ autoSave: newValue });
        
        // Dispatch custom event for auto-save toggle
        if (typeof document !== 'undefined') {
          document.dispatchEvent(new CustomEvent('auto-save-toggle', { 
            detail: { enabled: newValue } 
          }));
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Auto-save ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleKeyboardNavigation: () => {
        const newValue = !get().keyboardNavigation;
        set({ keyboardNavigation: newValue });
        
        // Update keyboard navigation indicators
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('keyboard-navigation-enabled', newValue);
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Keyboard navigation ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleScreenReaderMode: () => {
        const newValue = !get().screenReaderMode;
        set({ screenReaderMode: newValue });
        
        // Update screen reader optimizations
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('screen-reader-mode', newValue);
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Screen reader mode ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleLargeText: () => {
        const newValue = !get().largeText;
        set({ largeText: newValue });
        
        // Update text size
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('large-text', newValue);
        }
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Large text ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      toggleSound: () => {
        const newValue = !get().soundEnabled;
        set({ soundEnabled: newValue });
        
        // Announce change
        if (typeof window !== 'undefined') {
          const announcement = `Sound feedback ${newValue ? 'enabled' : 'disabled'}`;
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      resetToDefaults: () => {
        set(defaultThemeState);
        
        // Reset CSS classes
        if (typeof document !== 'undefined') {
          document.documentElement.className = '';
          document.body.className = '';
        }
        
        // Announce reset
        if (typeof window !== 'undefined') {
          const announcement = 'All accessibility settings reset to defaults';
          (window as any).announceToScreenReader?.(announcement);
        }
      },
      
      setSystemPreferences: (preferences) => {
        set({
          systemPrefersDark: preferences.prefersDark,
          systemPrefersReducedMotion: preferences.prefersReducedMotion,
          systemPrefersHighContrast: preferences.prefersHighContrast,
        });
      },
    }),
    {
      name: 'noxpanel-theme-storage',
      storage: createJSONStorage(() => localStorage),
      version: 1,
      migrate: (persistedState: any, version: number) => {
        // Handle migration from older versions
        if (version === 0) {
          return {
            ...defaultThemeState,
            ...persistedState,
          };
        }
        return persistedState;
      },
    }
  )
);

// Initialize system preferences detection
if (typeof window !== 'undefined') {
  const detectSystemPreferences = () => {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
    
    useThemeStore.getState().setSystemPreferences({
      prefersDark,
      prefersReducedMotion,
      prefersHighContrast,
    });
  };
  
  // Initial detection
  detectSystemPreferences();
  
  // Listen for changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', detectSystemPreferences);
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', detectSystemPreferences);
  window.matchMedia('(prefers-contrast: high)').addEventListener('change', detectSystemPreferences);
}