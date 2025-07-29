# 🤝 Contributing to NoxPanel Testing Framework

**Version:** 1.0
**Last Updated:** 2025-01-15

---

## 🎯 Overview

This guide helps you contribute high-quality, ADHD-friendly tests to the NoxPanel ecosystem. Our testing framework emphasizes clarity, maintainability, and comprehensive coverage across all user personas.

---

## 🧪 Test Development Guidelines

### 📝 Naming Conventions

#### Test Files
```
Format: [component/feature].[test-type].{ts|py}
Examples:
- Dashboard.component.test.tsx
- DeviceAPI.integration.test.py
- LoginFlow.e2e.spec.ts
- ThemeSelector.accessibility.test.tsx
```

#### Test Functions
```typescript
// ✅ Good: Descriptive BDD-style naming
describe('Dashboard Component', () => {
  it('should display device count when devices are loaded', () => {
    // Test implementation
  });

  it('should show loading state while fetching device data', () => {
    // Test implementation
  });

  it('should handle empty device list gracefully', () => {
    // Test implementation
  });
});
```

```python
# ✅ Good: Python test naming with should_when pattern
class TestDeviceAPI:
    def test_should_return_device_list_when_authenticated_user_requests(self):
        # Test implementation
        pass

    def test_should_reject_request_when_invalid_token_provided(self):
        # Test implementation
        pass

    def test_should_handle_database_timeout_gracefully_when_query_exceeds_limit(self):
        # Test implementation
        pass
```

---

## 📚 Documentation Standards

### 🎯 JSDoc for TypeScript/JavaScript
```typescript
/**
 * Tests the device grid component rendering and interaction
 *
 * @group Component Tests
 * @category Dashboard
 * @requires MockDeviceProvider
 *
 * @example
 * ```typescript
 * // Test device grid with empty state
 * render(<DeviceGrid devices={[]} />);
 * expect(screen.getByText('No devices found')).toBeInTheDocument();
 * ```
 */
describe('DeviceGrid Component', () => {
  /**
   * Verifies that the device grid displays correctly when provided with device data
   *
   * @test Rendering
   * @persona Admin User
   * @accessibility Ensures proper ARIA labels for screen readers
   */
  it('should render device cards with proper accessibility attributes', () => {
    const mockDevices = createMockDevices(5);
    render(<DeviceGrid devices={mockDevices} />);

    // Verify ARIA labels
    expect(screen.getByRole('grid')).toHaveAttribute('aria-label', 'Device list');
    expect(screen.getAllByRole('gridcell')).toHaveLength(5);
  });
});
```

### 🐍 Google-Style Docstrings for Python
```python
class TestDeviceAPI:
    """Tests for device management API endpoints.

    This test suite covers all CRUD operations for device management,
    including authentication, authorization, and error handling scenarios.

    Attributes:
        client: FastAPI test client instance
        test_db: Isolated database session for testing

    Test Categories:
        - Authentication: Login, token validation, session management
        - Authorization: Role-based access control
        - CRUD Operations: Create, read, update, delete devices
        - Error Handling: Invalid inputs, network failures, timeouts
    """

    def test_should_create_device_when_valid_data_provided(self):
        """Test device creation with valid input data.

        Verifies that a new device can be successfully created when all
        required fields are provided with valid values.

        Args:
            None (uses class fixtures)

        Returns:
            None

        Raises:
            AssertionError: If device creation fails or response is invalid

        Test Flow:
            1. Prepare valid device data
            2. Send POST request to /api/devices
            3. Verify 201 status code
            4. Verify response contains device ID
            5. Verify device exists in database

        Expected Outcome:
            - HTTP 201 Created response
            - Device ID in response body
            - Device persisted in database
            - All input fields preserved
        """
        # Arrange
        device_data = {
            "name": "Test Router",
            "ip_address": "192.168.1.1",
            "device_type": "router",
            "location": "Office A"
        }

        # Act
        response = self.client.post("/api/devices", json=device_data)

        # Assert
        assert response.status_code == 201
        assert "device_id" in response.json()

        # Verify database persistence
        device_id = response.json()["device_id"]
        saved_device = self.test_db.query(Device).filter(Device.id == device_id).first()
        assert saved_device is not None
        assert saved_device.name == device_data["name"]
```

---

## 🧩 Test Patterns & Best Practices

### 🔄 Async Testing Patterns
```typescript
// ✅ Good: Proper async/await with error handling
describe('API Integration Tests', () => {
  it('should handle network delays gracefully', async () => {
    // Mock slow network response
    const slowApiCall = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 2000))
    );

    render(<DeviceList apiCall={slowApiCall} />);

    // Verify loading state
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

    // Wait for completion
    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
```

### 🎭 Mock Data Generation
```typescript
// ✅ Good: Realistic test data with Faker
import { faker } from '@faker-js/faker';

export const createMockDevice = (overrides: Partial<Device> = {}): Device => ({
  id: faker.string.uuid(),
  name: faker.internet.domainName(),
  ip_address: faker.internet.ip(),
  mac_address: faker.internet.mac(),
  device_type: faker.helpers.arrayElement(['router', 'switch', 'access_point']),
  location: faker.location.city(),
  status: faker.helpers.arrayElement(['online', 'offline', 'warning']),
  last_seen: faker.date.recent(),
  ...overrides
});

// Usage in tests
const testDevices = Array.from({ length: 10 }, () => createMockDevice());
```

```python
# ✅ Good: Factory pattern for Python test data
import factory
from faker import Faker

fake = Faker()

class DeviceFactory(factory.Factory):
    """Factory for creating test device instances."""

    class Meta:
        model = Device

    id = factory.Sequence(lambda n: f"device_{n}")
    name = factory.LazyAttribute(lambda obj: fake.hostname())
    ip_address = factory.LazyAttribute(lambda obj: fake.ipv4())
    mac_address = factory.LazyAttribute(lambda obj: fake.mac_address())
    device_type = factory.Faker('random_element', elements=['router', 'switch', 'ap'])
    location = factory.Faker('city')
    status = factory.Faker('random_element', elements=['online', 'offline', 'warning'])

    @factory.post_generation
    def set_network_config(obj, create, extracted, **kwargs):
        """Set realistic network configuration based on device type."""
        if obj.device_type == 'router':
            obj.ports = 4
            obj.wifi_enabled = True
        elif obj.device_type == 'switch':
            obj.ports = fake.random_int(min=8, max=48)
            obj.wifi_enabled = False

# Usage in tests
def test_device_creation():
    device = DeviceFactory()
    assert device.name is not None
    assert device.ip_address is not None
```

---

## 🎯 Test Data Management

### 🗄️ Database Test Isolation
```python
# ✅ Good: Proper test database isolation
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

@pytest.fixture(scope="function")
def test_db():
    """Create isolated test database session."""
    # Create in-memory SQLite for speed
    engine = create_engine("sqlite:///:memory:")
    TestSessionLocal = sessionmaker(bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Provide session
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def authenticated_client(test_db):
    """Provide authenticated test client."""
    # Create test user
    test_user = UserFactory()
    test_db.add(test_user)
    test_db.commit()

    # Create client with auth token
    auth_token = create_access_token({"sub": test_user.id})
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {auth_token}"})

    return client
```

### 🎭 Frontend Mocking Strategies
```typescript
// ✅ Good: MSW for API mocking
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/devices', (req, res, ctx) => {
    return res(
      ctx.json({
        devices: [
          createMockDevice({ name: 'Test Router 1' }),
          createMockDevice({ name: 'Test Switch 1' })
        ]
      })
    );
  }),

  rest.post('/api/devices', (req, res, ctx) => {
    const newDevice = req.body as Device;
    return res(
      ctx.status(201),
      ctx.json({
        device_id: faker.string.uuid(),
        ...newDevice
      })
    );
  })
);

// Setup/teardown
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## ♿ Accessibility Testing Guidelines

### 🎯 WCAG 2.1 AA Compliance
```typescript
// ✅ Good: Comprehensive accessibility testing
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Dashboard Accessibility', () => {
  it('should meet WCAG 2.1 AA standards', async () => {
    const { container } = render(<Dashboard />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should support keyboard navigation', () => {
    render(<Dashboard />);

    // Test tab order
    const firstElement = screen.getByTestId('main-nav');
    const secondElement = screen.getByTestId('device-grid');

    firstElement.focus();
    expect(firstElement).toHaveFocus();

    userEvent.tab();
    expect(secondElement).toHaveFocus();
  });

  it('should provide screen reader announcements', () => {
    render(<Dashboard />);

    // Test live region updates
    const liveRegion = screen.getByRole('status');
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');

    // Trigger update that should announce
    fireEvent.click(screen.getByText('Refresh Devices'));

    expect(liveRegion).toHaveTextContent('Device list updated');
  });
});
```

### 🧠 ADHD-Specific Testing
```typescript
// ✅ Good: ADHD-friendly feature testing
describe('ADHD User Experience', () => {
  it('should provide clear focus indicators', () => {
    render(<DeviceForm />);

    const nameInput = screen.getByLabelText('Device Name');
    nameInput.focus();

    // Verify visible focus ring
    expect(nameInput).toHaveStyle('outline: 2px solid #3b82f6');
  });

  it('should support reduced motion preferences', () => {
    // Mock reduced motion preference
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
      })),
    });

    render(<AnimatedDashboard />);

    // Verify animations are disabled
    const animatedElement = screen.getByTestId('slide-panel');
    expect(animatedElement).toHaveStyle('animation: none');
  });

  it('should handle interruption and recovery', () => {
    render(<LongRunningTask />);

    // Start long operation
    fireEvent.click(screen.getByText('Start Import'));
    expect(screen.getByText('Importing devices...')).toBeInTheDocument();

    // Simulate interruption (page refresh)
    fireEvent.beforeUnload(window);

    // Verify recovery options
    expect(screen.getByText('Resume Import')).toBeInTheDocument();
  });
});
```

---

## 🚀 Performance Testing Guidelines

### ⚡ Load Testing with Locust
```python
# ✅ Good: Realistic load test scenarios
from locust import HttpUser, task, between

class NoxPanelUser(HttpUser):
    """Simulate typical NoxPanel user behavior."""

    wait_time = between(1, 3)  # Realistic user think time

    def on_start(self):
        """Login before starting tasks."""
        response = self.client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })

        if response.status_code == 200:
            self.auth_token = response.json()["access_token"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })

    @task(3)  # 30% of actions
    def view_dashboard(self):
        """View main dashboard."""
        with self.client.get("/api/dashboard/summary",
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task(2)  # 20% of actions
    def list_devices(self):
        """List all devices."""
        self.client.get("/api/devices")

    @task(1)  # 10% of actions
    def create_device(self):
        """Create new device."""
        device_data = {
            "name": f"Load Test Device {self.user_id}",
            "ip_address": f"192.168.1.{self.user_id}",
            "device_type": "router"
        }
        self.client.post("/api/devices", json=device_data)

    @task(1)  # 10% of actions
    def update_device_settings(self):
        """Update device configuration."""
        # First get a device
        response = self.client.get("/api/devices")
        if response.status_code == 200:
            devices = response.json().get("devices", [])
            if devices:
                device_id = devices[0]["id"]
                update_data = {"location": "Updated Location"}
                self.client.patch(f"/api/devices/{device_id}", json=update_data)
```

### 📊 Performance Metrics Collection
```typescript
// ✅ Good: Frontend performance monitoring
class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map();

  startTiming(operation: string): () => void {
    const startTime = performance.now();

    return () => {
      const endTime = performance.now();
      const duration = endTime - startTime;

      if (!this.metrics.has(operation)) {
        this.metrics.set(operation, []);
      }

      this.metrics.get(operation)!.push(duration);

      // Alert if operation is slow
      if (duration > 1000) {  // 1 second threshold
        console.warn(`Slow operation detected: ${operation} took ${duration}ms`);
      }
    };
  }

  getMetrics(operation: string): PerformanceMetrics {
    const times = this.metrics.get(operation) || [];

    return {
      count: times.length,
      average: times.reduce((a, b) => a + b, 0) / times.length,
      p95: this.percentile(times, 0.95),
      p99: this.percentile(times, 0.99),
      min: Math.min(...times),
      max: Math.max(...times)
    };
  }

  private percentile(values: number[], percentile: number): number {
    const sorted = values.sort((a, b) => a - b);
    const index = Math.ceil(sorted.length * percentile) - 1;
    return sorted[index];
  }
}

// Usage in tests
describe('Performance Tests', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = new PerformanceMonitor();
  });

  it('should load dashboard within performance budget', async () => {
    const stopTiming = monitor.startTiming('dashboard-load');

    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByTestId('device-grid')).toBeInTheDocument();
    });

    stopTiming();

    const metrics = monitor.getMetrics('dashboard-load');
    expect(metrics.average).toBeLessThan(500); // 500ms budget
  });
});
```

---

## 🔧 Local Development Setup

### 🎯 VS Code Test Integration
```json
// .vscode/settings.json
{
  "jest.autoRun": "watch",
  "jest.showCoverageOnLoad": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "backend/api-tests",
    "--verbose",
    "--cov=noxcore",
    "--cov-report=html"
  ],
  "testing.automaticallyOpenPeekView": "failureAnywhere"
}
```

### ⚡ Quick Development Commands
```bash
# Component testing with watch mode
npm run test:components -- --watch

# Run specific test file
npm run test:components -- Dashboard.test.tsx

# API testing with verbose output
pytest backend/api-tests/test_devices.py -v -s

# E2E testing in headed mode (for debugging)
npx playwright test --headed --debug

# Performance testing (development profile)
locust -f performance/locust/dev-profile.py --host=http://localhost:3000 -u 5 -r 1
```

---

## 🚨 Error Handling Patterns

### 🔄 Retry Logic for Flaky Tests
```typescript
// ✅ Good: Robust retry mechanism
const retryAssertion = async (
  assertion: () => Promise<void> | void,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<void> => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await assertion();
      return; // Success!
    } catch (error) {
      if (attempt === maxRetries) {
        throw error; // Final attempt failed
      }

      console.log(`Assertion failed (attempt ${attempt}/${maxRetries}), retrying...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};

// Usage
it('should handle intermittent network issues', async () => {
  render(<DeviceList />);

  await retryAssertion(async () => {
    await waitFor(() => {
      expect(screen.getByTestId('device-grid')).toBeInTheDocument();
    });
  });
});
```

### 🛡️ Error Boundary Testing
```typescript
// ✅ Good: Error boundary component testing
const ErrorBoundaryWrapper = ({ children }: { children: React.ReactNode }) => (
  <ErrorBoundary fallback={<div>Something went wrong</div>}>
    {children}
  </ErrorBoundary>
);

describe('Error Handling', () => {
  it('should display error boundary when component crashes', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundaryWrapper>
        <ThrowError />
      </ErrorBoundaryWrapper>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });
});
```

---

## 📊 Test Metrics & Reporting

### 🎯 Coverage Configuration
```javascript
// jest.config.js
module.exports = {
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/__tests__/**',
  ],
  coverageThreshold: {
    global: {
      statements: 90,
      branches: 85,
      functions: 95,
      lines: 90,
    },
    './src/components/': {
      statements: 95,
      branches: 90,
      functions: 100,
      lines: 95,
    },
  },
  coverageReporters: ['text', 'html', 'lcov'],
};
```

```ini
# pytest.ini
[tool:pytest]
addopts =
    --verbose
    --cov=noxcore
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=90
    --tb=short
    --strict-markers

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    smoke: marks tests as smoke tests for quick validation
```

---

## 🎭 Test Organization Best Practices

### 📁 File Structure
```
tests/
├── __helpers__/           # Shared test utilities
│   ├── factories.ts       # Data factories
│   ├── matchers.ts        # Custom Jest matchers
│   └── setup.ts           # Test environment setup
├── __mocks__/             # Module mocks
│   ├── api.ts             # API client mocks
│   └── localStorage.ts    # Browser API mocks
├── component/             # Component tests
├── integration/           # Integration tests
├── e2e/                   # End-to-end tests
└── performance/           # Performance tests
```

### 🏷️ Test Tagging Strategy
```typescript
// ✅ Good: Descriptive test tagging
describe('Device Management', () => {
  describe('CRUD Operations', () => {
    it('[SMOKE] should create device with valid data', () => {
      // Critical path test
    });

    it('[REGRESSION] should handle duplicate device names', () => {
      // Previous bug fix
    });

    it('[EDGE_CASE] should handle extremely long device names', () => {
      // Edge case coverage
    });
  });

  describe('ADHD User Experience', () => {
    it('[A11Y] should provide clear focus indicators', () => {
      // Accessibility test
    });

    it('[UX] should save form state during interruptions', () => {
      // User experience test
    });
  });
});
```

---

This comprehensive contributing guide ensures consistent, high-quality test development that supports both technical excellence and ADHD-friendly user experiences. Follow these patterns to create maintainable, reliable tests that enhance the overall quality of the NoxPanel system.
