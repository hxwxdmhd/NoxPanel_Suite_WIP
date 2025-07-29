/**
 * ADHD-Friendly Theme Configuration for NoxPanel
 * Designed with accessibility, focus management, and reduced cognitive load in mind
 */

export const adhdFriendlyTheme = (mode = 'light', accessibility = {}) => {
  const isDark = mode === 'dark';
  const {
    highContrast = false,
    reduceMotion = false,
    largerText = false,
    focusIndicators = true
  } = accessibility;

  // Color palette with ADHD-friendly considerations
  const colors = {
    light: {
      primary: {
        main: highContrast ? '#0066cc' : '#1976d2',
        light: highContrast ? '#3399ff' : '#42a5f5',
        dark: highContrast ? '#004499' : '#1565c0',
        contrastText: '#ffffff',
      },
      secondary: {
        main: highContrast ? '#cc6600' : '#ff9800',
        light: highContrast ? '#ff9933' : '#ffb74d',
        dark: highContrast ? '#994d00' : '#f57c00',
        contrastText: '#ffffff',
      },
      error: {
        main: highContrast ? '#cc0000' : '#f44336',
        light: highContrast ? '#ff3333' : '#e57373',
        dark: highContrast ? '#990000' : '#d32f2f',
      },
      warning: {
        main: highContrast ? '#cc8800' : '#ff9800',
        light: highContrast ? '#ffaa33' : '#ffb74d',
        dark: highContrast ? '#996600' : '#f57c00',
      },
      info: {
        main: highContrast ? '#0099cc' : '#2196f3',
        light: highContrast ? '#33aadd' : '#64b5f6',
        dark: highContrast ? '#007799' : '#1976d2',
      },
      success: {
        main: highContrast ? '#009900' : '#4caf50',
        light: highContrast ? '#33cc33' : '#81c784',
        dark: highContrast ? '#006600' : '#388e3c',
      },
      background: {
        default: highContrast ? '#ffffff' : '#fafafa',
        paper: highContrast ? '#ffffff' : '#ffffff',
        surface: highContrast ? '#f0f0f0' : '#f5f5f5',
      },
      text: {
        primary: highContrast ? '#000000' : '#212121',
        secondary: highContrast ? '#333333' : '#757575',
        disabled: highContrast ? '#666666' : '#9e9e9e',
      },
    },
    dark: {
      primary: {
        main: highContrast ? '#66b3ff' : '#90caf9',
        light: highContrast ? '#99ccff' : '#bbdefb',
        dark: highContrast ? '#3399ff' : '#64b5f6',
        contrastText: '#000000',
      },
      secondary: {
        main: highContrast ? '#ffaa33' : '#ffb74d',
        light: highContrast ? '#ffcc66' : '#ffd54f',
        dark: highContrast ? '#ff9900' : '#ff9800',
        contrastText: '#000000',
      },
      error: {
        main: highContrast ? '#ff6666' : '#ef5350',
        light: highContrast ? '#ff9999' : '#e57373',
        dark: highContrast ? '#ff3333' : '#e53935',
      },
      warning: {
        main: highContrast ? '#ffcc33' : '#ff9800',
        light: highContrast ? '#ffdd66' : '#ffb74d',
        dark: highContrast ? '#ffaa00' : '#f57c00',
      },
      info: {
        main: highContrast ? '#66ccff' : '#29b6f6',
        light: highContrast ? '#99ddff' : '#4fc3f7',
        dark: highContrast ? '#3399ff' : '#0288d1',
      },
      success: {
        main: highContrast ? '#66ff66' : '#66bb6a',
        light: highContrast ? '#99ff99' : '#81c784',
        dark: highContrast ? '#33ff33' : '#4caf50',
      },
      background: {
        default: highContrast ? '#000000' : '#121212',
        paper: highContrast ? '#1a1a1a' : '#1e1e1e',
        surface: highContrast ? '#2a2a2a' : '#2d2d2d',
      },
      text: {
        primary: highContrast ? '#ffffff' : '#ffffff',
        secondary: highContrast ? '#cccccc' : '#aaaaaa',
        disabled: highContrast ? '#999999' : '#666666',
      },
    },
  };

  const palette = colors[isDark ? 'dark' : 'light'];

  return {
    palette: {
      mode,
      ...palette,
      divider: highContrast 
        ? (isDark ? '#666666' : '#cccccc')
        : (isDark ? '#333333' : '#e0e0e0'),
    },
    typography: {
      fontFamily: [
        '-apple-system',
        'BlinkMacSystemFont',
        '"Segoe UI"',
        'Roboto',
        '"Helvetica Neue"',
        'Arial',
        'sans-serif',
      ].join(','),
      fontSize: largerText ? 16 : 14,
      h1: {
        fontSize: largerText ? '3rem' : '2.5rem',
        fontWeight: 600,
        lineHeight: 1.2,
      },
      h2: {
        fontSize: largerText ? '2.5rem' : '2rem',
        fontWeight: 600,
        lineHeight: 1.2,
      },
      h3: {
        fontSize: largerText ? '2rem' : '1.75rem',
        fontWeight: 600,
        lineHeight: 1.2,
      },
      h4: {
        fontSize: largerText ? '1.75rem' : '1.5rem',
        fontWeight: 600,
        lineHeight: 1.3,
      },
      h5: {
        fontSize: largerText ? '1.5rem' : '1.25rem',
        fontWeight: 600,
        lineHeight: 1.3,
      },
      h6: {
        fontSize: largerText ? '1.25rem' : '1.125rem',
        fontWeight: 600,
        lineHeight: 1.3,
      },
      body1: {
        fontSize: largerText ? '1.125rem' : '1rem',
        lineHeight: 1.6,
      },
      body2: {
        fontSize: largerText ? '1rem' : '0.875rem',
        lineHeight: 1.6,
      },
      button: {
        fontSize: largerText ? '1rem' : '0.875rem',
        fontWeight: 600,
        lineHeight: 1.4,
        textTransform: 'none',
      },
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            padding: '12px 24px',
            textTransform: 'none',
            fontWeight: 600,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            border: highContrast ? `2px solid ${palette.divider}` : 'none',
          },
        },
      },
    },
  };
};