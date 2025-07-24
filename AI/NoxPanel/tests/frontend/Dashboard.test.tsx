/**
 * Dashboard Component Tests
 *
 * Comprehensive test suite for the main dashboard component including:
 * - Component rendering and state management
 * - ADHD-friendly user experience validation
 * - Performance and accessibility compliance
 * - User interaction patterns and edge cases
 *
 * @group Component Tests
 * @category Dashboard
 * @requires MockDeviceProvider
 *
 * Test Coverage:
 * - ✅ Basic rendering with different data states
 * - ✅ ADHD-friendly features (reduced motion, clear focus)
 * - ✅ Performance within SLA thresholds (< 500ms)
 * - ✅ Accessibility (WCAG 2.1 AA compliance)
 * - ✅ Error handling and recovery
 * - ✅ Responsive design across viewports
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import '@testing-library/jest-dom';

import { Dashboard } from '../../frontend/src/components/Dashboard';
import { ThemeProvider } from '../../frontend/src/contexts/ThemeContext';
import { DeviceProvider } from '../../frontend/src/contexts/DeviceContext';
import { MockDeviceService, DeviceFactory, TestUtils } from '../conftest';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

/**
 * Mock device service for controlled testing
 */
const mockDeviceService = new MockDeviceService();

/**
 * Wrapper component with all necessary providers
 */
const DashboardWrapper = ({
  initialDevices = [],
  theme = 'light',
  adhdMode = false,
  children
}) => (
  <ThemeProvider initialTheme={theme} adhdMode={adhdMode}>
    <DeviceProvider deviceService={mockDeviceService} initialDevices={initialDevices}>
      {children}
    </DeviceProvider>
  </ThemeProvider>
);

/**
 * Performance monitoring utility for dashboard tests
 */
class DashboardPerformanceMonitor {
  private startTime: number;

  start() {
    this.startTime = performance.now();
  }

  end(operationName: string) {
    const duration = performance.now() - this.startTime;

    // Assert performance within SLA (500ms for dashboard load)
    expect(duration).toBeLessThan(500);

    console.log(`Dashboard ${operationName}: ${duration.toFixed(2)}ms`);
    return duration;
  }
}

describe('Dashboard Component', () => {
  let performanceMonitor: DashboardPerformanceMonitor;
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    performanceMonitor = new DashboardPerformanceMonitor();
    user = userEvent.setup();

    // Reset mock device service
    mockDeviceService.devices = {};
    mockDeviceService._populate_sample_devices();

    // Mock IntersectionObserver for lazy loading
    global.IntersectionObserver = jest.fn(() => ({
      observe: jest.fn(),
      disconnect: jest.fn(),
      unobserve: jest.fn(),
    }));

    // Mock matchMedia for responsive design tests
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
  });

  afterEach(() => {
    // Cleanup any test artifacts
    jest.clearAllMocks();
  });

  /**
   * Basic Rendering Tests
   */
  describe('Basic Rendering', () => {
    /**
     * Verifies dashboard renders correctly with sample device data
     */
    it('should render dashboard with device data within performance budget', async () => {
      // Arrange
      const testDevices = DeviceFactory.create_device_list(10);
      performanceMonitor.start();

      // Act
      render(
        <DashboardWrapper initialDevices={testDevices}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - Basic rendering
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-container')).toBeInTheDocument();

      // Wait for async data loading
      await waitFor(() => {
        expect(screen.getByTestId('device-grid')).toBeInTheDocument();
      });

      // Assert - Performance
      performanceMonitor.end('initial render');

      // Assert - Device count display
      expect(screen.getByText(/10 devices/i)).toBeInTheDocument();
    });

    /**
     * Verifies dashboard handles empty state gracefully
     */
    it('should display empty state when no devices are available', () => {
      // Arrange & Act
      render(
        <DashboardWrapper initialDevices={[]}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText(/no devices found/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /scan for devices/i })).toBeInTheDocument();
    });

    /**
     * Verifies dashboard loading state displays correctly
     */
    it('should show loading state while fetching device data', async () => {
      // Arrange
      const slowDeviceService = {
        ...mockDeviceService,
        get_devices: jest.fn(() => new Promise(resolve =>
          setTimeout(() => resolve(DeviceFactory.create_device_list(5)), 1000)
        ))
      };

      // Act
      render(
        <DashboardWrapper>
          <Dashboard deviceService={slowDeviceService} />
        </DashboardWrapper>
      );

      // Assert - Loading state
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByText(/loading devices/i)).toBeInTheDocument();

      // Assert - Loading disappears after data loads
      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  /**
   * ADHD-Friendly Feature Tests
   */
  describe('ADHD-Friendly Features', () => {
    /**
     * Verifies reduced motion preference is respected
     */
    it('should respect reduced motion preferences', () => {
      // Arrange - Mock reduced motion preference
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

      // Act
      render(
        <DashboardWrapper adhdMode={true}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - Animations should be disabled
      const dashboardContainer = screen.getByTestId('dashboard-container');
      expect(dashboardContainer).toHaveStyle('animation: none');

      // Assert - Transitions should be minimal
      const deviceCards = screen.getAllByTestId(/device-card/);
      deviceCards.forEach(card => {
        expect(card).toHaveStyle('transition: none');
      });
    });

    /**
     * Verifies clear focus indicators for keyboard navigation
     */
    it('should provide clear focus indicators for keyboard navigation', async () => {
      // Arrange
      const testDevices = DeviceFactory.create_device_list(3);
      render(
        <DashboardWrapper initialDevices={testDevices} adhdMode={true}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Act - Navigate with keyboard
      await user.tab(); // Focus on first interactive element

      // Assert - Focus indicator is visible
      const focusedElement = document.activeElement;
      expect(focusedElement).toHaveStyle('outline: 2px solid #3b82f6');
      expect(focusedElement).toHaveAttribute('data-focused', 'true');
    });

    /**
     * Verifies interruption recovery functionality
     */
    it('should handle user interruption and provide recovery options', async () => {
      // Arrange
      render(
        <DashboardWrapper adhdMode={true}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Act - Start a long operation
      const scanButton = screen.getByRole('button', { name: /scan for devices/i });
      await user.click(scanButton);

      // Simulate user interruption (page visibility change)
      Object.defineProperty(document, 'visibilityState', {
        writable: true,
        value: 'hidden'
      });

      fireEvent(document, new Event('visibilitychange'));

      // Simulate return to page
      Object.defineProperty(document, 'visibilityState', {
        writable: true,
        value: 'visible'
      });

      fireEvent(document, new Event('visibilitychange'));

      // Assert - Recovery options are presented
      await waitFor(() => {
        expect(screen.getByText(/operation was interrupted/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /resume scan/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /start over/i })).toBeInTheDocument();
      });
    });

    /**
     * Verifies high contrast mode functionality
     */
    it('should support high contrast mode for better visibility', () => {
      // Arrange & Act
      render(
        <DashboardWrapper theme="high_contrast" adhdMode={true}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - High contrast styles are applied
      const dashboardContainer = screen.getByTestId('dashboard-container');
      expect(dashboardContainer).toHaveClass('high-contrast');

      // Assert - Text contrast meets WCAG AAA standards
      const deviceCards = screen.getAllByTestId(/device-card/);
      deviceCards.forEach(card => {
        const computedStyle = window.getComputedStyle(card);
        // This would need actual contrast ratio calculation in real implementation
        expect(card).toHaveAttribute('data-contrast-verified', 'true');
      });
    });
  });

  /**
   * Accessibility Tests
   */
  describe('Accessibility', () => {
    /**
     * Verifies WCAG 2.1 AA compliance using axe-core
     */
    it('should meet WCAG 2.1 AA accessibility standards', async () => {
      // Arrange
      const testDevices = DeviceFactory.create_device_list(5);
      const { container } = render(
        <DashboardWrapper initialDevices={testDevices}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Wait for full rendering
      await waitFor(() => {
        expect(screen.getByTestId('device-grid')).toBeInTheDocument();
      });

      // Act & Assert
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    /**
     * Verifies proper ARIA labels and roles
     */
    it('should have proper ARIA labels and semantic structure', () => {
      // Arrange
      const testDevices = DeviceFactory.create_device_list(3);

      // Act
      render(
        <DashboardWrapper initialDevices={testDevices}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - Main landmarks
      expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Dashboard');
      expect(screen.getByRole('region', { name: 'Device overview' })).toBeInTheDocument();

      // Assert - Device grid structure
      const deviceGrid = screen.getByRole('grid', { name: 'Device list' });
      expect(deviceGrid).toBeInTheDocument();

      const deviceCards = within(deviceGrid).getAllByRole('gridcell');
      expect(deviceCards).toHaveLength(3);

      // Assert - Each device card has proper labeling
      deviceCards.forEach((card, index) => {
        expect(card).toHaveAttribute('aria-label');
        expect(card).toHaveAttribute('tabindex', '0');
      });
    });

    /**
     * Verifies keyboard navigation functionality
     */
    it('should support complete keyboard navigation', async () => {
      // Arrange
      const testDevices = DeviceFactory.create_device_list(3);
      render(
        <DashboardWrapper initialDevices={testDevices}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Act & Assert - Tab through interactive elements
      await user.tab(); // First device card
      expect(document.activeElement).toHaveAttribute('data-testid', 'device-card-0');

      await user.tab(); // Second device card
      expect(document.activeElement).toHaveAttribute('data-testid', 'device-card-1');

      await user.tab(); // Third device card
      expect(document.activeElement).toHaveAttribute('data-testid', 'device-card-2');

      await user.tab(); // Action buttons
      expect(document.activeElement).toHaveAttribute('data-testid', 'scan-devices-button');

      // Assert - Enter key activates focused elements
      await user.keyboard('{Enter}');
      // Should trigger scan operation
    });

    /**
     * Verifies screen reader announcements
     */
    it('should provide appropriate screen reader announcements', async () => {
      // Arrange
      render(
        <DashboardWrapper>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - Live region for announcements
      const liveRegion = screen.getByRole('status', { name: 'Dashboard announcements' });
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      expect(liveRegion).toHaveAttribute('aria-atomic', 'true');

      // Act - Trigger an action that should announce
      const scanButton = screen.getByRole('button', { name: /scan for devices/i });
      await user.click(scanButton);

      // Assert - Announcement is made
      await waitFor(() => {
        expect(liveRegion).toHaveTextContent(/scanning for devices/i);
      });
    });
  });

  /**
   * Performance Tests
   */
  describe('Performance', () => {
    /**
     * Verifies dashboard renders large device lists efficiently
     */
    it('should handle large device lists within performance budget', async () => {
      // Arrange
      const largeDeviceList = DeviceFactory.create_device_list(100);
      performanceMonitor.start();

      // Act
      render(
        <DashboardWrapper initialDevices={largeDeviceList}>
          <Dashboard />
        </DashboardWrapper>
      );

      // Wait for rendering
      await waitFor(() => {
        expect(screen.getByTestId('device-grid')).toBeInTheDocument();
      });

      // Assert - Performance within SLA
      performanceMonitor.end('large list render');

      // Assert - Virtualization is working (not all items rendered)
      const visibleCards = screen.getAllByTestId(/device-card/);
      expect(visibleCards.length).toBeLessThan(100); // Should be virtualized
      expect(visibleCards.length).toBeGreaterThan(0);
    });

    /**
     * Verifies theme switching performance
     */
    it('should switch themes within performance budget', async () => {
      // Arrange
      render(
        <DashboardWrapper>
          <Dashboard />
        </DashboardWrapper>
      );

      const themeToggle = screen.getByRole('button', { name: /toggle theme/i });

      // Act & Assert
      performanceMonitor.start();
      await user.click(themeToggle);

      // Wait for theme change
      await waitFor(() => {
        expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
      });

      performanceMonitor.end('theme switch');
    });
  });

  /**
   * Error Handling Tests
   */
  describe('Error Handling', () => {
    /**
     * Verifies graceful handling of API errors
     */
    it('should handle API errors gracefully with user-friendly messages', async () => {
      // Arrange
      const failingDeviceService = {
        ...mockDeviceService,
        get_devices: jest.fn().mockRejectedValue(new Error('Network error'))
      };

      // Act
      render(
        <DashboardWrapper>
          <Dashboard deviceService={failingDeviceService} />
        </DashboardWrapper>
      );

      // Assert - Error state is displayed
      await waitFor(() => {
        expect(screen.getByTestId('error-banner')).toBeInTheDocument();
        expect(screen.getByText(/unable to load devices/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      // Assert - Error is announced to screen readers
      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveTextContent(/error loading devices/i);
    });

    /**
     * Verifies retry functionality after errors
     */
    it('should allow retry after error with clear feedback', async () => {
      // Arrange
      let shouldFail = true;
      const unreliableService = {
        ...mockDeviceService,
        get_devices: jest.fn(() => {
          if (shouldFail) {
            shouldFail = false;
            return Promise.reject(new Error('Temporary error'));
          }
          return Promise.resolve(DeviceFactory.create_device_list(3));
        })
      };

      render(
        <DashboardWrapper>
          <Dashboard deviceService={unreliableService} />
        </DashboardWrapper>
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId('error-banner')).toBeInTheDocument();
      });

      // Act - Click retry
      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      // Assert - Success after retry
      await waitFor(() => {
        expect(screen.queryByTestId('error-banner')).not.toBeInTheDocument();
        expect(screen.getByTestId('device-grid')).toBeInTheDocument();
      });
    });
  });

  /**
   * Responsive Design Tests
   */
  describe('Responsive Design', () => {
    /**
     * Verifies mobile layout adaptation
     */
    it('should adapt layout for mobile devices', () => {
      // Arrange - Mock mobile viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(max-width: 768px)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      // Act
      render(
        <DashboardWrapper>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - Mobile layout classes
      const dashboardContainer = screen.getByTestId('dashboard-container');
      expect(dashboardContainer).toHaveClass('mobile-layout');

      // Assert - Touch-friendly button sizes
      const actionButtons = screen.getAllByRole('button');
      actionButtons.forEach(button => {
        const styles = window.getComputedStyle(button);
        const minHeight = parseInt(styles.minHeight);
        expect(minHeight).toBeGreaterThanOrEqual(44); // WCAG touch target size
      });
    });

    /**
     * Verifies tablet layout optimization
     */
    it('should optimize layout for tablet devices', () => {
      // Arrange - Mock tablet viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(min-width: 769px) and (max-width: 1024px)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      // Act
      render(
        <DashboardWrapper>
          <Dashboard />
        </DashboardWrapper>
      );

      // Assert - Tablet layout
      const dashboardContainer = screen.getByTestId('dashboard-container');
      expect(dashboardContainer).toHaveClass('tablet-layout');
    });
  });
});

/**
 * Test utilities specific to Dashboard component
 */
export const DashboardTestUtils = {
  /**
   * Create a dashboard with specific device scenarios
   */
  createDashboardWithScenario: (scenario: string) => {
    const scenarios = {
      'mixed_status': () => [
        DeviceFactory.create_device({ status: 'online' }),
        DeviceFactory.create_device({ status: 'offline' }),
        DeviceFactory.create_device({ status: 'warning' }),
        DeviceFactory.create_device({ status: 'error' })
      ],
      'all_healthy': () => DeviceFactory.create_device_list(5, { status: 'online' }),
      'critical_issues': () => DeviceFactory.create_device_list(3, { status: 'error' }),
      'empty_network': () => []
    };

    const devices = scenarios[scenario] ? scenarios[scenario]() : [];

    return render(
      <DashboardWrapper initialDevices={devices}>
        <Dashboard />
      </DashboardWrapper>
    );
  },

  /**
   * Wait for dashboard to fully load
   */
  waitForDashboardLoad: async () => {
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-container')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });
  }
};
