# NoxGuard Database Schema Documentation

## Overview

The NoxGuard---NoxPanel database system provides a comprehensive data storage solution for network management, knowledge management, AI conversations, and user sessions. Built on SQLite with connection pooling and migration support.

## Database Architecture

### Core Components

1. **NoxDatabase**: Core database class with connection pooling
2. **DatabaseConnectionPool**: Connection pool management for performance
3. **MigrationManager**: Schema versioning and migrations
4. **Repositories**: Data access layer for different entities
5. **DatabaseService**: High-level service orchestrating all components
6. **DatabaseAdmin**: Administrative tools and utilities

### Schema Version: 1

The current schema includes the following table groups:

## Core System Tables

### users
User account management and authentication.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique user identifier |
| username | TEXT UNIQUE NOT NULL | Login username |
| password_hash | TEXT NOT NULL | Hashed password |
| email | TEXT UNIQUE | Email address |
| role | TEXT DEFAULT 'user' | User role (admin, user, etc.) |
| created_at | TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | Last profile update |
| last_login | TIMESTAMP | Last successful login |
| active | BOOLEAN DEFAULT 1 | Account status |
| settings | TEXT DEFAULT '{}' | User settings (JSON) |
| preferences | TEXT DEFAULT '{}' | User preferences (JSON) |

### devices
Network device discovery and monitoring.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique device identifier |
| name | TEXT | Device name/hostname |
| ip_address | TEXT UNIQUE NOT NULL | IP address |
| mac_address | TEXT | MAC address |
| device_type | TEXT | Device type classification |
| vendor | TEXT | Device vendor/manufacturer |
| operating_system | TEXT | OS information |
| first_seen | TIMESTAMP | First discovery time |
| last_seen | TIMESTAMP | Last seen online |
| online | BOOLEAN DEFAULT 0 | Current online status |
| port_scan_data | TEXT DEFAULT '{}' | Port scan results (JSON) |
| vulnerability_data | TEXT DEFAULT '{}' | Security scan results (JSON) |
| notes | TEXT | Admin notes |
| tags | TEXT DEFAULT '[]' | Device tags (JSON array) |

### settings
System configuration and settings.

| Column | Type | Description |
|--------|------|-------------|
| key | TEXT PRIMARY KEY | Setting key |
| value | TEXT NOT NULL | Setting value |
| category | TEXT DEFAULT 'general' | Setting category |
| description | TEXT | Setting description |
| updated_at | TIMESTAMP | Last update time |
| updated_by | INTEGER | User who updated (FK) |

### audit_logs
System activity and security audit trail.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Log entry ID |
| user_id | INTEGER | User who performed action (FK) |
| action | TEXT NOT NULL | Action performed |
| resource_type | TEXT | Type of resource affected |
| resource_id | TEXT | ID of affected resource |
| details | TEXT DEFAULT '{}' | Additional details (JSON) |
| ip_address | TEXT | Client IP address |
| user_agent | TEXT | Client user agent |
| timestamp | TIMESTAMP | When action occurred |

## Knowledge Management Tables

### knowledge_items
Knowledge base articles and documentation.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique item identifier |
| title | TEXT NOT NULL | Article title |
| content | TEXT NOT NULL | Article content |
| content_type | TEXT DEFAULT 'text' | Content format (text, markdown, html) |
| category | TEXT DEFAULT 'general' | Content category |
| source | TEXT | Original source |
| source_url | TEXT | Source URL |
| author_id | INTEGER | Author user ID (FK) |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| last_accessed | TIMESTAMP | Last access time |
| access_count | INTEGER DEFAULT 0 | Number of times accessed |
| rating | REAL DEFAULT 0.0 | User rating |
| status | TEXT DEFAULT 'active' | Item status |
| metadata | TEXT DEFAULT '{}' | Additional metadata (JSON) |
| vector_embedding | BLOB | AI vector embedding for search |
| search_keywords | TEXT | Search keywords |

### tags
Content categorization and tagging system.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique tag identifier |
| name | TEXT UNIQUE NOT NULL | Tag name |
| description | TEXT | Tag description |
| color | TEXT DEFAULT '#808080' | Display color |
| category | TEXT DEFAULT 'general' | Tag category |
| usage_count | INTEGER DEFAULT 0 | How many times used |
| created_at | TIMESTAMP | Creation time |
| created_by | INTEGER | Creator user ID (FK) |

### knowledge_item_tags
Many-to-many relationship between knowledge items and tags.

| Column | Type | Description |
|--------|------|-------------|
| knowledge_item_id | INTEGER | Knowledge item ID (FK) |
| tag_id | INTEGER | Tag ID (FK) |
| created_at | TIMESTAMP | When tag was applied |

### knowledge_relationships
Relationships between knowledge items.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Relationship ID |
| source_item_id | INTEGER | Source item ID (FK) |
| target_item_id | INTEGER | Target item ID (FK) |
| relationship_type | TEXT DEFAULT 'related' | Type of relationship |
| strength | REAL DEFAULT 1.0 | Relationship strength |
| created_at | TIMESTAMP | When relationship was created |

## AI Conversation Tables

### conversations
AI chat sessions and conversations.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique conversation ID |
| user_id | INTEGER | User ID (FK) |
| session_id | TEXT | Session identifier |
| title | TEXT | Conversation title |
| model_name | TEXT | AI model used |
| model_version | TEXT | Model version |
| context_window | INTEGER DEFAULT 4096 | Context window size |
| total_tokens | INTEGER DEFAULT 0 | Total tokens used |
| total_cost | REAL DEFAULT 0.0 | Cost if applicable |
| status | TEXT DEFAULT 'active' | Conversation status |
| started_at | TIMESTAMP | Start time |
| ended_at | TIMESTAMP | End time |
| metadata | TEXT DEFAULT '{}' | Additional metadata (JSON) |

### conversation_messages
Individual messages within conversations.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Message ID |
| conversation_id | INTEGER | Conversation ID (FK) |
| role | TEXT NOT NULL | Message role (user, assistant, system) |
| content | TEXT NOT NULL | Message content |
| token_count | INTEGER DEFAULT 0 | Tokens in this message |
| response_time | REAL | AI response time in seconds |
| model_name | TEXT | Model that generated response |
| timestamp | TIMESTAMP | Message timestamp |
| metadata | TEXT DEFAULT '{}' | Additional metadata (JSON) |

### ai_metrics
AI model performance metrics.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Metric ID |
| model_name | TEXT NOT NULL | Model name |
| metric_type | TEXT NOT NULL | Type of metric |
| metric_value | REAL NOT NULL | Metric value |
| context | TEXT DEFAULT '{}' | Metric context (JSON) |
| recorded_at | TIMESTAMP | When metric was recorded |

### ai_feedback
User feedback on AI responses.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Feedback ID |
| conversation_id | INTEGER | Conversation ID (FK) |
| message_id | INTEGER | Specific message ID (FK) |
| user_id | INTEGER | User providing feedback (FK) |
| feedback_type | TEXT | Type: positive, negative, neutral |
| rating | INTEGER | Rating 1-5 |
| comments | TEXT | Feedback comments |
| created_at | TIMESTAMP | Feedback timestamp |

## Session Management Tables

### sessions
User session tracking and management.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PRIMARY KEY | Session ID (UUID) |
| user_id | INTEGER | User ID (FK) |
| ip_address | TEXT | Client IP address |
| user_agent | TEXT | Client user agent |
| created_at | TIMESTAMP | Session creation time |
| last_activity | TIMESTAMP | Last activity time |
| expires_at | TIMESTAMP | Session expiration time |
| active | BOOLEAN DEFAULT 1 | Session status |
| session_data | TEXT DEFAULT '{}' | Session data (JSON) |
| security_flags | TEXT DEFAULT '{}' | Security settings (JSON) |

### session_activities
Session activity logging.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Activity ID |
| session_id | TEXT | Session ID (FK) |
| activity_type | TEXT NOT NULL | Type of activity |
| activity_data | TEXT DEFAULT '{}' | Activity details (JSON) |
| timestamp | TIMESTAMP | Activity timestamp |

### api_tokens
API authentication tokens.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Token ID |
| user_id | INTEGER | User ID (FK) |
| token_hash | TEXT UNIQUE NOT NULL | Hashed token |
| name | TEXT | Token name/description |
| permissions | TEXT DEFAULT '[]' | Token permissions (JSON) |
| created_at | TIMESTAMP | Creation time |
| expires_at | TIMESTAMP | Expiration time |
| last_used | TIMESTAMP | Last usage time |
| active | BOOLEAN DEFAULT 1 | Token status |
| usage_count | INTEGER DEFAULT 0 | Number of times used |
| rate_limit | INTEGER DEFAULT 1000 | Rate limit per hour |

## Database Indexes

The following indexes are created for optimal performance:

### User Indexes
- `idx_users_username` on `users(username)`
- `idx_users_email` on `users(email)`
- `idx_users_active` on `users(active)`
- `idx_users_last_login` on `users(last_login)`

### Device Indexes
- `idx_devices_ip` on `devices(ip_address)`
- `idx_devices_mac` on `devices(mac_address)`
- `idx_devices_online` on `devices(online)`
- `idx_devices_last_seen` on `devices(last_seen)`
- `idx_devices_type` on `devices(device_type)`

### Knowledge Indexes
- `idx_knowledge_title` on `knowledge_items(title)`
- `idx_knowledge_category` on `knowledge_items(category)`
- `idx_knowledge_author` on `knowledge_items(author_id)`
- `idx_knowledge_created` on `knowledge_items(created_at)`
- `idx_knowledge_status` on `knowledge_items(status)`
- `idx_knowledge_keywords` on `knowledge_items(search_keywords)`

### Tag Indexes
- `idx_tags_name` on `tags(name)`
- `idx_tags_category` on `tags(category)`
- `idx_tags_usage` on `tags(usage_count)`

### Conversation Indexes
- `idx_conversations_user` on `conversations(user_id)`
- `idx_conversations_session` on `conversations(session_id)`
- `idx_conversations_started` on `conversations(started_at)`
- `idx_conversations_status` on `conversations(status)`

### Message Indexes
- `idx_messages_conversation` on `conversation_messages(conversation_id)`
- `idx_messages_timestamp` on `conversation_messages(timestamp)`
- `idx_messages_role` on `conversation_messages(role)`

### Session Indexes
- `idx_sessions_user` on `sessions(user_id)`
- `idx_sessions_active` on `sessions(active)`
- `idx_sessions_expires` on `sessions(expires_at)`
- `idx_sessions_last_activity` on `sessions(last_activity)`

### Audit Indexes
- `idx_audit_user` on `audit_logs(user_id)`
- `idx_audit_action` on `audit_logs(action)`
- `idx_audit_timestamp` on `audit_logs(timestamp)`
- `idx_audit_resource` on `audit_logs(resource_type, resource_id)`

## Migration System

The database uses a versioned migration system:

- **Schema Version 1**: Initial comprehensive schema
- **Migration Table**: `schema_migrations` tracks applied migrations
- **Auto-Migration**: Automatically applies pending migrations on startup
- **Rollback Support**: Migrations can be rolled back to previous versions

### Migration Commands

```bash
# Check migration status
python -m noxcore.migrations status

# Apply migrations
python -m noxcore.migrations migrate

# Rollback to specific version
python -m noxcore.migrations rollback 0

# Validate schema
python -m noxcore.migrations validate
```

## Connection Pooling

The database implements connection pooling for improved performance:

- **Pool Size**: Configurable (default: 10 connections)
- **Connection Health**: Automatic health checking
- **WAL Mode**: Uses Write-Ahead Logging for better concurrency
- **Optimizations**: Various SQLite optimizations applied

## Administrative Tools

### Command Line Interface

```bash
# Database status
python -m noxcore.database_admin status

# Health check
python -m noxcore.database_admin health

# Create backup
python -m noxcore.database_admin backup --path backup.db

# Restore from backup
python -m noxcore.database_admin restore backup.db

# Optimize database
python -m noxcore.database_admin optimize

# Clean up old data
python -m noxcore.database_admin cleanup --days 30

# User management
python -m noxcore.database_admin user create username password --email user@example.com
python -m noxcore.database_admin user list
python -m noxcore.database_admin user reset-password username newpass
python -m noxcore.database_admin user deactivate username

# Data export/import
python -m noxcore.database_admin export data.json
python -m noxcore.database_admin import-knowledge knowledge.json

# Generate report
python -m noxcore.database_admin report --output report.json
```

## Usage Examples

### Basic Database Operations

```python
from noxcore.database_service import get_database_service

# Get database service
db = get_database_service()

# Create user
user_id = db.users.create_user('john', 'password123', 'john@example.com')

# Create knowledge item
item_id = db.knowledge.create_knowledge_item(
    title='Python Best Practices',
    content='Here are some Python best practices...',
    category='programming',
    author_id=user_id
)

# Search knowledge
results = db.knowledge.search_knowledge_items('Python')

# Create AI conversation
conv_id = db.conversations.create_conversation(
    user_id=user_id,
    title='Python Help',
    model_name='gpt-3.5-turbo'
)

# Add messages
db.conversations.add_message(conv_id, 'user', 'What are Python decorators?')
db.conversations.add_message(conv_id, 'assistant', 'Python decorators are...')
```

### Session Management

```python
# Create session
session_id = db.sessions.create_session(
    user_id=user_id,
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...'
)

# Get session
session = db.sessions.get_session(session_id)

# Invalidate session
db.sessions.invalidate_session(session_id)
```

### Database Maintenance

```python
# Get database status
status = db.get_status()
print(f"Database size: {status['database_size_mb']} MB")

# Create backup
success = db.backup_database('backup.db')

# Clean up old data
stats = db.cleanup_old_data(days=30)
print(f"Cleaned up: {stats}")

# Optimize database
db.optimize_database()
```

## Performance Considerations

1. **Connection Pooling**: Reduces connection overhead
2. **Indexing**: Comprehensive indexes for common queries
3. **WAL Mode**: Better concurrency than standard SQLite
4. **Query Optimization**: ANALYZE and PRAGMA optimize regularly
5. **Data Cleanup**: Regular cleanup of old data
6. **Connection Health**: Automatic detection of stale connections

## Security Features

1. **Password Hashing**: SHA-256 hashing (recommend bcrypt for production)
2. **Session Management**: Secure session handling with expiration
3. **Audit Logging**: Comprehensive activity logging
4. **API Tokens**: Token-based API authentication
5. **Input Validation**: Repository layer validates inputs
6. **SQL Injection Protection**: Parameterized queries throughout

## Backup and Recovery

1. **Automated Backups**: Scheduled backup capability
2. **Point-in-Time Recovery**: WAL mode enables point-in-time recovery
3. **Backup Validation**: Automatic validation of restored backups
4. **Metadata Tracking**: Backup metadata for verification
5. **Rolling Backups**: Configurable backup retention

## Monitoring and Health

1. **Health Checks**: Comprehensive database health monitoring
2. **Performance Metrics**: Connection pool utilization, query performance
3. **Integrity Checks**: Regular PRAGMA integrity_check
4. **Growth Monitoring**: Database size and table count tracking
5. **Activity Monitoring**: Recent activity and usage patterns

This documentation provides a comprehensive overview of the NoxGuard database system. For implementation details, refer to the source code in the `noxcore` module.