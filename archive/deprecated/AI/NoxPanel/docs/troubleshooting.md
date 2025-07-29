# 🔧 NoxPanel Troubleshooting Guide

**Version:** 1.0
**Last Updated:** 2025-01-15
**Audience:** Developers, System Administrators, Power Users

---

## 🎯 Quick Reference

### 🚨 Emergency Commands
```powershell
# Stop all services immediately
npm run emergency:stop

# Reset database to last known good state
npm run db:rollback

# Clear all caches and restart
npm run cache:clear && npm run dev

# Generate diagnostic report
npm run diagnostics:full
```

### 📞 Support Escalation
- **P0 (Critical):** System down, data loss risk
- **P1 (High):** Core functionality broken, security issues
- **P2 (Medium):** Feature degradation, performance issues
- **P3 (Low):** Enhancement requests, minor bugs

---

## 🔍 Common Issues & Solutions

### 🌐 Frontend Issues

#### ❌ White Screen of Death (WSOD)
**Symptoms:** React app shows blank page, no console errors

**Diagnosis Steps:**
```bash
# Check browser console for JavaScript errors
# F12 → Console tab

# Verify API connectivity
curl -X GET http://localhost:5000/api/health

# Check React dev tools
# Install React Developer Tools browser extension
```

**Solutions:**
```typescript
// 1. Check for unhandled Promise rejections
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason);
});

// 2. Add error boundary at app root
<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>

// 3. Verify environment variables
console.log('Environment:', process.env.NODE_ENV);
console.log('API URL:', process.env.REACT_APP_API_URL);
```

**Prevention:**
- Always use error boundaries around major components
- Implement proper loading states
- Add comprehensive error logging

---

#### ❌ Infinite Loading States
**Symptoms:** Spinners never disappear, content never loads

**Diagnosis:**
```typescript
// Add debug logging to async operations
const fetchDevices = async () => {
  console.log('Starting device fetch...');
  try {
    const response = await api.get('/devices');
    console.log('Fetch successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Fetch failed:', error);
    throw error;
  }
};
```

**Solutions:**
```typescript
// 1. Add timeout to all API calls
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 10000, // 10 second timeout
});

// 2. Implement retry logic with exponential backoff
const retryOperation = async (operation, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
};

// 3. Add loading timeout protection
useEffect(() => {
  const timeoutId = setTimeout(() => {
    if (isLoading) {
      setError('Request timed out. Please try again.');
      setIsLoading(false);
    }
  }, 15000); // 15 second max

  return () => clearTimeout(timeoutId);
}, [isLoading]);
```

---

#### ❌ Component Not Updating
**Symptoms:** UI doesn't reflect state changes, stale data

**Diagnosis:**
```typescript
// Check for state mutation (common React anti-pattern)
// ❌ Bad: Mutating state directly
setState(prevState => {
  prevState.devices.push(newDevice); // Mutation!
  return prevState;
});

// ✅ Good: Immutable updates
setState(prevState => ({
  ...prevState,
  devices: [...prevState.devices, newDevice]
}));
```

**Solutions:**
```typescript
// 1. Use React Developer Tools Profiler
// Identify which components re-render and why

// 2. Add dependency arrays to useEffect
useEffect(() => {
  fetchDevices();
}, [userId, selectedLocation]); // Specify dependencies

// 3. Use useCallback for event handlers
const handleDeviceUpdate = useCallback((device) => {
  setDevices(prev => prev.map(d =>
    d.id === device.id ? { ...d, ...device } : d
  ));
}, []);

// 4. Implement proper key props for lists
{devices.map(device => (
  <DeviceCard
    key={device.id} // Stable, unique key
    device={device}
    onUpdate={handleDeviceUpdate}
  />
))}
```

---

### 🐍 Backend Issues

#### ❌ API Endpoints Returning 500 Errors
**Symptoms:** Internal server errors, stack traces in logs

**Diagnosis:**
```bash
# Check application logs
tail -f logs/noxpanel.log

# Test endpoint directly
curl -X GET http://localhost:5000/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -v

# Check database connectivity
python -c "
from noxcore.database import get_db_session
session = get_db_session()
print('Database connection:', session.is_active)
"
```

**Solutions:**
```python
# 1. Add comprehensive error handling
@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat()
    }), 500

# 2. Implement database connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections
    pool_recycle=3600    # Recycle connections every hour
)

# 3. Add request validation
from pydantic import BaseModel, validator

class DeviceCreateRequest(BaseModel):
    name: str
    ip_address: str
    device_type: str

    @validator('ip_address')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v
```

---

#### ❌ Database Connection Timeouts
**Symptoms:** "Connection pool exhausted", database timeout errors

**Diagnosis:**
```python
# Check active connections
import psutil
from sqlalchemy import text

def diagnose_db_connections():
    with engine.connect() as conn:
        # Check PostgreSQL connections
        result = conn.execute(text("""
            SELECT count(*) as active_connections,
                   max_conn.setting as max_connections
            FROM pg_stat_activity,
                 (SELECT setting FROM pg_settings WHERE name='max_connections') max_conn
            WHERE state = 'active'
            GROUP BY max_conn.setting
        """))

        for row in result:
            print(f"Active: {row.active_connections}, Max: {row.max_connections}")
```

**Solutions:**
```python
# 1. Implement connection cleanup
@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# 2. Add connection health checks
@app.before_request
def check_db_health():
    try:
        with get_db_session() as session:
            session.execute(text('SELECT 1'))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({"error": "Database unavailable"}), 503

# 3. Implement circuit breaker pattern
class DatabaseCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

    def reset(self):
        self.failure_count = 0
        self.state = 'CLOSED'
```

---

#### ❌ Memory Leaks in Long-Running Processes
**Symptoms:** Gradually increasing memory usage, eventual OOM kills

**Diagnosis:**
```python
# Monitor memory usage
import tracemalloc
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

    # Track object counts
    print(f"Objects: {len(gc.get_objects())}")

    # Start tracemalloc for detailed tracking
    tracemalloc.start()

    # ... run your code ...

    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()
```

**Solutions:**
```python
# 1. Implement proper session cleanup
@app.after_request
def cleanup_session(response):
    try:
        db.session.remove()
    except Exception as e:
        logger.warning(f"Session cleanup warning: {e}")
    return response

# 2. Use weak references for caches
import weakref

class DeviceCache:
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()

    def get(self, device_id):
        return self._cache.get(device_id)

    def set(self, device_id, device):
        self._cache[device_id] = device

# 3. Implement periodic cleanup
import threading
import time

def periodic_cleanup():
    while True:
        gc.collect()  # Force garbage collection

        # Clear expired cache entries
        cache.cleanup_expired()

        # Log memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory usage: {memory_mb:.2f} MB")

        time.sleep(300)  # Every 5 minutes

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

---

### 🔒 Authentication & Authorization Issues

#### ❌ JWT Token Expiration Handling
**Symptoms:** Unexpected logouts, "Invalid token" errors

**Diagnosis:**
```javascript
// Check token expiration
const decodeToken = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Date.now() / 1000;
    console.log('Token expires:', new Date(payload.exp * 1000));
    console.log('Current time:', new Date());
    console.log('Time until expiry:', payload.exp - now, 'seconds');
    return payload;
  } catch (error) {
    console.error('Invalid token format:', error);
    return null;
  }
};
```

**Solutions:**
```typescript
// 1. Implement automatic token refresh
class AuthService {
  private refreshTimer?: NodeJS.Timeout;

  scheduleTokenRefresh(token: string) {
    const payload = this.decodeToken(token);
    if (!payload) return;

    // Refresh 5 minutes before expiration
    const refreshTime = (payload.exp * 1000) - Date.now() - (5 * 60 * 1000);

    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(() => {
        this.refreshToken();
      }, refreshTime);
    }
  }

  async refreshToken() {
    try {
      const response = await api.post('/auth/refresh');
      const newToken = response.data.access_token;

      localStorage.setItem('authToken', newToken);
      this.scheduleTokenRefresh(newToken);

      // Update axios default headers
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
    }
  }
}

// 2. Add axios interceptor for token errors
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const authService = new AuthService();
      const refreshed = await authService.refreshToken();

      if (refreshed) {
        // Retry original request
        return api.request(error.config);
      } else {
        // Redirect to login
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);
```

---

#### ❌ Session Management Issues
**Symptoms:** Users logged out unexpectedly, session data lost

**Solutions:**
```python
# 1. Implement robust session storage
from flask_session import Session
import redis

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'noxpanel:'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

Session(app)

# 2. Add session validation middleware
@app.before_request
def validate_session():
    if request.endpoint and request.endpoint.startswith('api.'):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Invalid session"}), 401

        # Verify user still exists and is active
        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            session.clear()
            return jsonify({"error": "User not found"}), 401

# 3. Implement session timeout handling
@app.before_request
def check_session_timeout():
    if 'last_activity' in session:
        # 30 minute timeout
        if time.time() - session['last_activity'] > 1800:
            session.clear()
            return jsonify({"error": "Session expired"}), 401

    session['last_activity'] = time.time()
```

---

### 🔌 Network & Connectivity Issues

#### ❌ CORS Policy Violations
**Symptoms:** Browser blocks requests, CORS errors in console

**Diagnosis:**
```javascript
// Check CORS headers in browser developer tools
// Network tab → Select failed request → Check Response Headers

// Test CORS with curl
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:5000/api/devices
```

**Solutions:**
```python
# 1. Configure CORS properly
from flask_cors import CORS

CORS(app,
     origins=['http://localhost:3000', 'https://your-domain.com'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

# 2. Handle preflight requests explicitly
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

# 3. Development vs Production CORS
if app.config.get('ENV') == 'development':
    CORS(app, origins=['http://localhost:3000'])
else:
    CORS(app, origins=['https://noxpanel.yourdomain.com'])
```

---

#### ❌ API Rate Limiting Issues
**Symptoms:** "Rate limit exceeded" errors, requests being rejected

**Solutions:**
```python
# 1. Implement intelligent rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

# Different limits for different endpoints
@app.route('/api/devices')
@limiter.limit("200 per minute")
def get_devices():
    return jsonify(devices)

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter for auth
def login():
    return handle_login()

# 2. Add rate limit headers
@app.after_request
def add_rate_limit_headers(response):
    # Add remaining requests info
    response.headers['X-RateLimit-Remaining'] = '42'
    response.headers['X-RateLimit-Reset'] = '1234567890'
    return response
```

```typescript
// 3. Frontend rate limit handling
class ApiClient {
  private requestQueue: Array<() => Promise<any>> = [];
  private isProcessing = false;

  async request(config: RequestConfig) {
    return new Promise((resolve, reject) => {
      this.requestQueue.push(async () => {
        try {
          const response = await axios(config);
          resolve(response);
        } catch (error) {
          if (error.response?.status === 429) {
            // Rate limited - add delay and retry
            const retryAfter = error.response.headers['retry-after'] || 60;
            setTimeout(() => this.request(config).then(resolve).catch(reject),
                      retryAfter * 1000);
          } else {
            reject(error);
          }
        }
      });

      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.isProcessing || this.requestQueue.length === 0) return;

    this.isProcessing = true;

    while (this.requestQueue.length > 0) {
      const request = this.requestQueue.shift()!;
      await request();

      // Add small delay between requests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    this.isProcessing = false;
  }
}
```

---

### 🗄️ Database Issues

#### ❌ Migration Failures
**Symptoms:** Database schema out of sync, migration errors

**Diagnosis:**
```bash
# Check migration status
alembic current
alembic history --verbose

# Check for schema differences
alembic check

# Generate new migration
alembic revision --autogenerate -m "Description"
```

**Solutions:**
```python
# 1. Safe migration practices
def upgrade():
    # Always use batch operations for SQLite compatibility
    with op.batch_alter_table('devices') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(100), nullable=True))

    # Populate new field with default values
    connection = op.get_bind()
    connection.execute(
        "UPDATE devices SET new_field = 'default' WHERE new_field IS NULL"
    )

    # Make field non-nullable after population
    with op.batch_alter_table('devices') as batch_op:
        batch_op.alter_column('new_field', nullable=False)

# 2. Add migration validation
def validate_migration():
    """Ensure migration is safe to run."""
    connection = op.get_bind()

    # Check for required conditions
    result = connection.execute("SELECT COUNT(*) FROM devices").scalar()
    if result > 10000:
        raise Exception("Large table detected. Run migration during maintenance window.")

# 3. Rollback procedures
def downgrade():
    # Always provide rollback procedures
    with op.batch_alter_table('devices') as batch_op:
        batch_op.drop_column('new_field')
```

---

#### ❌ Query Performance Issues
**Symptoms:** Slow API responses, high database CPU usage

**Diagnosis:**
```sql
-- PostgreSQL query analysis
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM devices
WHERE location = 'Office A'
ORDER BY last_seen DESC;

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'devices';

-- Find slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Solutions:**
```python
# 1. Add strategic indexes
class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)  # Index for searches
    location = db.Column(db.String(100), index=True)
    last_seen = db.Column(db.DateTime, index=True)  # Index for sorting

    # Composite index for common query patterns
    __table_args__ = (
        db.Index('ix_device_location_status', 'location', 'status'),
        db.Index('ix_device_last_seen_status', 'last_seen', 'status'),
    )

# 2. Optimize queries with proper joins
def get_devices_with_stats():
    return db.session.query(Device)\
        .options(joinedload(Device.network_stats))\
        .filter(Device.status == 'active')\
        .order_by(Device.last_seen.desc())\
        .limit(100)

# 3. Implement query caching
from functools import lru_cache
import hashlib

class QueryCache:
    def __init__(self, timeout=300):  # 5 minutes
        self.cache = {}
        self.timeout = timeout

    def get_or_set(self, key, func):
        cache_key = hashlib.md5(str(key).encode()).hexdigest()

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.timeout:
                return result

        result = func()
        self.cache[cache_key] = (result, time.time())
        return result

query_cache = QueryCache()

@app.route('/api/devices')
def get_devices():
    cache_key = f"devices_{request.args.get('location', 'all')}"

    devices = query_cache.get_or_set(cache_key, lambda:
        Device.query.filter_by(location=request.args.get('location')).all()
    )

    return jsonify([device.to_dict() for device in devices])
```

---

## 🚀 Performance Optimization

### ⚡ Frontend Performance

#### 🎯 Bundle Size Optimization
```bash
# Analyze bundle size
npm run build
npx webpack-bundle-analyzer build/static/js/*.js

# Check for large dependencies
npm install -g cost-of-modules
cost-of-modules --less

# Audit for security and performance
npm audit
npm audit fix
```

**Solutions:**
```typescript
// 1. Implement code splitting
import { lazy, Suspense } from 'react';

const DeviceManagement = lazy(() => import('./DeviceManagement'));
const NetworkAnalytics = lazy(() => import('./NetworkAnalytics'));

const App = () => (
  <Router>
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/devices" element={<DeviceManagement />} />
        <Route path="/analytics" element={<NetworkAnalytics />} />
      </Routes>
    </Suspense>
  </Router>
);

// 2. Optimize imports
// ❌ Bad: Imports entire library
import * as _ from 'lodash';

// ✅ Good: Import only what you need
import { debounce, throttle } from 'lodash';

// 3. Use React.memo for expensive components
const DeviceCard = React.memo(({ device, onUpdate }) => {
  return (
    <div className="device-card">
      {/* Component content */}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function
  return prevProps.device.id === nextProps.device.id &&
         prevProps.device.status === nextProps.device.status;
});
```

---

#### 🔄 State Management Optimization
```typescript
// 1. Use React Query for server state
import { useQuery, useMutation, useQueryClient } from 'react-query';

const useDevices = (filters) => {
  return useQuery(
    ['devices', filters],
    () => api.getDevices(filters),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    }
  );
};

const useUpdateDevice = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (device) => api.updateDevice(device),
    {
      onSuccess: (updatedDevice) => {
        // Update cache immediately
        queryClient.setQueryData(['devices'], (oldData) =>
          oldData.map(device =>
            device.id === updatedDevice.id ? updatedDevice : device
          )
        );
      }
    }
  );
};

// 2. Optimize Redux stores
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const devicesSlice = createSlice({
  name: 'devices',
  initialState: {
    items: [],
    loading: false,
    error: null,
    lastFetch: null,
  },
  reducers: {
    // Use immer for immutable updates
    updateDevice: (state, action) => {
      const index = state.items.findIndex(d => d.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = { ...state.items[index], ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDevices.fulfilled, (state, action) => {
        state.items = action.payload;
        state.loading = false;
        state.lastFetch = Date.now();
      });
  },
});
```

---

### 🐍 Backend Performance

#### ⚡ Database Optimization
```python
# 1. Use database connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Disable SQL logging in production
)

# 2. Implement query optimization
class DeviceService:
    @classmethod
    def get_devices_paginated(cls, page=1, per_page=50, filters=None):
        query = Device.query

        # Apply filters efficiently
        if filters:
            if filters.get('location'):
                query = query.filter(Device.location == filters['location'])
            if filters.get('status'):
                query = query.filter(Device.status.in_(filters['status']))
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        Device.name.ilike(search),
                        Device.ip_address.ilike(search)
                    )
                )

        # Use efficient pagination
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @classmethod
    def bulk_update_status(cls, device_ids, status):
        """Efficient bulk updates."""
        return Device.query.filter(Device.id.in_(device_ids))\
            .update({Device.status: status}, synchronize_session=False)

# 3. Implement caching layers
from functools import wraps
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, timeout, json.dumps(result))

            return result
        return wrapper
    return decorator

@cache_result(timeout=600)  # 10 minutes
def get_network_statistics():
    """Expensive aggregation query."""
    return db.session.query(
        func.count(Device.id).label('total_devices'),
        func.count(case([(Device.status == 'online', 1)])).label('online_devices'),
        func.avg(Device.response_time).label('avg_response_time')
    ).first()._asdict()
```

---

## 🔐 Security Troubleshooting

### 🛡️ Authentication Security
```python
# 1. Implement secure password handling
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib

def hash_password(password):
    """Secure password hashing with salt."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256',
                                  password.encode('utf-8'),
                                  salt.encode('utf-8'),
                                  100000)  # 100k iterations
    return salt + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify password against stored hash."""
    salt = stored_password[:32]
    stored_hash = stored_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256',
                                  provided_password.encode('utf-8'),
                                  salt.encode('utf-8'),
                                  100000)
    return pwdhash.hex() == stored_hash

# 2. Implement rate limiting for auth
from collections import defaultdict
import time

class AuthRateLimiter:
    def __init__(self):
        self.attempts = defaultdict(list)
        self.blocked_ips = {}

    def is_allowed(self, ip_address):
        now = time.time()

        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            if now - self.blocked_ips[ip_address] < 900:  # 15 minute block
                return False
            else:
                del self.blocked_ips[ip_address]

        # Clean old attempts
        self.attempts[ip_address] = [
            attempt for attempt in self.attempts[ip_address]
            if now - attempt < 300  # 5 minute window
        ]

        # Check rate limit
        if len(self.attempts[ip_address]) >= 5:  # 5 attempts per 5 minutes
            self.blocked_ips[ip_address] = now
            return False

        return True

    def record_attempt(self, ip_address):
        self.attempts[ip_address].append(time.time())

rate_limiter = AuthRateLimiter()

@app.route('/api/auth/login', methods=['POST'])
def login():
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    if not rate_limiter.is_allowed(client_ip):
        return jsonify({"error": "Too many login attempts"}), 429

    # Process login...
    rate_limiter.record_attempt(client_ip)
```

---

### 🔒 Data Protection
```python
# 1. Implement field-level encryption
from cryptography.fernet import Fernet
import base64
import os

class FieldEncryption:
    def __init__(self):
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated encryption key: {key.decode()}")

        self.cipher = Fernet(key if isinstance(key, bytes) else key.encode())

    def encrypt(self, data):
        if not data:
            return data
        return base64.urlsafe_b64encode(
            self.cipher.encrypt(data.encode())
        ).decode()

    def decrypt(self, encrypted_data):
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(
            base64.urlsafe_b64decode(encrypted_data.encode())
        ).decode()

encryption = FieldEncryption()

# 2. Secure sensitive database fields
class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    _snmp_community = db.Column('snmp_community', db.Text)  # Encrypted field

    @property
    def snmp_community(self):
        return encryption.decrypt(self._snmp_community) if self._snmp_community else None

    @snmp_community.setter
    def snmp_community(self, value):
        self._snmp_community = encryption.encrypt(value) if value else None

# 3. Audit trail implementation
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50))
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(100))
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def log_audit_event(user_id, action, resource_type, resource_id,
                   old_values=None, new_values=None):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        old_values=old_values,
        new_values=new_values,
        ip_address=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
        user_agent=request.headers.get('User-Agent', '')
    )
    db.session.add(audit_log)
    db.session.commit()
```

---

## 📊 Monitoring & Diagnostics

### 📈 Application Monitoring
```python
# 1. Health check endpoint
@app.route('/health')
def health_check():
    checks = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': os.environ.get('APP_VERSION', '1.0.0'),
        'checks': {}
    }

    # Database connectivity
    try:
        db.session.execute(text('SELECT 1'))
        checks['checks']['database'] = 'healthy'
    except Exception as e:
        checks['checks']['database'] = f'unhealthy: {str(e)}'
        checks['status'] = 'unhealthy'

    # Redis connectivity (if used)
    try:
        redis_client.ping()
        checks['checks']['redis'] = 'healthy'
    except Exception as e:
        checks['checks']['redis'] = f'unhealthy: {str(e)}'

    # Disk space
    import shutil
    total, used, free = shutil.disk_usage('/')
    free_percent = (free / total) * 100
    checks['checks']['disk_space'] = f'{free_percent:.1f}% free'

    if free_percent < 10:
        checks['status'] = 'warning'

    status_code = 200 if checks['status'] == 'healthy' else 503
    return jsonify(checks), status_code

# 2. Metrics collection
from prometheus_client import Counter, Histogram, Gauge, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_DEVICES = Gauge('active_devices_total', 'Number of active devices')

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_duration = time.time() - request.start_time
    REQUEST_DURATION.observe(request_duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    return response

@app.route('/metrics')
def metrics():
    # Update gauges
    active_count = Device.query.filter_by(status='online').count()
    ACTIVE_DEVICES.set(active_count)

    return generate_latest(), 200, {'Content-Type': 'text/plain'}
```

---

### 🚨 Error Tracking
```python
# 1. Structured logging
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, level, message, **context):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'context': context
        }

        # Add request context if available
        if request:
            log_entry['request'] = {
                'method': request.method,
                'url': request.url,
                'ip': request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', '')
            }

        self.logger.info(json.dumps(log_entry))

    def error(self, message, **context):
        self.log('ERROR', message, **context)

    def info(self, message, **context):
        self.log('INFO', message, **context)

    def warning(self, message, **context):
        self.log('WARNING', message, **context)

logger = StructuredLogger('noxpanel')

# 2. Exception handling middleware
@app.errorhandler(Exception)
def handle_exception(error):
    import traceback

    error_id = str(uuid.uuid4())

    logger.error(
        'Unhandled exception',
        error_id=error_id,
        error_type=type(error).__name__,
        error_message=str(error),
        traceback=traceback.format_exc(),
        user_id=session.get('user_id'),
        endpoint=request.endpoint
    )

    # Don't expose internal errors to users
    if app.config.get('ENV') == 'production':
        return jsonify({
            'error': 'Internal server error',
            'error_id': error_id
        }), 500
    else:
        return jsonify({
            'error': str(error),
            'error_id': error_id,
            'traceback': traceback.format_exc()
        }), 500
```

---

## 🛠️ Development Tools

### 🔧 Debugging Utilities
```bash
# Backend debugging
# 1. Run with debugger
python -m pdb main.py

# 2. Run with detailed logging
FLASK_ENV=development FLASK_DEBUG=1 python main.py

# 3. Profile performance
python -m cProfile -o profile.stats main.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Frontend debugging
# 1. Run with debug flags
REACT_APP_DEBUG=true npm start

# 2. Analyze bundle
npm run build -- --analyze

# 3. Check for memory leaks
node --inspect-brk=0.0.0.0:9229 --max-old-space-size=4096 node_modules/.bin/react-scripts start
```

### 📊 Performance Profiling
```typescript
// Frontend performance utilities
class PerformanceProfiler {
  private marks = new Map<string, number>();

  start(name: string) {
    this.marks.set(name, performance.now());
  }

  end(name: string): number {
    const startTime = this.marks.get(name);
    if (!startTime) {
      console.warn(`No start mark found for: ${name}`);
      return 0;
    }

    const duration = performance.now() - startTime;
    console.log(`${name}: ${duration.toFixed(2)}ms`);

    // Send to analytics if needed
    if (duration > 1000) {
      this.reportSlowOperation(name, duration);
    }

    this.marks.delete(name);
    return duration;
  }

  private reportSlowOperation(name: string, duration: number) {
    // Report to monitoring service
    fetch('/api/analytics/performance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        operation: name,
        duration,
        timestamp: Date.now(),
        user_agent: navigator.userAgent
      })
    }).catch(console.error);
  }
}

const profiler = new PerformanceProfiler();

// Usage in components
const DeviceList = () => {
  useEffect(() => {
    profiler.start('device-list-render');

    return () => {
      profiler.end('device-list-render');
    };
  }, []);

  // Component implementation...
};
```

---

This comprehensive troubleshooting guide provides practical solutions for the most common issues encountered in NoxPanel development and deployment. Keep this guide updated as new issues are discovered and resolved.
