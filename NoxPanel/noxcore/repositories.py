"""
Data Access Layer for NoxGuard---NoxPanel
Provides high-level interfaces for database operations
"""

import logging
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union, Tuple
from contextlib import contextmanager

from .database import NoxDatabase


# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logging.getLogger(__name__)

class BaseRepository:
    """Base repository class with common functionality"""
    
    def __init__(self, db: NoxDatabase) -> None:
        self.db = db
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string"""
        if isinstance(data, str):
            return data
        return json.dumps(data, default=str)
    
    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string to data"""
        if not data:
            return {}
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

class UserRepository(BaseRepository):
    """Repository for user management"""
    
    def create_user(self, username: str, password: str, email: str = None, 
                   role: str = 'user', **kwargs) -> Optional[int]:
        """Create a new user"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, email, role, settings, preferences)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    password_hash,
                    email,
                    role,
                    self._serialize_json(kwargs.get('settings', {})),
                    self._serialize_json(kwargs.get('preferences', {}))
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            return None
    
    def get_user(self, user_id: int = None, username: str = None) -> Optional[Dict[str, Any]]:
        """Get user by ID or username"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute("SELECT * FROM users WHERE id = ? AND active = 1", (user_id,))
                elif username:
                    cursor.execute("SELECT * FROM users WHERE username = ? AND active = 1", (username,))
                else:
                    return None
                
                row = cursor.fetchone()
                if row:
                    user = dict(row)
                    user['settings'] = self._deserialize_json(user['settings'])
                    user['preferences'] = self._deserialize_json(user['preferences'])
                    return user
                return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        user = self.get_user(username=username)
        if user:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user['password_hash'] == password_hash:
                # Update last login
                self.update_last_login(user['id'])
                return user
        return None
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")

class KnowledgeRepository(BaseRepository):
    """Repository for knowledge management"""
    
    def create_knowledge_item(self, title: str, content: str, category: str = 'general',
                            author_id: int = None, **kwargs) -> Optional[int]:
        """Create a new knowledge item"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO knowledge_items 
                    (title, content, content_type, category, source, source_url, 
                     author_id, metadata, search_keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    content,
                    kwargs.get('content_type', 'text'),
                    category,
                    kwargs.get('source'),
                    kwargs.get('source_url'),
                    author_id,
                    self._serialize_json(kwargs.get('metadata', {})),
                    kwargs.get('search_keywords', '')
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create knowledge item: {e}")
            return None
    
    def get_knowledge_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get knowledge item by ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT k.*, u.username as author_name 
                    FROM knowledge_items k 
                    LEFT JOIN users u ON k.author_id = u.id 
                    WHERE k.id = ? AND k.status = 'active'
                """, (item_id,))
                
                row = cursor.fetchone()
                if row:
                    item = dict(row)
                    item['metadata'] = self._deserialize_json(item['metadata'])
                    
                    # Update access tracking
                    conn.execute("""
                        UPDATE knowledge_items 
                        SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                        WHERE id = ?
                    """, (item_id,))
                    
                    return item
                return None
        except Exception as e:
            logger.error(f"Failed to get knowledge item {item_id}: {e}")
            return None
    
    def search_knowledge_items(self, query: str, category: str = None, 
                             limit: int = 50) -> List[Dict[str, Any]]:
        """Search knowledge items"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    SELECT k.*, u.username as author_name 
                    FROM knowledge_items k 
                    LEFT JOIN users u ON k.author_id = u.id 
                    WHERE k.status = 'active' AND (
                        k.title LIKE ? OR k.content LIKE ? OR k.search_keywords LIKE ?
                    )
                """
                params = [f"%{query}%", f"%{query}%", f"%{query}%"]
                
                if category:
                    sql += " AND k.category = ?"
                    params.append(category)
                
                sql += " ORDER BY k.access_count DESC, k.updated_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                items = []
                for row in cursor.fetchall():
                    item = dict(row)
                    item['metadata'] = self._deserialize_json(item['metadata'])
                    items.append(item)
                
                return items
        except Exception as e:
            logger.error(f"Failed to search knowledge items: {e}")
            return []
    
    def get_knowledge_categories(self) -> List[str]:
        """Get all knowledge categories"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT category FROM knowledge_items 
                    WHERE status = 'active' 
                    ORDER BY category
                """)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get knowledge categories: {e}")
            return []

class TagRepository(BaseRepository):
    """Repository for tag management"""
    
    def create_tag(self, name: str, description: str = None, color: str = '#808080',
                  category: str = 'general', created_by: int = None) -> Optional[int]:
        """Create a new tag"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tags (name, description, color, category, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, description, color, category, created_by))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create tag {name}: {e}")
            return None
    
    def get_tag(self, tag_id: int = None, name: str = None) -> Optional[Dict[str, Any]]:
        """Get tag by ID or name"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if tag_id:
                    cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
                elif name:
                    cursor.execute("SELECT * FROM tags WHERE name = ?", (name,))
                else:
                    return None
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get tag: {e}")
            return None
    
    def add_tag_to_knowledge_item(self, knowledge_item_id: int, tag_id: int) -> bool:
        """Add tag to knowledge item"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO knowledge_item_tags (knowledge_item_id, tag_id)
                    VALUES (?, ?)
                """, (knowledge_item_id, tag_id))
                
                # Update tag usage count
                conn.execute("""
                    UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?
                """, (tag_id,))
                return True
        except Exception as e:
            logger.error(f"Failed to add tag to knowledge item: {e}")
            return False

class ConversationRepository(BaseRepository):
    """Repository for AI conversation management"""
    
    def create_conversation(self, user_id: int, session_id: str = None, 
                          title: str = None, model_name: str = None) -> Optional[int]:
        """Create a new conversation"""
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (user_id, session_id, title, model_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, session_id, title, model_name))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return None
    
    def add_message(self, conversation_id: int, role: str, content: str,
                   token_count: int = 0, response_time: float = None,
                   model_name: str = None) -> Optional[int]:
        """Add message to conversation"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_messages 
                    (conversation_id, role, content, token_count, response_time, model_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (conversation_id, role, content, token_count, response_time, model_name))
                
                # Update conversation token count
                conn.execute("""
                    UPDATE conversations 
                    SET total_tokens = total_tokens + ? 
                    WHERE id = ?
                """, (token_count, conversation_id))
                
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add message to conversation: {e}")
            return None
    
    def get_conversation(self, conversation_id: int, include_messages: bool = True) -> Optional[Dict[str, Any]]:
        """Get conversation with optional messages"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM conversations c 
                    LEFT JOIN users u ON c.user_id = u.id 
                    WHERE c.id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                conversation = dict(row)
                conversation['metadata'] = self._deserialize_json(conversation['metadata'])
                
                if include_messages:
                    cursor.execute("""
                        SELECT * FROM conversation_messages 
                        WHERE conversation_id = ? 
                        ORDER BY timestamp
                    """, (conversation_id,))
                    
                    messages = []
                    for msg_row in cursor.fetchall():
                        message = dict(msg_row)
                        message['metadata'] = self._deserialize_json(message['metadata'])
                        messages.append(message)
                    
                    conversation['messages'] = messages
                
                return conversation
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    def get_user_conversations(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's conversations"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, COUNT(cm.id) as message_count
                    FROM conversations c 
                    LEFT JOIN conversation_messages cm ON c.id = cm.conversation_id
                    WHERE c.user_id = ? 
                    GROUP BY c.id
                    ORDER BY c.started_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                conversations = []
                for row in cursor.fetchall():
                    conv = dict(row)
                    conv['metadata'] = self._deserialize_json(conv['metadata'])
                    conversations.append(conv)
                
                return conversations
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []

class SessionRepository(BaseRepository):
    """Repository for session management"""
    
    def create_session(self, user_id: int, ip_address: str = None, 
                      user_agent: str = None, expires_in_hours: int = 24) -> Optional[str]:
        """Create a new session"""
        try:
            session_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO sessions (id, user_id, ip_address, user_agent, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, user_id, ip_address, user_agent, expires_at.isoformat()))
                
                return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get active session"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, u.username, u.role 
                    FROM sessions s 
                    LEFT JOIN users u ON s.user_id = u.id 
                    WHERE s.id = ? AND s.active = 1 AND s.expires_at > ?
                """, (session_id, datetime.now().isoformat()))
                
                row = cursor.fetchone()
                if row:
                    session = dict(row)
                    session['session_data'] = self._deserialize_json(session['session_data'])
                    session['security_flags'] = self._deserialize_json(session['security_flags'])
                    
                    # Update last activity
                    conn.execute("""
                        UPDATE sessions 
                        SET last_activity = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (session_id,))
                    
                    return session
                return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE sessions SET active = 0 WHERE id = ?
                """, (session_id,))
                return True
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET active = 0 
                    WHERE expires_at <= ? OR last_activity <= ?
                """, (
                    datetime.now().isoformat(),
                    (datetime.now() - timedelta(days=7)).isoformat()
                ))
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

class AuditRepository(BaseRepository):
    """Repository for audit logging"""
    
    def log_action(self, user_id: int, action: str, resource_type: str = None,
                  resource_id: str = None, details: Dict[str, Any] = None,
                  ip_address: str = None, user_agent: str = None) -> bool:
        """Log an audit action"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_logs 
                    (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, action, resource_type, resource_id,
                    self._serialize_json(details or {}), ip_address, user_agent
                ))
                return True
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            return False
    
    def get_audit_logs(self, user_id: int = None, action: str = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    SELECT a.*, u.username 
                    FROM audit_logs a 
                    LEFT JOIN users u ON a.user_id = u.id 
                    WHERE 1=1
                """
                params = []
                
                if user_id:
                    sql += " AND a.user_id = ?"
                    params.append(user_id)
                
                if action:
                    sql += " AND a.action = ?"
                    params.append(action)
                
                sql += " ORDER BY a.timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                
                logs = []
                for row in cursor.fetchall():
                    log = dict(row)
                    log['details'] = self._deserialize_json(log['details'])
                    logs.append(log)
                
                return logs
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

# Export all repositories
__all__ = [
    'BaseRepository', 'UserRepository', 'KnowledgeRepository', 
    'TagRepository', 'ConversationRepository', 'SessionRepository', 'AuditRepository'
]