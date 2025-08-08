import React from 'react';
import { Global, css } from '@emotion/react';
import { useTheme } from '@mui/material/styles';
import { designTokens } from './tokens';

export const GlobalStyles: React.FC = () => {
  const theme = useTheme();

  const globalStyles = css`
    /* ADHD-Friendly Global Reset */
    *, *::before, *::after {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
      -webkit-text-size-adjust: 100%;
      -moz-text-size-adjust: 100%;
      text-size-adjust: 100%;
    }

    body {
      margin: 0;
      padding: 0;
      font-family: ${theme.typography.fontFamily};
      font-size: ${designTokens.typography.fontSize.base[0]};
      line-height: 1.6;
      color: ${theme.palette.text.primary};
      background-color: ${theme.palette.background.default};
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* ADHD-Friendly Focus Management */
    :focus {
      outline: ${designTokens.adhd.focusRing.width} ${designTokens.adhd.focusRing.style} ${designTokens.adhd.focusRing.color} !important;
      outline-offset: ${designTokens.adhd.focusRing.offset} !important;
      border-radius: ${designTokens.borderRadius.md} !important;
    }

    :focus:not(:focus-visible) {
      outline: none !important;
    }

    :focus-visible {
      outline: ${designTokens.adhd.focusRing.width} ${designTokens.adhd.focusRing.style} ${designTokens.adhd.focusRing.color} !important;
      outline-offset: ${designTokens.adhd.focusRing.offset} !important;
    }

    /* Skip to main content link */
    .skip-link {
      position: absolute;
      top: -40px;
      left: 6px;
      background: ${theme.palette.primary.main};
      color: ${theme.palette.primary.contrastText};
      padding: ${designTokens.spacing[2]} ${designTokens.spacing[3]};
      text-decoration: none;
      border-radius: ${designTokens.borderRadius.md};
      z-index: ${designTokens.zIndex.tooltip};
      transition: top ${theme.transitions.duration.shortest}ms ${theme.transitions.easing.easeOut};
      font-weight: ${designTokens.typography.fontWeight.medium};
    }

    .skip-link:focus {
      top: 6px;
    }

    /* Reduced Motion Support */
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
      
      html {
        scroll-behavior: auto;
      }
    }

    /* High Contrast Mode */
    @media (prefers-contrast: high) {
      * {
        text-shadow: none !important;
        box-shadow: none !important;
      }
      
      button, input, select, textarea {
        border: 2px solid ${designTokens.adhd.highContrast.colors.border} !important;
      }
    }

    /* Screen Reader Only */
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    /* ADHD-Friendly Utility Classes */
    .adhd-focus-mode {
      filter: none !important;
      opacity: 1 !important;
      background: ${theme.palette.background.paper} !important;
      backdrop-filter: blur(8px) !important;
      border: 2px solid ${theme.palette.primary.main} !important;
      border-radius: ${designTokens.borderRadius.lg} !important;
      box-shadow: ${designTokens.boxShadow.lg} !important;
      z-index: ${designTokens.zIndex.sticky} !important;
    }

    .adhd-reduced-noise {
      background-image: none !important;
      box-shadow: ${designTokens.boxShadow.sm} !important;
      border: 1px solid ${theme.palette.divider} !important;
    }

    .adhd-high-contrast {
      filter: contrast(200%) !important;
      border: 2px solid ${theme.palette.text.primary} !important;
    }

    /* Auto-save indicator */
    .auto-save-indicator {
      position: fixed;
      top: ${designTokens.spacing[4]};
      right: ${designTokens.spacing[4]};
      background: ${theme.palette.success.main};
      color: ${theme.palette.success.contrastText};
      padding: ${designTokens.spacing[2]} ${designTokens.spacing[3]};
      border-radius: ${designTokens.borderRadius.md};
      font-size: ${designTokens.typography.fontSize.sm[0]};
      font-weight: ${designTokens.typography.fontWeight.medium};
      z-index: ${designTokens.zIndex.toast};
      opacity: 0;
      transform: translateY(-10px);
      transition: 
        opacity ${theme.transitions.duration.short}ms ${theme.transitions.easing.easeOut},
        transform ${theme.transitions.duration.short}ms ${theme.transitions.easing.easeOut};
    }

    .auto-save-indicator.show {
      opacity: 1;
      transform: translateY(0);
    }

    /* Loading States */
    .skeleton {
      background: linear-gradient(
        90deg,
        ${theme.palette.grey[200]} 25%,
        ${theme.palette.grey[100]} 50%,
        ${theme.palette.grey[200]} 75%
      );
      background-size: 200% 100%;
      animation: loading 1.5s infinite;
      border-radius: ${designTokens.borderRadius.md};
    }

    @keyframes loading {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Error and Success States */
    .error-message {
      color: ${theme.palette.error.main};
      font-weight: ${designTokens.typography.fontWeight.medium};
      display: flex;
      align-items: center;
      gap: ${designTokens.spacing[2]};
      padding: ${designTokens.spacing[2]};
      background: ${theme.palette.error.light}20;
      border: 1px solid ${theme.palette.error.light};
      border-radius: ${designTokens.borderRadius.md};
    }

    .success-message {
      color: ${theme.palette.success.main};
      font-weight: ${designTokens.typography.fontWeight.medium};
      display: flex;
      align-items: center;
      gap: ${designTokens.spacing[2]};
      padding: ${designTokens.spacing[2]};
      background: ${theme.palette.success.light}20;
      border: 1px solid ${theme.palette.success.light};
      border-radius: ${designTokens.borderRadius.md};
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    ::-webkit-scrollbar-track {
      background: ${theme.palette.grey[100]};
      border-radius: ${designTokens.borderRadius.md};
    }

    ::-webkit-scrollbar-thumb {
      background: ${theme.palette.grey[300]};
      border-radius: ${designTokens.borderRadius.md};
    }

    ::-webkit-scrollbar-thumb:hover {
      background: ${theme.palette.grey[400]};
    }

    /* Dark mode scrollbars */
    @media (prefers-color-scheme: dark) {
      ::-webkit-scrollbar-track {
        background: ${theme.palette.grey[800]};
      }

      ::-webkit-scrollbar-thumb {
        background: ${theme.palette.grey[600]};
      }

      ::-webkit-scrollbar-thumb:hover {
        background: ${theme.palette.grey[500]};
      }
    }

    /* Print Styles */
    @media print {
      * {
        background: transparent !important;
        color: black !important;
        box-shadow: none !important;
        text-shadow: none !important;
      }
      
      a {
        text-decoration: underline;
      }
      
      .no-print {
        display: none !important;
      }
      
      .print-break {
        page-break-before: always;
      }
    }

    /* Focus trap for modals */
    .focus-trap {
      position: relative;
    }

    .focus-trap::before,
    .focus-trap::after {
      content: '';
      position: absolute;
      width: 1px;
      height: 1px;
      opacity: 0;
      pointer-events: none;
    }

    /* Keyboard navigation indicators */
    .keyboard-navigation-active {
      outline: 2px solid ${theme.palette.primary.main};
      outline-offset: 2px;
    }

    /* Responsive utilities */
    @media (max-width: ${designTokens.breakpoints.sm}) {
      .hide-mobile {
        display: none !important;
      }
    }

    @media (min-width: ${designTokens.breakpoints.md}) {
      .hide-desktop {
        display: none !important;
      }
    }

    /* Animation classes for ADHD-friendly transitions */
    .fade-in {
      animation: fadeIn ${theme.transitions.duration.standard}ms ${theme.transitions.easing.easeOut};
    }

    .slide-in-up {
      animation: slideInUp ${theme.transitions.duration.standard}ms ${theme.transitions.easing.easeOut};
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* Live region for screen reader announcements */
    .live-region {
      position: absolute;
      left: -10000px;
      width: 1px;
      height: 1px;
      overflow: hidden;
    }

    /* Text selection */
    ::selection {
      background: ${theme.palette.primary.main}40;
      color: ${theme.palette.text.primary};
    }

    ::-moz-selection {
      background: ${theme.palette.primary.main}40;
      color: ${theme.palette.text.primary};
    }
  `;

  return <Global styles={globalStyles} />;
};