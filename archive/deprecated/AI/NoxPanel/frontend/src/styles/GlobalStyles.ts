import { createGlobalStyle } from 'styled-components';

const GlobalStyles = createGlobalStyle`
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  html {
    font-size: 16px;
    scroll-behavior: smooth;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background: var(--background-color);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    transition: all var(--transition-duration) ease;
  }

  :root {
    /* Default Light Theme */
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
    --accent-color: #e74c3c;
    --background-color: #f8f9fa;
    --surface-color: #ffffff;
    --text-color: #2c3e50;
    --text-muted: #6c757d;
    --border-color: #dee2e6;
    --shadow-color: rgba(0, 0, 0, 0.1);

    /* Animation Variables */
    --transition-duration: 0.3s;
    --hover-scale: 1.05;
    --border-radius: 8px;

    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;

    /* Typography */
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-md: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 2rem;

    /* Z-index */
    --z-dropdown: 1000;
    --z-sticky: 1020;
    --z-fixed: 1030;
    --z-modal-backdrop: 1040;
    --z-modal: 1050;
    --z-popover: 1060;
    --z-tooltip: 1070;
  }

  /* Dark Theme */
  [data-theme="dark"] {
    --primary-color: #4A90E2;
    --secondary-color: #7ED321;
    --accent-color: #F5A623;
    --background-color: #1a1a2e;
    --surface-color: #16213e;
    --text-color: #eee;
    --text-muted: #a0a0a0;
    --border-color: #333;
    --shadow-color: rgba(0, 0, 0, 0.3);
  }

  /* ADHD-Friendly Theme */
  [data-theme="adhd"] {
    --primary-color: #8E44AD;
    --secondary-color: #27AE60;
    --accent-color: #F39C12;
    --background-color: #F7F1FF;
    --surface-color: #FFFFFF;
    --text-color: #2C3E50;
    --text-muted: #7F8C8D;
    --border-color: #E8E8E8;
    --shadow-color: rgba(142, 68, 173, 0.1);
    --transition-duration: 0.2s;
    --border-radius: 12px;
  }

  /* High Contrast Theme */
  [data-theme="high-contrast"] {
    --primary-color: #000000;
    --secondary-color: #000000;
    --accent-color: #FF0000;
    --background-color: #FFFFFF;
    --surface-color: #F0F0F0;
    --text-color: #000000;
    --text-muted: #333333;
    --border-color: #000000;
    --shadow-color: rgba(0, 0, 0, 0.5);
  }

  /* Neon Theme */
  [data-theme="neon"] {
    --primary-color: #00FFFF;
    --secondary-color: #FF00FF;
    --accent-color: #FFFF00;
    --background-color: #0A0A0A;
    --surface-color: #1A1A1A;
    --text-color: #00FFFF;
    --text-muted: #808080;
    --border-color: #00FFFF;
    --shadow-color: rgba(0, 255, 255, 0.3);
  }

  /* Corporate Theme */
  [data-theme="corporate"] {
    --primary-color: #2E4A87;
    --secondary-color: #5B8A3A;
    --accent-color: #C5282F;
    --background-color: #FAFAFA;
    --surface-color: #FFFFFF;
    --text-color: #333333;
    --text-muted: #666666;
    --border-color: #CCCCCC;
    --shadow-color: rgba(0, 0, 0, 0.08);
  }

  /* Accessibility Improvements */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }

  @media (prefers-contrast: high) {
    :root {
      --border-color: #000000;
      --shadow-color: rgba(0, 0, 0, 0.8);
    }
  }

  /* Focus indicators */
  *:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
  }

  button:focus,
  input:focus,
  select:focus,
  textarea:focus,
  [tabindex]:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: var(--background-color);
  }

  ::-webkit-scrollbar-thumb {
    background: var(--text-muted);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: var(--text-color);
  }

  /* Selection styling */
  ::selection {
    background: var(--primary-color);
    color: white;
  }

  ::-moz-selection {
    background: var(--primary-color);
    color: white;
  }

  /* Animation keyframes */
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
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

  @keyframes slideInRight {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  @keyframes bounce {
    0%, 20%, 53%, 80%, 100% {
      transform: translate3d(0, 0, 0);
    }
    40%, 43% {
      transform: translate3d(0, -8px, 0);
    }
    70% {
      transform: translate3d(0, -4px, 0);
    }
    90% {
      transform: translate3d(0, -2px, 0);
    }
  }

  /* Utility classes */
  .fade-in {
    animation: fadeIn var(--transition-duration) ease;
  }

  .slide-in-up {
    animation: slideInUp var(--transition-duration) ease;
  }

  .slide-in-right {
    animation: slideInRight var(--transition-duration) ease;
  }

  .pulse {
    animation: pulse 2s infinite;
  }

  .spin {
    animation: spin 1s linear infinite;
  }

  .bounce {
    animation: bounce 1s infinite;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    html {
      font-size: 14px;
    }
  }

  @media (max-width: 480px) {
    html {
      font-size: 12px;
    }
  }

  /* Print styles */
  @media print {
    * {
      background: white !important;
      color: black !important;
      box-shadow: none !important;
    }
  }
`;

export default GlobalStyles;
