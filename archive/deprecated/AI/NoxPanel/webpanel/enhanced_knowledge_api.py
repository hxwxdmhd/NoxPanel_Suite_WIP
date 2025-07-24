"""
Enhanced Knowledge Management API Routes
=====================================

Advanced database-powered knowledge management with authentication.
Unlocked after Gates 1-2 completion.
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import sqlite3
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
import logging

# Create enhanced knowledge API blueprint
knowledge_api_bp = Blueprint('knowledge_api', __name__, url_prefix='/api/knowledge')

logger = logging.getLogger(__name__)

def require_auth(f):
    """Authentication decorator for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple session-based auth check
        if 'authenticated' not in session or not session['authenticated']:
            return jsonify({
                'error': 'Authentication required',
                'status': 'unauthorized'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Get database connection with proper error handling"""
    try:
        db_path = Path("data/db/knowledge.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Initialize tables if they don't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                content_type TEXT DEFAULT 'note',
                language TEXT,
                tags TEXT,
                is_featured BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                search_index TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_stats (
                id INTEGER PRIMARY KEY,
                total_items INTEGER DEFAULT 0,
                featured_items INTEGER DEFAULT 0,
                total_tags INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        return conn
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@knowledge_api_bp.route('/stats')
@require_auth
def get_stats():
    """Get enhanced knowledge base statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get comprehensive stats
        stats = {}
        
        # Basic counts
        result = conn.execute('SELECT COUNT(*) as total FROM knowledge_items').fetchone()
        stats['total_items'] = result['total'] if result else 0
        
        result = conn.execute('SELECT COUNT(*) as featured FROM knowledge_items WHERE is_featured = 1').fetchone()
        stats['featured_items'] = result['featured'] if result else 0
        
        # Items added today
        today = datetime.now().strftime('%Y-%m-%d')
        result = conn.execute(
            'SELECT COUNT(*) as today FROM knowledge_items WHERE DATE(created_at) = ?', 
            (today,)
        ).fetchone()
        stats['items_today'] = result['today'] if result else 0
        
        # Language distribution
        language_results = conn.execute('''
            SELECT language, COUNT(*) as count 
            FROM knowledge_items 
            WHERE language IS NOT NULL AND language != '' 
            GROUP BY language 
            ORDER BY count DESC
        ''').fetchall()
        
        stats['by_language'] = {row['language']: row['count'] for row in language_results}
        stats['languages_count'] = len(stats['by_language'])
        
        # Content type distribution
        type_results = conn.execute('''
            SELECT content_type, COUNT(*) as count 
            FROM knowledge_items 
            GROUP BY content_type
        ''').fetchall()
        
        stats['by_type'] = {row['content_type']: row['count'] for row in type_results}
        
        # Tag analysis
        all_tags = conn.execute('SELECT tags FROM knowledge_items WHERE tags IS NOT NULL').fetchall()
        unique_tags = set()
        for row in all_tags:
            if row['tags']:
                try:
                    tags = json.loads(row['tags'])
                    unique_tags.update(tags)
                except:
                    # Handle simple comma-separated tags
                    tags = [t.strip() for t in row['tags'].split(',')]
                    unique_tags.update(tags)
        
        stats['total_tags'] = len(unique_tags)
        stats['popular_tags'] = list(unique_tags)[:10]  # Top 10 for now
        
        # Performance metrics
        stats['response_time'] = round(time.time() * 1000) % 1000  # Simulated
        stats['last_updated'] = datetime.now().isoformat()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'database_connected': True,
            'authenticated': True
        })
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({
            'error': 'Failed to fetch stats',
            'status': 'error'
        }), 500

@knowledge_api_bp.route('/suggestions')
@require_auth
def get_search_suggestions():
    """Get search suggestions based on query"""
    try:
        query = request.args.get('q', '').strip().lower()
        if len(query) < 2:
            return jsonify({'suggestions': []})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'suggestions': []})
        
        suggestions = []
        
        # Title suggestions
        title_results = conn.execute('''
            SELECT DISTINCT title, content_type 
            FROM knowledge_items 
            WHERE LOWER(title) LIKE ? 
            LIMIT 5
        ''', (f'%{query}%',)).fetchall()
        
        for row in title_results:
            icon = {
                'code': 'code',
                'documentation': 'book',
                'script': 'terminal',
                'note': 'sticky-note'
            }.get(row['content_type'], 'file')
            
            suggestions.append({
                'text': row['title'],
                'type': row['content_type'],
                'icon': icon,
                'category': 'title'
            })
        
        # Tag suggestions
        tag_results = conn.execute('''
            SELECT DISTINCT tags, content_type 
            FROM knowledge_items 
            WHERE tags IS NOT NULL AND LOWER(tags) LIKE ?
            LIMIT 3
        ''', (f'%{query}%',)).fetchall()
        
        for row in tag_results:
            if row['tags']:
                try:
                    tags = json.loads(row['tags'])
                    matching_tags = [t for t in tags if query in t.lower()]
                    for tag in matching_tags[:2]:  # Max 2 per item
                        suggestions.append({
                            'text': tag,
                            'type': 'tag',
                            'icon': 'tag',
                            'category': 'tag'
                        })
                except:
                    pass
        
        # Language suggestions
        if any(lang.lower().startswith(query) for lang in ['python', 'javascript', 'bash', 'sql', 'html', 'css']):
            matching_langs = [lang for lang in ['python', 'javascript', 'bash', 'sql', 'html', 'css'] 
                            if lang.lower().startswith(query)]
            for lang in matching_langs:
                suggestions.append({
                    'text': lang,
                    'type': 'language',
                    'icon': 'code',
                    'category': 'language'
                })
        
        conn.close()
        
        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            key = (suggestion['text'], suggestion['type'])
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= 8:
                    break
        
        return jsonify({
            'suggestions': unique_suggestions,
            'query': query,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Suggestions API error: {e}")
        return jsonify({'suggestions': []})

@knowledge_api_bp.route('/search')
@require_auth
def advanced_search():
    """Enhanced search with database indexing"""
    try:
        query = request.args.get('q', '').strip()
        content_type = request.args.get('type', '')
        language = request.args.get('language', '')
        exact_match = request.args.get('exact_match') == 'on'
        include_content = request.args.get('include_content', 'on') == 'on'
        featured_only = request.args.get('featured_only') == 'on'
        
        if not query:
            return jsonify({'results': [], 'total': 0})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Build search query
        search_conditions = []
        search_params = []
        
        if exact_match:
            if include_content:
                search_conditions.append('(title = ? OR content = ?)')
                search_params.extend([query, query])
            else:
                search_conditions.append('title = ?')
                search_params.append(query)
        else:
            if include_content:
                search_conditions.append('(LOWER(title) LIKE ? OR LOWER(content) LIKE ?)')
                search_params.extend([f'%{query.lower()}%', f'%{query.lower()}%'])
            else:
                search_conditions.append('LOWER(title) LIKE ?')
                search_params.append(f'%{query.lower()}%')
        
        if content_type:
            search_conditions.append('content_type = ?')
            search_params.append(content_type)
        
        if language:
            search_conditions.append('language = ?')
            search_params.append(language)
        
        if featured_only:
            search_conditions.append('is_featured = 1')
        
        where_clause = ' AND '.join(search_conditions) if search_conditions else '1=1'
        
        # Execute search
        sql = f'''
            SELECT id, title, content, content_type, language, tags, is_featured, 
                   created_at, updated_at
            FROM knowledge_items 
            WHERE {where_clause}
            ORDER BY 
                CASE WHEN is_featured = 1 THEN 0 ELSE 1 END,
                updated_at DESC
            LIMIT 50
        '''
        
        results = conn.execute(sql, search_params).fetchall()
        
        # Format results
        formatted_results = []
        for row in results:
            item = dict(row)
            
            # Parse tags
            if item['tags']:
                try:
                    item['tags'] = json.loads(item['tags'])
                except:
                    item['tags'] = [t.strip() for t in item['tags'].split(',')]
            else:
                item['tags'] = []
            
            # Add relevance score (simplified)
            relevance = 0
            if query.lower() in item['title'].lower():
                relevance += 10
            if include_content and query.lower() in (item['content'] or '').lower():
                relevance += 5
            if item['is_featured']:
                relevance += 3
            
            item['relevance'] = relevance
            formatted_results.append(item)
        
        # Sort by relevance
        formatted_results.sort(key=lambda x: x['relevance'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'results': formatted_results,
            'total': len(formatted_results),
            'query': query,
            'filters': {
                'type': content_type,
                'language': language,
                'exact_match': exact_match,
                'include_content': include_content,
                'featured_only': featured_only
            },
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({
            'error': 'Search failed',
            'status': 'error'
        }), 500

@knowledge_api_bp.route('/analytics')
@require_auth
def get_analytics():
    """Get detailed analytics for knowledge base"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        analytics = {}
        
        # Growth over time (last 30 days)
        growth_data = conn.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM knowledge_items 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''').fetchall()
        
        analytics['growth'] = [dict(row) for row in growth_data]
        
        # Content type distribution
        type_dist = conn.execute('''
            SELECT content_type, COUNT(*) as count
            FROM knowledge_items
            GROUP BY content_type
            ORDER BY count DESC
        ''').fetchall()
        
        analytics['content_types'] = [dict(row) for row in type_dist]
        
        # Most popular tags
        all_tags = conn.execute('SELECT tags FROM knowledge_items WHERE tags IS NOT NULL').fetchall()
        tag_counts = {}
        for row in all_tags:
            if row['tags']:
                try:
                    tags = json.loads(row['tags'])
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except:
                    pass
        
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        analytics['popular_tags'] = [{'tag': tag, 'count': count} for tag, count in popular_tags]
        
        # Recent activity
        recent_items = conn.execute('''
            SELECT title, content_type, created_at
            FROM knowledge_items
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
        
        analytics['recent_activity'] = [dict(row) for row in recent_items]
        
        conn.close()
        
        return jsonify({
            'analytics': analytics,
            'generated_at': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Analytics API error: {e}")
        return jsonify({
            'error': 'Analytics generation failed',
            'status': 'error'
        }), 500

# Register the blueprint in the main application
def register_enhanced_knowledge_api(app):
    """Register the enhanced knowledge API with the Flask app"""
    app.register_blueprint(knowledge_api_bp)
    logger.info("Enhanced Knowledge Management API registered (Gates 1-2 unlocked)")
