import { createTheme, Theme, ThemeOptions } from '@mui/material/styles';
import { designTokens } from './tokens';

interface CustomThemeOptions {
  mode: 'light' | 'dark';
  isHighContrast?: boolean;
  isReducedMotion?: boolean;
}

export const createCustomTheme = ({
  mode,
  isHighContrast = false,
  isReducedMotion = false,
}: CustomThemeOptions): Theme => {
  const isLight = mode === 'light';
  
  const baseTheme: ThemeOptions = {
    palette: {
      mode,
      primary: {
        50: designTokens.colors.primary[50],
        100: designTokens.colors.primary[100],
        200: designTokens.colors.primary[200],
        300: designTokens.colors.primary[300],
        400: designTokens.colors.primary[400],
        500: designTokens.colors.primary[500],
        600: designTokens.colors.primary[600],
        700: designTokens.colors.primary[700],
        800: designTokens.colors.primary[800],
        900: designTokens.colors.primary[900],
        main: isHighContrast 
          ? designTokens.adhd.highContrast.colors.focus
          : designTokens.colors.primary[600],
        contrastText: isLight ? '#ffffff' : '#000000',
      },
      secondary: {
        50: designTokens.colors.secondary[50],
        100: designTokens.colors.secondary[100],
        200: designTokens.colors.secondary[200],
        300: designTokens.colors.secondary[300],
        400: designTokens.colors.secondary[400],
        500: designTokens.colors.secondary[500],
        600: designTokens.colors.secondary[600],
        700: designTokens.colors.secondary[700],
        800: designTokens.colors.secondary[800],
        900: designTokens.colors.secondary[900],
        main: designTokens.colors.secondary[600],
        contrastText: isLight ? '#ffffff' : '#000000',
      },
      error: {
        50: designTokens.colors.error[50],
        100: designTokens.colors.error[100],
        200: designTokens.colors.error[200],
        300: designTokens.colors.error[300],
        400: designTokens.colors.error[400],
        500: designTokens.colors.error[500],
        600: designTokens.colors.error[600],
        700: designTokens.colors.error[700],
        800: designTokens.colors.error[800],
        900: designTokens.colors.error[900],
        main: isHighContrast 
          ? designTokens.adhd.highContrast.colors.error
          : designTokens.colors.error[600],
        contrastText: '#ffffff',
      },
      warning: {
        50: designTokens.colors.warning[50],
        100: designTokens.colors.warning[100],
        200: designTokens.colors.warning[200],
        300: designTokens.colors.warning[300],
        400: designTokens.colors.warning[400],
        500: designTokens.colors.warning[500],
        600: designTokens.colors.warning[600],
        700: designTokens.colors.warning[700],
        800: designTokens.colors.warning[800],
        900: designTokens.colors.warning[900],
        main: isHighContrast 
          ? designTokens.adhd.highContrast.colors.warning
          : designTokens.colors.warning[600],
        contrastText: '#ffffff',
      },
      success: {
        50: designTokens.colors.success[50],
        100: designTokens.colors.success[100],
        200: designTokens.colors.success[200],
        300: designTokens.colors.success[300],
        400: designTokens.colors.success[400],
        500: designTokens.colors.success[500],
        600: designTokens.colors.success[600],
        700: designTokens.colors.success[700],
        800: designTokens.colors.success[800],
        900: designTokens.colors.success[900],
        main: isHighContrast 
          ? designTokens.adhd.highContrast.colors.success
          : designTokens.colors.success[600],
        contrastText: '#ffffff',
      },
      background: {
        default: isLight 
          ? (isHighContrast ? designTokens.adhd.highContrast.colors.background : '#ffffff')
          : (isHighContrast ? '#000000' : designTokens.colors.neutral[900]),
        paper: isLight 
          ? (isHighContrast ? designTokens.adhd.highContrast.colors.background : '#ffffff')
          : (isHighContrast ? '#000000' : designTokens.colors.neutral[800]),
      },
      text: {
        primary: isLight 
          ? (isHighContrast ? designTokens.adhd.highContrast.colors.text : designTokens.colors.neutral[900])
          : (isHighContrast ? '#ffffff' : designTokens.colors.neutral[50]),
        secondary: isLight 
          ? designTokens.colors.neutral[600]
          : designTokens.colors.neutral[400],
        disabled: isLight 
          ? designTokens.colors.neutral[400]
          : designTokens.colors.neutral[600],
      },
      divider: isLight 
        ? (isHighContrast ? designTokens.adhd.highContrast.colors.border : designTokens.colors.neutral[200])
        : (isHighContrast ? '#ffffff' : designTokens.colors.neutral[700]),
    },
    
    typography: {
      fontFamily: designTokens.typography.fontFamily.sans.join(','),
      h1: {
        fontSize: designTokens.typography.fontSize['4xl'][0],
        fontWeight: designTokens.typography.fontWeight.bold,
        lineHeight: designTokens.typography.fontSize['4xl'][1].lineHeight,
        letterSpacing: '-0.025em',
      },
      h2: {
        fontSize: designTokens.typography.fontSize['3xl'][0],
        fontWeight: designTokens.typography.fontWeight.semibold,
        lineHeight: designTokens.typography.fontSize['3xl'][1].lineHeight,
        letterSpacing: '-0.025em',
      },
      h3: {
        fontSize: designTokens.typography.fontSize['2xl'][0],
        fontWeight: designTokens.typography.fontWeight.semibold,
        lineHeight: designTokens.typography.fontSize['2xl'][1].lineHeight,
      },
      h4: {
        fontSize: designTokens.typography.fontSize.xl[0],
        fontWeight: designTokens.typography.fontWeight.semibold,
        lineHeight: designTokens.typography.fontSize.xl[1].lineHeight,
      },
      h5: {
        fontSize: designTokens.typography.fontSize.lg[0],
        fontWeight: designTokens.typography.fontWeight.medium,
        lineHeight: designTokens.typography.fontSize.lg[1].lineHeight,
      },
      h6: {
        fontSize: designTokens.typography.fontSize.base[0],
        fontWeight: designTokens.typography.fontWeight.medium,
        lineHeight: designTokens.typography.fontSize.base[1].lineHeight,
      },
      body1: {
        fontSize: designTokens.typography.fontSize.base[0],
        lineHeight: '1.6', // ADHD-friendly line height
      },
      body2: {
        fontSize: designTokens.typography.fontSize.sm[0],
        lineHeight: '1.6',
      },
      button: {
        fontSize: designTokens.typography.fontSize.sm[0],
        fontWeight: designTokens.typography.fontWeight.medium,
        textTransform: 'none' as const,
        letterSpacing: '0.025em',
      },
      caption: {
        fontSize: designTokens.typography.fontSize.xs[0],
        lineHeight: designTokens.typography.fontSize.xs[1].lineHeight,
      },
      overline: {
        fontSize: designTokens.typography.fontSize.xs[0],
        fontWeight: designTokens.typography.fontWeight.semibold,
        textTransform: 'uppercase' as const,
        letterSpacing: '0.1em',
      },
    },
    
    spacing: (factor: number) => `${0.25 * factor}rem`,
    
    shape: {
      borderRadius: parseInt(designTokens.borderRadius.md.replace('rem', '')) * 16,
    },
    
    shadows: [
      'none',
      designTokens.boxShadow.sm,
      designTokens.boxShadow.base,
      designTokens.boxShadow.md,
      designTokens.boxShadow.lg,
      designTokens.boxShadow.xl,
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow.xl,
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
      designTokens.boxShadow['2xl'],
    ],
    
    transitions: {
      duration: {
        shortest: isReducedMotion ? 1 : 150,
        shorter: isReducedMotion ? 1 : 200,
        short: isReducedMotion ? 1 : 250,
        standard: isReducedMotion ? 1 : 300,
        complex: isReducedMotion ? 1 : 375,
        enteringScreen: isReducedMotion ? 1 : 225,
        leavingScreen: isReducedMotion ? 1 : 195,
      },
      easing: {
        easeInOut: isReducedMotion ? 'linear' : 'cubic-bezier(0.4, 0, 0.2, 1)',
        easeOut: isReducedMotion ? 'linear' : 'cubic-bezier(0.0, 0, 0.2, 1)',
        easeIn: isReducedMotion ? 'linear' : 'cubic-bezier(0.4, 0, 1, 1)',
        sharp: isReducedMotion ? 'linear' : 'cubic-bezier(0.4, 0, 0.6, 1)',
      },
    },
    
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: designTokens.borderRadius.lg,
            textTransform: 'none',
            fontWeight: designTokens.typography.fontWeight.medium,
            padding: `${designTokens.spacing[2]} ${designTokens.spacing[4]}`,
            '&:focus': {
              outline: `${designTokens.adhd.focusRing.width} ${designTokens.adhd.focusRing.style} ${designTokens.adhd.focusRing.color}`,
              outlineOffset: designTokens.adhd.focusRing.offset,
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: designTokens.borderRadius.lg,
              '&:focus-within': {
                outline: `${designTokens.adhd.focusRing.width} ${designTokens.adhd.focusRing.style} ${designTokens.adhd.focusRing.color}`,
                outlineOffset: designTokens.adhd.focusRing.offset,
              },
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: designTokens.borderRadius.xl,
            boxShadow: designTokens.boxShadow.md,
            border: isHighContrast ? `2px solid ${designTokens.adhd.highContrast.colors.border}` : 'none',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: designTokens.borderRadius.full,
            fontWeight: designTokens.typography.fontWeight.medium,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: designTokens.boxShadow.sm,
            backdropFilter: 'blur(8px)',
            backgroundColor: isLight ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)',
          },
        },
      },
    },
  };

  return createTheme(baseTheme);
};

// Light theme
export const lightTheme = createCustomTheme({ mode: 'light' });

// Dark theme
export const darkTheme = createCustomTheme({ mode: 'dark' });

// High contrast light theme
export const highContrastLightTheme = createCustomTheme({ 
  mode: 'light', 
  isHighContrast: true 
});

// High contrast dark theme
export const highContrastDarkTheme = createCustomTheme({ 
  mode: 'dark', 
  isHighContrast: true 
});

// Reduced motion themes
export const reducedMotionLightTheme = createCustomTheme({ 
  mode: 'light', 
  isReducedMotion: true 
});

export const reducedMotionDarkTheme = createCustomTheme({ 
  mode: 'dark', 
  isReducedMotion: true 
});