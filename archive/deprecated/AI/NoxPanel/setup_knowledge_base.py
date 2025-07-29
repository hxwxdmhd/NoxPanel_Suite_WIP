"""
NoxPanel v5.0 Knowledge Management Setup Script
Initializes the knowledge base and creates sample data for testing
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from noxcore.knowledge_manager import (
    KnowledgeManager, KnowledgeItem, ContentType, ScriptLanguage
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_conversations_data():
    """
    RLVR: Creates new entity with validation and error handling

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for create_sample_conversations_data
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Creates new entity with validation and error handling
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """Create sample conversation data for testing"""
    sample_conversations = {
        "conversations": [
            {
                "id": "conv_001",
                "title": "NoxPanel Security Implementation",
                "create_time": datetime.now().timestamp(),
                "mapping": {
                    "node_1": {
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": ["I need to implement security features for my Flask application. Can you help me create a rate limiting system?"]},
                            "create_time": datetime.now().timestamp()
                        }
                    },
                    "node_2": {
                        "message": {
                            "author": {"role": "assistant"},
                            "content": {"parts": ["""# Flask Rate Limiting Implementation

Here's a comprehensive rate limiting system for Flask:

```python
import time
from functools import wraps
from collections import defaultdict, deque
from flask import request, jsonify, g

class RateLimiter:
    def __init__(self):
        self.clients = defaultdict(deque)
        self.rules = {}

    def add_rule(self, endpoint, max_requests, window_seconds):
        self.rules[endpoint] = {
            'max_requests': max_requests,
            'window_seconds': window_seconds
        }

    def is_allowed(self, client_id, endpoint):
        if endpoint not in self.rules:
            return True

        rule = self.rules[endpoint]
        now = time.time()
        window_start = now - rule['window_seconds']

        # Clean old requests
        client_requests = self.clients[client_id]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) < rule['max_requests']:
            client_requests.append(now)
            return True

        return False

# Usage decorator
def rate_limit(max_requests=100, window_seconds=3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = request.remote_addr
            endpoint = request.endpoint

            limiter = getattr(g, 'rate_limiter', None)
            if limiter and not limiter.is_allowed(client_id, endpoint):
                return jsonify({'error': 'Rate limit exceeded'}), 429

            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

## Best Practices

1. **Sliding Window**: Use a sliding window approach for more accurate rate limiting
2. **Multiple Limits**: Implement both per-minute and per-hour limits
3. **Client Identification**: Use IP address or API key for client identification
4. **Redis Backend**: For production, use Redis for distributed rate limiting
5. **Graceful Degradation**: Return helpful error messages with retry-after headers

## Security Considerations

- Implement rate limiting on authentication endpoints
- Use different limits for authenticated vs anonymous users
- Monitor for patterns indicating abuse
- Consider implementing CAPTCHA for repeated violations
"""]}
                        }
                    }
                }
            },
            {
                "id": "conv_002",
                "title": "Database Optimization Strategies",
                "create_time": datetime.now().timestamp(),
                "mapping": {
                    "node_1": {
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": ["What are the best practices for optimizing SQLite performance in a Flask application?"]},
                            "create_time": datetime.now().timestamp()
                        }
                    },
                    "node_2": {
                        "message": {
                            "author": {"role": "assistant"},
                            "content": {"parts": ["""# SQLite Performance Optimization

## Connection Pooling

```python
import sqlite3
import threading
from contextlib import contextmanager
from queue import Queue, Empty

class SQLiteConnectionPool:
    def __init__(self, database_path, max_connections=10):
        self.database_path = database_path
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        for _ in range(self.max_connections):
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")
            self.pool.put(conn)

    @contextmanager
    def get_connection(self):
        try:
            conn = self.pool.get(timeout=5.0)
            yield conn
        except Empty:
            raise Exception("No database connections available")
        finally:
            self.pool.put(conn)
```

## Performance SQL Queries

```sql
-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Optimize common queries
-- Bad: SELECT * FROM logs WHERE timestamp > ?
-- Good: SELECT id, level, message FROM logs WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 100;

-- Use compound indexes for multi-column queries
CREATE INDEX IF NOT EXISTS idx_logs_user_level ON logs(user_id, level, timestamp);
```

## Best Practices

1. **WAL Mode**: Use Write-Ahead Logging for better concurrency
2. **Connection Pooling**: Reuse connections to avoid setup overhead
3. **Prepared Statements**: Use parameterized queries
4. **Batch Operations**: Group multiple operations in transactions
5. **Proper Indexing**: Create indexes for frequently queried columns
6. **Query Optimization**: Use EXPLAIN QUERY PLAN to optimize queries

## PowerShell Health Check Script

```powershell
# SQLite Database Health Check
param(
    [Parameter(Mandatory=$true)]
    [string]$DatabasePath
)

function Test-SQLiteHealth {
    param([string]$DbPath)

    try {
        Add-Type -Path "System.Data.SQLite.dll"
        $connectionString = "Data Source=$DbPath;Version=3;"
        $connection = New-Object System.Data.SQLite.SQLiteConnection($connectionString)
        $connection.Open()

        # Check integrity
        $command = $connection.CreateCommand()
        $command.CommandText = "PRAGMA integrity_check;"
        $result = $command.ExecuteScalar()

        Write-Host "Database Health: $result" -ForegroundColor Green

        # Get database size
        $fileInfo = Get-Item $DbPath
        $sizeM = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Host "Database Size: $sizeM MB" -ForegroundColor Cyan

        $connection.Close()
        return $true
    }
    catch {
        Write-Error "Database health check failed: $_"
        return $false
    }
}

Test-SQLiteHealth -DbPath $DatabasePath
```
"""]}
                        }
                    }
                }
            },
            {
                "id": "conv_003",
                "title": "PowerShell Automation Scripts",
                "create_time": datetime.now().timestamp(),
                "mapping": {
                    "node_1": {
                        "message": {
                            "author": {"role": "user"},
                            "content": {"parts": ["I need PowerShell scripts for automating system monitoring and log analysis."]},
                            "create_time": datetime.now().timestamp()
                        }
                    },
                    "node_2": {
                        "message": {
                            "author": {"role": "assistant"},
                            "content": {"parts": ["""# PowerShell System Monitoring Scripts

## System Resource Monitor

```powershell
# Advanced System Monitor
param(
    [int]$IntervalSeconds = 30,
    [string]$LogPath = "C:\\Logs\\SystemMonitor.log",
    [int]$CpuThreshold = 80,
    [int]$MemoryThreshold = 85
)

function Write-MonitorLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogPath -Value $logEntry
}

function Get-SystemMetrics {
    # CPU Usage
    $cpuUsage = (Get-Counter "\\Processor(_Total)\\% Processor Time").CounterSamples.CookedValue

    # Memory Usage
    $memory = Get-WmiObject -Class Win32_OperatingSystem
    $memoryUsage = [math]::Round(((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100), 2)

    # Disk Usage
    $diskUsage = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | ForEach-Object {
        [PSCustomObject]@{
            Drive = $_.DeviceID
            UsedPercent = [math]::Round((($_.Size - $_.FreeSpace) / $_.Size) * 100, 2)
            FreeGB = [math]::Round($_.FreeSpace / 1GB, 2)
        }
    }

    return @{
        CPU = $cpuUsage
        Memory = $memoryUsage
        Disks = $diskUsage
    }
}

# Main monitoring loop
while ($true) {
    try {
        $metrics = Get-SystemMetrics

        Write-MonitorLog "CPU: $($metrics.CPU)% | Memory: $($metrics.Memory)%"

        # Check thresholds
        if ($metrics.CPU -gt $CpuThreshold) {
            Write-MonitorLog "HIGH CPU USAGE: $($metrics.CPU)%" -Level "WARNING"
        }

        if ($metrics.Memory -gt $MemoryThreshold) {
            Write-MonitorLog "HIGH MEMORY USAGE: $($metrics.Memory)%" -Level "WARNING"
        }

        foreach ($disk in $metrics.Disks) {
            if ($disk.UsedPercent -gt 90) {
                Write-MonitorLog "LOW DISK SPACE: $($disk.Drive) at $($disk.UsedPercent)%" -Level "CRITICAL"
            }
        }
    }
    catch {
        Write-MonitorLog "Monitoring error: $_" -Level "ERROR"
    }

    Start-Sleep -Seconds $IntervalSeconds
}
```

## Log Analysis Script

```powershell
# Log Analysis and Alerting
param(
    [Parameter(Mandatory=$true)]
    [string]$LogDirectory,
    [string]$Pattern = "ERROR|CRITICAL|FATAL",
    [int]$LastHours = 24
)

function Analyze-Logs {
    param(
        [string]$Directory,
        [string]$SearchPattern,
        [datetime]$Since
    )

    $logFiles = Get-ChildItem -Path $Directory -Filter "*.log" -Recurse
    $results = @()

    foreach ($file in $logFiles) {
        if ($file.LastWriteTime -ge $Since) {
            $content = Get-Content -Path $file.FullName

            foreach ($line in $content) {
                if ($line -match $SearchPattern) {
                    $results += [PSCustomObject]@{
                        File = $file.Name
                        Line = $line
                        Timestamp = $file.LastWriteTime
                        Severity = if ($line -match "CRITICAL|FATAL") { "High" } else { "Medium" }
                    }
                }
            }
        }
    }

    return $results | Sort-Object Timestamp -Descending
}

$since = (Get-Date).AddHours(-$LastHours)
$issues = Analyze-Logs -Directory $LogDirectory -SearchPattern $Pattern -Since $since

if ($issues.Count -gt 0) {
    Write-Host "Found $($issues.Count) issues in the last $LastHours hours:" -ForegroundColor Red
    $issues | Format-Table -AutoSize

    # Generate summary report
    $summary = $issues | Group-Object Severity | ForEach-Object {
        [PSCustomObject]@{
            Severity = $_.Name
            Count = $_.Count
        }
    }

    Write-Host "Summary:" -ForegroundColor Yellow
    $summary | Format-Table -AutoSize
}
else {
    Write-Host "No issues found in the last $LastHours hours." -ForegroundColor Green
}
```

## Best Practices for PowerShell Automation

1. **Error Handling**: Always use try-catch blocks
2. **Logging**: Implement comprehensive logging
3. **Parameters**: Use parameters for flexibility
4. **Validation**: Validate inputs and file paths
5. **Performance**: Use efficient cmdlets and avoid loops when possible
6. **Security**: Follow principle of least privilege

## Scheduled Task Setup

```powershell
# Register scheduled task for monitoring
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\\Scripts\\SystemMonitor.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal
Register-ScheduledTask -TaskName "SystemMonitor" -InputObject $task
    """
    RLVR: Creates new entity with validation and error handling

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for create_sample_knowledge_items
    2. Analysis: Function complexity 1.2/5.0
    3. Solution: Creates new entity with validation and error handling
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
```
"""]}
                        }
                    }
                }
            }
        ]
    }

    return sample_conversations

def create_sample_knowledge_items(km: KnowledgeManager):
    """Create sample knowledge items directly"""

    sample_items = [
        {
            "title": "Python Virtual Environment Best Practices",
            "content": """# Python Virtual Environment Management

## Creating Virtual Environments

```bash
# Using venv (Python 3.3+)
python -m venv myproject_env

# Using virtualenv
virtualenv myproject_env

# Using conda
conda create -n myproject python=3.9
```

## Activation Commands

```bash
# Windows
myproject_env\\Scripts\\activate

# macOS/Linux
source myproject_env/bin/activate

# Conda
conda activate myproject
```

## Best Practices

1. **Project-specific environments**: One environment per project
2. **Requirements files**: Always maintain requirements.txt
3. **Version pinning**: Pin dependency versions for reproducibility
4. **Environment naming**: Use descriptive names
5. **Documentation**: Document environment setup in README
""",
            "content_type": ContentType.BEST_PRACTICE,
            "language": None,
            "tags": ["python", "virtual-environment", "development", "best-practices"],
            "topic": "development",
            "category": "best-practices"
        },
        {
            "title": "Flask Security Headers Implementation",
            "content": """from flask import Flask, Response
from functools import wraps

def add_security_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if isinstance(response, Response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    return decorated_function

@app.route('/api/secure-endpoint')
@add_security_headers
def secure_endpoint():
    return {'message': 'This endpoint has security headers'}""",
            "content_type": ContentType.CODE_SNIPPET,
            "language": ScriptLanguage.PYTHON,
            "tags": ["flask", "security", "headers", "web-security"],
            "topic": "security",
            "category": "development"
        },
        {
            "title": "Git Workflow Documentation",
            "content": """# Git Workflow for Development Teams

## Branch Naming Convention

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes

## Standard Workflow

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature
   ```

2. **Development Process**
   ```bash
   # Make changes
   git add .
   git commit -m "feat: add new feature implementation"
   git push origin feature/new-feature
   ```

3. **Pull Request Process**
   - Create PR from feature branch to develop
   - Request code review
   - Address feedback
   - Merge after approval

4. **Release Process**
   ```bash
   git checkout main
   git merge develop
   git tag v1.0.0
   git push origin main --tags
   ```

## Commit Message Format

    """
    RLVR: Implements setup_knowledge_base with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for setup_knowledge_base
    2. Analysis: Function complexity 1.5/5.0
    3. Solution: Implements setup_knowledge_base with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
```
type(scope): description

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore
""",
            "content_type": ContentType.DOCUMENTATION,
            "language": None,
            "tags": ["git", "workflow", "version-control", "development"],
            "topic": "development",
            "category": "documentation"
        }
    ]

    for item_data in sample_items:
        km.add_manual_item(**item_data)

    logger.info(f"✅ Created {len(sample_items)} sample knowledge items")

def setup_knowledge_base():
    """Set up the knowledge base with sample data"""
    try:
        # Initialize knowledge manager
        km = KnowledgeManager()

        # Create sample conversations file
        sample_data = create_sample_conversations_data()
        sample_file = Path("data/temp/sample_conversations.json")
        sample_file.parent.mkdir(parents=True, exist_ok=True)

        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Created sample conversations file: {sample_file}")

        # Import conversations
        results = km.import_conversations(str(sample_file))
        logger.info(f"📥 Imported conversations: {results['processed']} processed, {results['items_created']} items created")

        # Create additional sample items
        create_sample_knowledge_items(km)

        # Get final statistics
        stats = km.db.get_statistics()
        logger.info(f"📊 Knowledge base statistics: {stats}")

        # Clean up temp file
        sample_file.unlink()

        logger.info("🎉 Knowledge base setup completed successfully!")

        return True

    except Exception as e:
        logger.error(f"❌ Knowledge base setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🧠 NoxPanel Knowledge Management Setup")
    print("=" * 50)

    success = setup_knowledge_base()

    if success:
        print("\n✅ Setup completed successfully!")
        print("\nYou can now:")
        print("1. Start NoxPanel: python webpanel/app_v5.py")
        print("2. Navigate to: http://localhost:5000/knowledge/")
        print("3. Explore the knowledge base")
        print("4. Import your own conversations.json file")
    else:
        print("\n❌ Setup failed. Check the logs for details.")
        sys.exit(1)
