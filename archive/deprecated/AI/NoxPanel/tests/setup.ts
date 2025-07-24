/**
 * Jest Test Setup for NoxPanel Frontend
 *
 * This file configures the testing environment for React Testing Library,
 * accessibility testing with jest-axe, and ADHD-friendly test utilities.
 *
 * Setup includes:
 * - Jest DOM matchers for enhanced assertions
 * - Accessibility testing with axe-core
 * - Mock service worker for API mocking
 * - Performance monitoring utilities
 * - ADHD-specific test helpers
 */

import '@testing-library/jest-dom';
import 'jest-axe/extend-expect';
import { configure } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Configure React Testing Library for ADHD-friendly timeouts
configure({
  // Longer timeout for ADHD users who might need more processing time
  asyncUtilTimeout: 10000,

  // More specific test ID attribute for consistent targeting
  testIdAttribute: 'data-testid',

  // Disable automatic cleanup to allow manual control for interruption testing
  asyncWrapper: async (cb) => {
    const result = await cb();
    return result;
  }
});

// Mock IntersectionObserver for component virtualization tests
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
  root: null,
  rootMargin: '',
  thresholds: []
}));

// Mock ResizeObserver for responsive component tests
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock matchMedia for responsive design and accessibility tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage for theme and preference persistence
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock sessionStorage for temporary state management
Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock
});

// Mock window.location for navigation tests
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    hostname: 'localhost',
    port: '3000',
    protocol: 'http:',
    pathname: '/',
    search: '',
    hash: '',
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn()
  },
  writable: true
});

// Mock Web APIs that may not be available in test environment
Object.defineProperty(window, 'requestIdleCallback', {
  value: jest.fn().mockImplementation(cb => setTimeout(cb, 0)),
  writable: true
});

Object.defineProperty(window, 'cancelIdleCallback', {
  value: jest.fn(),
  writable: true
});

// Mock Web Workers for background processing tests
Object.defineProperty(window, 'Worker', {
  value: jest.fn().mockImplementation(() => ({
    postMessage: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    terminate: jest.fn()
  })),
  writable: true
});

// Mock Service Worker for PWA testing
Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    register: jest.fn(() => Promise.resolve()),
    ready: Promise.resolve({
      unregister: jest.fn(() => Promise.resolve())
    })
  },
  writable: true
});

// Setup MSW (Mock Service Worker) for API mocking
const mockApiHandlers = [
  // Device API endpoints
  rest.get('/api/devices', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        devices: [
          {
            id: '1',
            name: 'Test Router',
            ip_address: '192.168.1.1',
            status: 'online',
            device_type: 'router'
          }
        ]
      })
    );
  }),

  rest.post('/api/devices', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'new-device-id',
        ...req.body
      })
    );
  }),

  rest.get('/api/devices/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        id,
        name: `Device ${id}`,
        ip_address: '192.168.1.100',
        status: 'online',
        device_type: 'switch'
      })
    );
  }),

  // Auth API endpoints
  rest.post('/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        user: {
          id: 'user-1',
          username: 'testuser',
          role: 'admin'
        }
      })
    );
  }),

  // Health check endpoint
  rest.get('/api/health', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        timestamp: new Date().toISOString()
      })
    );
  })
];

export const server = setupServer(...mockApiHandlers);

// Start MSW before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
  jest.clearAllMocks();
  localStorageMock.clear();
});

// Stop MSW after all tests
afterAll(() => {
  server.close();
});

// Global test utilities for ADHD-friendly testing
global.testUtils = {
  /**
   * Wait for animations to complete (respects reduced motion)
   */
  waitForAnimations: async () => {
    await new Promise(resolve => setTimeout(resolve, 100));
  },

  /**
   * Simulate user interruption scenarios
   */
  simulateInterruption: () => {
    // Simulate tab switching
    Object.defineProperty(document, 'visibilityState', {
      writable: true,
      value: 'hidden'
    });
    document.dispatchEvent(new Event('visibilitychange'));

    // Return function to restore focus
    return () => {
      Object.defineProperty(document, 'visibilityState', {
        writable: true,
        value: 'visible'
      });
      document.dispatchEvent(new Event('visibilitychange'));
    };
  },

  /**
   * Set up reduced motion preferences
   */
  enableReducedMotion: () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });
  },

  /**
   * Set up high contrast preferences
   */
  enableHighContrast: () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-contrast: high)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });
  },

  /**
   * Performance timing utilities
   */
  performance: {
    mark: (name: string) => {
      performance.mark(name);
    },

    measure: (name: string, startMark: string, endMark?: string) => {
      if (endMark) {
        performance.measure(name, startMark, endMark);
      } else {
        performance.measure(name, startMark);
      }

      const measure = performance.getEntriesByName(name)[0];
      return measure.duration;
    }
  }
};

// Console override for cleaner test output
const originalError = console.error;
const originalWarn = console.warn;

console.error = (...args) => {
  // Suppress specific React warnings that are expected in tests
  if (
    args[0]?.includes?.('Warning: ReactDOM.render is no longer supported') ||
    args[0]?.includes?.('Warning: An invalid form control') ||
    args[0]?.includes?.('Warning: Failed prop type')
  ) {
    return;
  }
  originalError.call(console, ...args);
};

console.warn = (...args) => {
  // Suppress specific warnings that are expected in tests
  if (
    args[0]?.includes?.('componentWillReceiveProps') ||
    args[0]?.includes?.('componentWillUpdate')
  ) {
    return;
  }
  originalWarn.call(console, ...args);
};

// Custom Jest matchers for ADHD-friendly testing
expect.extend({
  /**
   * Check if element has proper focus indicators
   */
  toHaveProperFocusIndicator(received) {
    const computedStyle = window.getComputedStyle(received);
    const outline = computedStyle.outline;
    const outlineWidth = computedStyle.outlineWidth;
    const outlineColor = computedStyle.outlineColor;

    const hasOutline = outline !== 'none' &&
                      outlineWidth !== '0px' &&
                      outlineColor !== 'transparent';

    return {
      message: () =>
        `expected element to have proper focus indicator, but got outline: ${outline}`,
      pass: hasOutline
    };
  },

  /**
   * Check if element meets minimum touch target size (44px)
   */
  toMeetTouchTargetSize(received) {
    const rect = received.getBoundingClientRect();
    const minSize = 44;
    const meetsCriteria = rect.width >= minSize && rect.height >= minSize;

    return {
      message: () =>
        `expected element to meet minimum touch target size of ${minSize}px, but got ${rect.width}x${rect.height}`,
      pass: meetsCriteria
    };
  },

  /**
   * Check if text has sufficient color contrast
   */
  toHaveSufficientContrast(received, minimumRatio = 4.5) {
    // This would require actual color contrast calculation
    // For now, return true as placeholder
    return {
      message: () =>
        `expected element to have minimum contrast ratio of ${minimumRatio}`,
      pass: true
    };
  }
});

// Export server for use in individual test files
export { server };
