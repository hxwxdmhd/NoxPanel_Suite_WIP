#!/usr/bin/env python3
"""
Plugin Framework Registry and Marketplace

This module implements the plugin registry and marketplace foundation for 
discovering, managing, and distributing plugins in the framework ecosystem.

Key Features:
- Centralized plugin registry with search and discovery
- Plugin marketplace with ratings and reviews
- Plugin dependency resolution and compatibility checking
- Automatic updates and version management
- Plugin security scanning and validation
- Community features and plugin collections
- Enterprise plugin distribution support
"""

import asyncio
import json
import logging
import hashlib
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import semantic_version

# Import core framework components
from plugin_framework_core import (
    PluginMetadata, PluginType, PluginDependency, DependencyType
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Registry and Marketplace Types
# ============================================================================

class PluginStatus(Enum):
    """Plugin status in the registry"""
    DRAFT = "draft"              # Plugin is in development
    PENDING = "pending"          # Awaiting approval
    APPROVED = "approved"        # Approved for distribution
    PUBLISHED = "published"      # Available in marketplace
    DEPRECATED = "deprecated"    # No longer maintained
    ARCHIVED = "archived"        # Removed from marketplace
    REJECTED = "rejected"        # Failed approval process


class SecurityScanStatus(Enum):
    """Security scan status"""
    NOT_SCANNED = "not_scanned"
    SCANNING = "scanning"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class PluginRating:
    """Plugin rating and review"""
    user_id: str
    rating: int  # 1-5 stars
    review: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    helpful_votes: int = 0
    verified_purchase: bool = False


@dataclass
class PluginStatistics:
    """Plugin usage statistics"""
    download_count: int = 0
    active_installations: int = 0
    daily_active_users: int = 0
    weekly_active_users: int = 0
    monthly_active_users: int = 0
    avg_rating: float = 0.0
    rating_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityScanResult:
    """Security scan result"""
    scan_id: str
    status: SecurityScanStatus
    score: int  # 0-100
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=datetime.now)
    scanner_version: str = "1.0.0"


@dataclass
class PluginRegistryEntry:
    """Complete plugin registry entry"""
    metadata: PluginMetadata
    status: PluginStatus = PluginStatus.DRAFT
    
    # Marketplace Information
    publisher_id: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    price: float = 0.0  # 0 for free plugins
    license_type: str = "MIT"
    
    # Statistics and Metrics
    statistics: PluginStatistics = field(default_factory=PluginStatistics)
    ratings: List[PluginRating] = field(default_factory=list)
    
    # Security and Compliance
    security_scan: Optional[SecurityScanResult] = None
    compliance_checks: Dict[str, bool] = field(default_factory=dict)
    
    # Version Management
    versions: List[str] = field(default_factory=list)
    latest_version: str = ""
    
    # Distribution
    download_url: str = ""
    package_hash: str = ""
    package_size: int = 0
    
    # Registry Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None


@dataclass
class PluginCollection:
    """Curated plugin collection"""
    id: str
    name: str
    description: str
    curator_id: str
    plugin_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_featured: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MarketplaceSearchQuery:
    """Marketplace search query"""
    query: str = ""
    plugin_type: Optional[PluginType] = None
    category: str = ""
    tags: List[str] = field(default_factory=list)
    min_rating: float = 0.0
    max_price: float = float('inf')
    free_only: bool = False
    sort_by: str = "relevance"  # relevance, downloads, rating, updated
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0


# ============================================================================
# Plugin Registry Core
# ============================================================================

class PluginRegistry:
    """
    Core plugin registry with database storage and search capabilities.
    """
    
    def __init__(self, registry_db_path: Path = None):
        self.registry_db_path = registry_db_path or Path("./plugin_registry.db")
        self.registry_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # In-memory cache for frequent lookups
        self.plugin_cache: Dict[str, PluginRegistryEntry] = {}
        self.collection_cache: Dict[str, PluginCollection] = {}
        
        self.logger = logging.getLogger("PluginRegistry")
        self.logger.info("Plugin Registry initialized")
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        
        with sqlite3.connect(self.registry_db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Plugins table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS plugins (
                    id TEXT PRIMARY KEY,
                    metadata_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    publisher_id TEXT NOT NULL,
                    category TEXT,
                    tags_json TEXT,
                    price REAL DEFAULT 0.0,
                    license_type TEXT,
                    statistics_json TEXT,
                    security_scan_json TEXT,
                    compliance_json TEXT,
                    versions_json TEXT,
                    latest_version TEXT,
                    download_url TEXT,
                    package_hash TEXT,
                    package_size INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    published_at TEXT
                )
            ''')
            
            # Ratings table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ratings (
                    plugin_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    review TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    helpful_votes INTEGER DEFAULT 0,
                    verified_purchase BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (plugin_id, user_id),
                    FOREIGN KEY (plugin_id) REFERENCES plugins(id)
                )
            ''')
            
            # Collections table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    curator_id TEXT NOT NULL,
                    plugin_ids_json TEXT,
                    tags_json TEXT,
                    is_featured BOOLEAN DEFAULT FALSE,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Download statistics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS download_stats (
                    plugin_id TEXT NOT NULL,
                    user_id TEXT,
                    downloaded_at TEXT,
                    version TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (plugin_id) REFERENCES plugins(id)
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugins(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_plugins_publisher ON plugins(publisher_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ratings_plugin ON ratings(plugin_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_downloads_plugin ON download_stats(plugin_id)')
            
            conn.commit()
    
    # ========================================================================
    # Plugin Registration and Management
    # ========================================================================
    
    async def register_plugin(self, entry: PluginRegistryEntry) -> bool:
        """
        Register a new plugin in the registry.
        
        Args:
            entry: Plugin registry entry to register
            
        Returns:
            True if registration successful, False otherwise
        """
        
        try:
            # Validate plugin entry
            if not await self._validate_plugin_entry(entry):
                self.logger.error(f"Plugin entry validation failed: {entry.metadata.id}")
                return False
            
            # Check for existing plugin
            existing = await self.get_plugin(entry.metadata.id)
            if existing:
                self.logger.warning(f"Plugin already registered: {entry.metadata.id}")
                return await self.update_plugin(entry)
            
            # Insert into database
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.execute('''
                    INSERT INTO plugins (
                        id, metadata_json, status, publisher_id, category,
                        tags_json, price, license_type, statistics_json,
                        security_scan_json, compliance_json, versions_json,
                        latest_version, download_url, package_hash, package_size,
                        created_at, updated_at, published_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.metadata.id,
                    json.dumps(asdict(entry.metadata)),
                    entry.status.value,
                    entry.publisher_id,
                    entry.category,
                    json.dumps(entry.tags),
                    entry.price,
                    entry.license_type,
                    json.dumps(asdict(entry.statistics)),
                    json.dumps(asdict(entry.security_scan)) if entry.security_scan else None,
                    json.dumps(entry.compliance_checks),
                    json.dumps(entry.versions),
                    entry.latest_version,
                    entry.download_url,
                    entry.package_hash,
                    entry.package_size,
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat(),
                    entry.published_at.isoformat() if entry.published_at else None
                ))
                
                # Insert ratings
                for rating in entry.ratings:
                    conn.execute('''
                        INSERT OR REPLACE INTO ratings (
                            plugin_id, user_id, rating, review, created_at,
                            updated_at, helpful_votes, verified_purchase
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        entry.metadata.id,
                        rating.user_id,
                        rating.rating,
                        rating.review,
                        rating.created_at.isoformat(),
                        rating.updated_at.isoformat(),
                        rating.helpful_votes,
                        rating.verified_purchase
                    ))
                
                conn.commit()
            
            # Update cache
            self.plugin_cache[entry.metadata.id] = entry
            
            self.logger.info(f"Successfully registered plugin: {entry.metadata.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering plugin: {e}")
            return False
    
    async def update_plugin(self, entry: PluginRegistryEntry) -> bool:
        """Update an existing plugin entry"""
        
        try:
            entry.updated_at = datetime.now()
            
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.execute('''
                    UPDATE plugins SET
                        metadata_json = ?, status = ?, publisher_id = ?,
                        category = ?, tags_json = ?, price = ?, license_type = ?,
                        statistics_json = ?, security_scan_json = ?,
                        compliance_json = ?, versions_json = ?, latest_version = ?,
                        download_url = ?, package_hash = ?, package_size = ?,
                        updated_at = ?, published_at = ?
                    WHERE id = ?
                ''', (
                    json.dumps(asdict(entry.metadata)),
                    entry.status.value,
                    entry.publisher_id,
                    entry.category,
                    json.dumps(entry.tags),
                    entry.price,
                    entry.license_type,
                    json.dumps(asdict(entry.statistics)),
                    json.dumps(asdict(entry.security_scan)) if entry.security_scan else None,
                    json.dumps(entry.compliance_checks),
                    json.dumps(entry.versions),
                    entry.latest_version,
                    entry.download_url,
                    entry.package_hash,
                    entry.package_size,
                    entry.updated_at.isoformat(),
                    entry.published_at.isoformat() if entry.published_at else None,
                    entry.metadata.id
                ))
                
                conn.commit()
            
            # Update cache
            self.plugin_cache[entry.metadata.id] = entry
            
            self.logger.info(f"Successfully updated plugin: {entry.metadata.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating plugin: {e}")
            return False
    
    async def get_plugin(self, plugin_id: str) -> Optional[PluginRegistryEntry]:
        """Get a plugin entry from the registry"""
        
        try:
            # Check cache first
            if plugin_id in self.plugin_cache:
                return self.plugin_cache[plugin_id]
            
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM plugins WHERE id = ?
                ''', (plugin_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Convert row to PluginRegistryEntry
                entry = await self._row_to_plugin_entry(row)
                
                # Load ratings
                ratings_cursor = conn.execute('''
                    SELECT * FROM ratings WHERE plugin_id = ?
                ''', (plugin_id,))
                
                for rating_row in ratings_cursor.fetchall():
                    rating = PluginRating(
                        user_id=rating_row['user_id'],
                        rating=rating_row['rating'],
                        review=rating_row['review'] or "",
                        created_at=datetime.fromisoformat(rating_row['created_at']),
                        updated_at=datetime.fromisoformat(rating_row['updated_at']),
                        helpful_votes=rating_row['helpful_votes'],
                        verified_purchase=rating_row['verified_purchase']
                    )
                    entry.ratings.append(rating)
                
                # Update cache
                self.plugin_cache[plugin_id] = entry
                
                return entry
                
        except Exception as e:
            self.logger.error(f"Error getting plugin {plugin_id}: {e}")
            return None
    
    async def _validate_plugin_entry(self, entry: PluginRegistryEntry) -> bool:
        """Validate plugin entry before registration"""
        
        try:
            # Check required fields
            if not entry.metadata.id:
                return False
            if not entry.metadata.name:
                return False
            if not entry.metadata.version:
                return False
            if not entry.publisher_id:
                return False
            
            # Validate version format
            try:
                semantic_version.Version(entry.metadata.version)
            except ValueError:
                self.logger.warning(f"Invalid version format: {entry.metadata.version}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating plugin entry: {e}")
            return False
    
    async def _row_to_plugin_entry(self, row: sqlite3.Row) -> PluginRegistryEntry:
        """Convert database row to PluginRegistryEntry"""
        
        # Parse JSON fields
        metadata_dict = json.loads(row['metadata_json'])
        statistics_dict = json.loads(row['statistics_json'])
        tags = json.loads(row['tags_json']) if row['tags_json'] else []
        versions = json.loads(row['versions_json']) if row['versions_json'] else []
        compliance = json.loads(row['compliance_json']) if row['compliance_json'] else {}
        
        # Create metadata object (simplified - would need proper deserialization)
        metadata = PluginMetadata(
            id=metadata_dict['id'],
            name=metadata_dict['name'],
            version=metadata_dict['version'],
            description=metadata_dict.get('description', ''),
            author=metadata_dict.get('author', ''),
            plugin_type=PluginType(metadata_dict.get('plugin_type', 'utility'))
        )
        
        # Create statistics object
        statistics = PluginStatistics(
            download_count=statistics_dict.get('download_count', 0),
            active_installations=statistics_dict.get('active_installations', 0),
            avg_rating=statistics_dict.get('avg_rating', 0.0),
            rating_count=statistics_dict.get('rating_count', 0)
        )
        
        # Parse security scan if present
        security_scan = None
        if row['security_scan_json']:
            scan_dict = json.loads(row['security_scan_json'])
            security_scan = SecurityScanResult(
                scan_id=scan_dict['scan_id'],
                status=SecurityScanStatus(scan_dict['status']),
                score=scan_dict['score']
            )
        
        # Create entry
        entry = PluginRegistryEntry(
            metadata=metadata,
            status=PluginStatus(row['status']),
            publisher_id=row['publisher_id'],
            category=row['category'] or "",
            tags=tags,
            price=row['price'],
            license_type=row['license_type'],
            statistics=statistics,
            security_scan=security_scan,
            compliance_checks=compliance,
            versions=versions,
            latest_version=row['latest_version'],
            download_url=row['download_url'],
            package_hash=row['package_hash'],
            package_size=row['package_size'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else None
        )
        
        return entry
    
    # ========================================================================
    # Plugin Search and Discovery
    # ========================================================================
    
    async def search_plugins(self, query: MarketplaceSearchQuery) -> List[PluginRegistryEntry]:
        """
        Search plugins in the registry.
        
        Args:
            query: Search query parameters
            
        Returns:
            List of matching plugin entries
        """
        
        try:
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build SQL query
                sql_parts = ["SELECT * FROM plugins WHERE 1=1"]
                params = []
                
                # Status filter (only published by default)
                sql_parts.append("AND status = 'published'")
                
                # Text search
                if query.query:
                    sql_parts.append("""
                        AND (
                            id LIKE ? OR 
                            JSON_EXTRACT(metadata_json, '$.name') LIKE ? OR 
                            JSON_EXTRACT(metadata_json, '$.description') LIKE ?
                        )
                    """)
                    search_term = f"%{query.query}%"
                    params.extend([search_term, search_term, search_term])
                
                # Plugin type filter
                if query.plugin_type:
                    sql_parts.append("AND JSON_EXTRACT(metadata_json, '$.plugin_type') = ?")
                    params.append(query.plugin_type.value)
                
                # Category filter
                if query.category:
                    sql_parts.append("AND category = ?")
                    params.append(query.category)
                
                # Price filter
                if query.free_only:
                    sql_parts.append("AND price = 0")
                elif query.max_price < float('inf'):
                    sql_parts.append("AND price <= ?")
                    params.append(query.max_price)
                
                # Rating filter
                if query.min_rating > 0:
                    sql_parts.append("AND JSON_EXTRACT(statistics_json, '$.avg_rating') >= ?")
                    params.append(query.min_rating)
                
                # Tag filter
                if query.tags:
                    for tag in query.tags:
                        sql_parts.append("AND tags_json LIKE ?")
                        params.append(f'%"{tag}"%')
                
                # Sorting
                sort_column = {
                    'downloads': 'JSON_EXTRACT(statistics_json, "$.download_count")',
                    'rating': 'JSON_EXTRACT(statistics_json, "$.avg_rating")',
                    'updated': 'updated_at',
                    'relevance': 'updated_at'  # Default fallback
                }.get(query.sort_by, 'updated_at')
                
                sort_direction = 'DESC' if query.sort_order == 'desc' else 'ASC'
                sql_parts.append(f"ORDER BY {sort_column} {sort_direction}")
                
                # Pagination
                sql_parts.append("LIMIT ? OFFSET ?")
                params.extend([query.limit, query.offset])
                
                # Execute query
                sql = " ".join(sql_parts)
                cursor = conn.execute(sql, params)
                
                results = []
                for row in cursor.fetchall():
                    entry = await self._row_to_plugin_entry(row)
                    results.append(entry)
                
                self.logger.info(f"Search returned {len(results)} results")
                return results
                
        except Exception as e:
            self.logger.error(f"Error searching plugins: {e}")
            return []
    
    async def get_featured_plugins(self, limit: int = 10) -> List[PluginRegistryEntry]:
        """Get featured plugins"""
        
        query = MarketplaceSearchQuery(
            sort_by="downloads",
            sort_order="desc",
            limit=limit
        )
        
        return await self.search_plugins(query)
    
    async def get_trending_plugins(self, days: int = 7, limit: int = 10) -> List[PluginRegistryEntry]:
        """Get trending plugins based on recent downloads"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute('''
                    SELECT p.*, COUNT(d.plugin_id) as recent_downloads
                    FROM plugins p
                    LEFT JOIN download_stats d ON p.id = d.plugin_id
                        AND datetime(d.downloaded_at) >= ?
                    WHERE p.status = 'published'
                    GROUP BY p.id
                    ORDER BY recent_downloads DESC
                    LIMIT ?
                ''', (cutoff_date.isoformat(), limit))
                
                results = []
                for row in cursor.fetchall():
                    entry = await self._row_to_plugin_entry(row)
                    results.append(entry)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error getting trending plugins: {e}")
            return []
    
    # ========================================================================
    # Plugin Collections
    # ========================================================================
    
    async def create_collection(self, collection: PluginCollection) -> bool:
        """Create a new plugin collection"""
        
        try:
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.execute('''
                    INSERT INTO collections (
                        id, name, description, curator_id, plugin_ids_json,
                        tags_json, is_featured, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    collection.id,
                    collection.name,
                    collection.description,
                    collection.curator_id,
                    json.dumps(collection.plugin_ids),
                    json.dumps(collection.tags),
                    collection.is_featured,
                    collection.created_at.isoformat(),
                    collection.updated_at.isoformat()
                ))
                
                conn.commit()
            
            # Update cache
            self.collection_cache[collection.id] = collection
            
            self.logger.info(f"Created collection: {collection.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            return False
    
    async def get_collection(self, collection_id: str) -> Optional[PluginCollection]:
        """Get a plugin collection"""
        
        try:
            # Check cache first
            if collection_id in self.collection_cache:
                return self.collection_cache[collection_id]
            
            with sqlite3.connect(self.registry_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM collections WHERE id = ?
                ''', (collection_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                collection = PluginCollection(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    curator_id=row['curator_id'],
                    plugin_ids=json.loads(row['plugin_ids_json']),
                    tags=json.loads(row['tags_json']) if row['tags_json'] else [],
                    is_featured=row['is_featured'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
                # Update cache
                self.collection_cache[collection_id] = collection
                
                return collection
                
        except Exception as e:
            self.logger.error(f"Error getting collection {collection_id}: {e}")
            return None


# ============================================================================
# Plugin Marketplace
# ============================================================================

class PluginMarketplace:
    """
    Plugin marketplace with advanced features for plugin discovery,
    distribution, and community interaction.
    """
    
    def __init__(self, registry: PluginRegistry, marketplace_config: Dict[str, Any] = None):
        self.registry = registry
        self.config = marketplace_config or {}
        
        # Marketplace features
        self.enable_ratings = self.config.get("enable_ratings", True)
        self.enable_reviews = self.config.get("enable_reviews", True)
        self.enable_collections = self.config.get("enable_collections", True)
        self.enable_paid_plugins = self.config.get("enable_paid_plugins", False)
        
        self.logger = logging.getLogger("PluginMarketplace")
        self.logger.info("Plugin Marketplace initialized")
    
    # ========================================================================
    # Plugin Discovery and Browsing
    # ========================================================================
    
    async def browse_plugins(self, category: str = None, page: int = 1, 
                           per_page: int = 20) -> Dict[str, Any]:
        """
        Browse plugins in the marketplace.
        
        Args:
            category: Plugin category to browse
            page: Page number for pagination
            per_page: Number of plugins per page
            
        Returns:
            Browsing results with plugins and metadata
        """
        
        try:
            query = MarketplaceSearchQuery(
                category=category or "",
                limit=per_page,
                offset=(page - 1) * per_page,
                sort_by="downloads",
                sort_order="desc"
            )
            
            plugins = await self.registry.search_plugins(query)
            
            # Get total count for pagination
            total_count = await self._get_plugin_count(category)
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                "plugins": [await self._plugin_entry_to_marketplace_info(p) for p in plugins],
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "total_count": total_count
                },
                "category": category,
                "featured_plugins": [
                    await self._plugin_entry_to_marketplace_info(p) 
                    for p in await self.registry.get_featured_plugins(5)
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error browsing plugins: {e}")
            return {
                "plugins": [],
                "pagination": {"current_page": page, "per_page": per_page, "total_pages": 0, "total_count": 0},
                "category": category,
                "featured_plugins": []
            }
    
    async def search_marketplace(self, search_query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search the plugin marketplace.
        
        Args:
            search_query: Search query string
            filters: Additional search filters
            
        Returns:
            Search results with plugins and metadata
        """
        
        try:
            filters = filters or {}
            
            query = MarketplaceSearchQuery(
                query=search_query,
                plugin_type=PluginType(filters.get("plugin_type")) if filters.get("plugin_type") else None,
                category=filters.get("category", ""),
                tags=filters.get("tags", []),
                min_rating=filters.get("min_rating", 0.0),
                max_price=filters.get("max_price", float('inf')),
                free_only=filters.get("free_only", False),
                sort_by=filters.get("sort_by", "relevance"),
                sort_order=filters.get("sort_order", "desc"),
                limit=filters.get("limit", 50),
                offset=filters.get("offset", 0)
            )
            
            plugins = await self.registry.search_plugins(query)
            
            return {
                "query": search_query,
                "results": [await self._plugin_entry_to_marketplace_info(p) for p in plugins],
                "count": len(plugins),
                "filters_applied": filters,
                "suggestions": await self._get_search_suggestions(search_query)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching marketplace: {e}")
            return {
                "query": search_query,
                "results": [],
                "count": 0,
                "filters_applied": filters,
                "suggestions": []
            }
    
    async def get_plugin_details(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed plugin information for marketplace display"""
        
        try:
            entry = await self.registry.get_plugin(plugin_id)
            if not entry:
                return None
            
            details = await self._plugin_entry_to_marketplace_info(entry)
            
            # Add detailed information
            details.update({
                "versions": entry.versions,
                "dependencies": [asdict(dep) for dep in entry.metadata.dependencies],
                "security_scan": asdict(entry.security_scan) if entry.security_scan else None,
                "compliance_checks": entry.compliance_checks,
                "download_url": entry.download_url,
                "package_size": entry.package_size,
                "installation_guide": await self._generate_installation_guide(entry),
                "compatibility": await self._check_compatibility(entry),
                "related_plugins": await self._get_related_plugins(entry),
                "recent_updates": await self._get_recent_updates(plugin_id)
            })
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting plugin details: {e}")
            return None
    
    async def _plugin_entry_to_marketplace_info(self, entry: PluginRegistryEntry) -> Dict[str, Any]:
        """Convert plugin entry to marketplace display format"""
        
        return {
            "id": entry.metadata.id,
            "name": entry.metadata.name,
            "version": entry.metadata.version,
            "description": entry.metadata.description,
            "author": entry.metadata.author,
            "publisher": entry.publisher_id,
            "category": entry.category,
            "tags": entry.tags,
            "plugin_type": entry.metadata.plugin_type.value,
            "price": entry.price,
            "license": entry.license_type,
            "statistics": {
                "downloads": entry.statistics.download_count,
                "rating": entry.statistics.avg_rating,
                "rating_count": entry.statistics.rating_count,
                "active_installations": entry.statistics.active_installations
            },
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "published_at": entry.published_at.isoformat() if entry.published_at else None,
            "ratings": [asdict(r) for r in entry.ratings[-5:]]  # Last 5 ratings
        }
    
    # ========================================================================
    # Plugin Ratings and Reviews
    # ========================================================================
    
    async def add_rating(self, plugin_id: str, user_id: str, rating: int, review: str = "") -> bool:
        """Add a rating and review for a plugin"""
        
        try:
            if not self.enable_ratings:
                return False
            
            if not (1 <= rating <= 5):
                self.logger.error("Rating must be between 1 and 5")
                return False
            
            # Get plugin entry
            entry = await self.registry.get_plugin(plugin_id)
            if not entry:
                self.logger.error(f"Plugin not found: {plugin_id}")
                return False
            
            # Create or update rating
            existing_rating = None
            for i, r in enumerate(entry.ratings):
                if r.user_id == user_id:
                    existing_rating = i
                    break
            
            new_rating = PluginRating(
                user_id=user_id,
                rating=rating,
                review=review,
                created_at=datetime.now() if existing_rating is None else entry.ratings[existing_rating].created_at,
                updated_at=datetime.now()
            )
            
            if existing_rating is not None:
                entry.ratings[existing_rating] = new_rating
            else:
                entry.ratings.append(new_rating)
            
            # Recalculate statistics
            await self._update_rating_statistics(entry)
            
            # Update in registry
            await self.registry.update_plugin(entry)
            
            self.logger.info(f"Added rating for plugin {plugin_id} by user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding rating: {e}")
            return False
    
    async def _update_rating_statistics(self, entry: PluginRegistryEntry):
        """Update plugin rating statistics"""
        
        if not entry.ratings:
            entry.statistics.avg_rating = 0.0
            entry.statistics.rating_count = 0
            return
        
        total_rating = sum(r.rating for r in entry.ratings)
        entry.statistics.avg_rating = total_rating / len(entry.ratings)
        entry.statistics.rating_count = len(entry.ratings)
    
    # ========================================================================
    # Dependency Resolution and Compatibility
    # ========================================================================
    
    async def resolve_dependencies(self, plugin_id: str) -> Dict[str, Any]:
        """
        Resolve plugin dependencies and check compatibility.
        
        Args:
            plugin_id: Plugin to resolve dependencies for
            
        Returns:
            Dependency resolution results
        """
        
        try:
            entry = await self.registry.get_plugin(plugin_id)
            if not entry:
                return {"success": False, "error": "Plugin not found"}
            
            resolution_result = {
                "success": True,
                "plugin_id": plugin_id,
                "dependencies": [],
                "conflicts": [],
                "missing": [],
                "optional_missing": [],
                "install_order": []
            }
            
            # Analyze dependencies
            for dependency in entry.metadata.dependencies:
                dep_result = await self._resolve_single_dependency(dependency)
                
                if dep_result["available"]:
                    resolution_result["dependencies"].append(dep_result)
                else:
                    if dependency.optional:
                        resolution_result["optional_missing"].append(dep_result)
                    else:
                        resolution_result["missing"].append(dep_result)
                        resolution_result["success"] = False
            
            # Build installation order (topological sort)
            if resolution_result["success"]:
                resolution_result["install_order"] = await self._build_install_order(
                    plugin_id, resolution_result["dependencies"]
                )
            
            return resolution_result
            
        except Exception as e:
            self.logger.error(f"Error resolving dependencies: {e}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_single_dependency(self, dependency: PluginDependency) -> Dict[str, Any]:
        """Resolve a single dependency"""
        
        if dependency.type == DependencyType.PLUGIN:
            # Check if plugin exists in registry
            plugin_entry = await self.registry.get_plugin(dependency.name)
            
            return {
                "name": dependency.name,
                "type": dependency.type.value,
                "version_requirement": dependency.version_requirement,
                "available": plugin_entry is not None,
                "available_version": plugin_entry.metadata.version if plugin_entry else None,
                "compatible": self._check_version_compatibility(
                    plugin_entry.metadata.version if plugin_entry else None,
                    dependency.version_requirement
                ),
                "optional": dependency.optional
            }
        
        elif dependency.type == DependencyType.PYTHON_PACKAGE:
            # This would check PyPI or local packages
            return {
                "name": dependency.name,
                "type": dependency.type.value,
                "version_requirement": dependency.version_requirement,
                "available": True,  # Simplified - would check actual availability
                "available_version": "unknown",
                "compatible": True,
                "optional": dependency.optional
            }
        
        else:
            # Other dependency types
            return {
                "name": dependency.name,
                "type": dependency.type.value,
                "version_requirement": dependency.version_requirement,
                "available": True,  # Simplified
                "available_version": "unknown",
                "compatible": True,
                "optional": dependency.optional
            }
    
    def _check_version_compatibility(self, available_version: str, requirement: str) -> bool:
        """Check if available version satisfies requirement"""
        
        if not available_version or requirement == "*":
            return True
        
        try:
            spec = semantic_version.SimpleSpec(requirement)
            version = semantic_version.Version(available_version)
            return spec.match(version)
        except Exception:
            return False
    
    async def _build_install_order(self, root_plugin_id: str, dependencies: List[Dict[str, Any]]) -> List[str]:
        """Build installation order using topological sort"""
        
        # Simplified implementation - would need full dependency graph analysis
        install_order = []
        
        # Add plugin dependencies first
        for dep in dependencies:
            if dep["type"] == "plugin" and dep["name"] not in install_order:
                install_order.append(dep["name"])
        
        # Add root plugin last
        install_order.append(root_plugin_id)
        
        return install_order
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    async def _get_plugin_count(self, category: str = None) -> int:
        """Get total plugin count for pagination"""
        
        try:
            with sqlite3.connect(self.registry.registry_db_path) as conn:
                if category:
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM plugins 
                        WHERE status = 'published' AND category = ?
                    ''', (category,))
                else:
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM plugins WHERE status = 'published'
                    ''')
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Error getting plugin count: {e}")
            return 0
    
    async def _get_search_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions based on query"""
        
        # Simplified implementation - would use more sophisticated suggestion logic
        suggestions = []
        
        if query:
            # Add plugin type suggestions
            for plugin_type in PluginType:
                if plugin_type.value.startswith(query.lower()):
                    suggestions.append(plugin_type.value)
            
            # Add common category suggestions
            common_categories = ["network", "security", "monitoring", "automation", "utility"]
            for category in common_categories:
                if category.startswith(query.lower()):
                    suggestions.append(category)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    async def _generate_installation_guide(self, entry: PluginRegistryEntry) -> Dict[str, Any]:
        """Generate installation guide for plugin"""
        
        return {
            "steps": [
                {"step": 1, "description": "Download plugin package", "command": f"download {entry.metadata.id}"},
                {"step": 2, "description": "Verify package integrity", "command": f"verify {entry.package_hash}"},
                {"step": 3, "description": "Install dependencies", "command": "resolve-dependencies"},
                {"step": 4, "description": "Load plugin", "command": f"load-plugin {entry.metadata.id}"},
                {"step": 5, "description": "Configure plugin", "command": "configure"}
            ],
            "requirements": {
                "framework_version": entry.metadata.framework_version,
                "python_version": entry.metadata.python_requires,
                "memory_mb": entry.metadata.estimated_memory_mb,
                "network_access": entry.metadata.requires_network,
                "filesystem_access": entry.metadata.requires_filesystem
            }
        }
    
    async def _check_compatibility(self, entry: PluginRegistryEntry) -> Dict[str, Any]:
        """Check plugin compatibility with current environment"""
        
        return {
            "framework_compatible": True,  # Simplified
            "python_compatible": True,
            "dependencies_satisfied": True,
            "security_level": "medium",
            "warnings": [],
            "recommendations": []
        }
    
    async def _get_related_plugins(self, entry: PluginRegistryEntry, limit: int = 5) -> List[Dict[str, Any]]:
        """Get plugins related to the given plugin"""
        
        # Find plugins with similar tags or category
        query = MarketplaceSearchQuery(
            category=entry.category,
            tags=entry.tags[:3],  # Use first few tags
            limit=limit + 1
        )
        
        related = await self.registry.search_plugins(query)
        
        # Remove the original plugin from results
        related = [p for p in related if p.metadata.id != entry.metadata.id][:limit]
        
        return [await self._plugin_entry_to_marketplace_info(p) for p in related]
    
    async def _get_recent_updates(self, plugin_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent updates for a plugin"""
        
        # Simplified implementation - would track actual update history
        return [
            {
                "version": "1.2.0",
                "date": "2024-01-15T10:30:00",
                "changes": ["Added new features", "Bug fixes", "Performance improvements"]
            }
        ]


# ============================================================================
# Plugin Security Scanner
# ============================================================================

class PluginSecurityScanner:
    """
    Security scanner for plugins to detect potential security issues.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("PluginSecurityScanner")
    
    async def scan_plugin(self, plugin_entry: PluginRegistryEntry) -> SecurityScanResult:
        """
        Perform security scan on a plugin.
        
        Args:
            plugin_entry: Plugin entry to scan
            
        Returns:
            Security scan result
        """
        
        try:
            scan_id = hashlib.md5(f"{plugin_entry.metadata.id}_{datetime.now()}".encode()).hexdigest()
            
            scan_result = SecurityScanResult(
                scan_id=scan_id,
                status=SecurityScanStatus.SCANNING,
                score=0
            )
            
            # Perform various security checks
            issues = []
            score = 100  # Start with perfect score
            
            # Check for dangerous imports
            dangerous_imports = await self._check_dangerous_imports(plugin_entry)
            if dangerous_imports:
                issues.extend(dangerous_imports)
                score -= len(dangerous_imports) * 10
            
            # Check for suspicious network operations
            network_issues = await self._check_network_operations(plugin_entry)
            if network_issues:
                issues.extend(network_issues)
                score -= len(network_issues) * 15
            
            # Check for file system operations
            filesystem_issues = await self._check_filesystem_operations(plugin_entry)
            if filesystem_issues:
                issues.extend(filesystem_issues)
                score -= len(filesystem_issues) * 5
            
            # Check for code quality issues
            quality_issues = await self._check_code_quality(plugin_entry)
            if quality_issues:
                issues.extend(quality_issues)
                score -= len(quality_issues) * 2
            
            # Final score and status
            scan_result.score = max(0, score)
            scan_result.issues = issues
            
            if scan_result.score >= 80:
                scan_result.status = SecurityScanStatus.PASSED
            elif scan_result.score >= 60:
                scan_result.status = SecurityScanStatus.WARNING
            else:
                scan_result.status = SecurityScanStatus.FAILED
            
            # Generate recommendations
            scan_result.recommendations = await self._generate_recommendations(scan_result)
            
            self.logger.info(f"Security scan completed for {plugin_entry.metadata.id}: {scan_result.status.value}")
            
            return scan_result
            
        except Exception as e:
            self.logger.error(f"Error scanning plugin: {e}")
            return SecurityScanResult(
                scan_id="error",
                status=SecurityScanStatus.ERROR,
                score=0,
                issues=[{"type": "scan_error", "message": str(e)}]
            )
    
    async def _check_dangerous_imports(self, plugin_entry: PluginRegistryEntry) -> List[Dict[str, Any]]:
        """Check for potentially dangerous imports"""
        
        dangerous_modules = [
            "subprocess", "os.system", "eval", "exec", "compile", 
            "__import__", "importlib", "pickle", "shelve"
        ]
        
        issues = []
        
        # This would analyze the actual plugin code
        # For now, return example issues
        
        return issues
    
    async def _check_network_operations(self, plugin_entry: PluginRegistryEntry) -> List[Dict[str, Any]]:
        """Check for suspicious network operations"""
        
        issues = []
        
        # Check if plugin requires network but doesn't declare it
        if not plugin_entry.metadata.requires_network:
            # Would check for network-related imports/operations
            pass
        
        return issues
    
    async def _check_filesystem_operations(self, plugin_entry: PluginRegistryEntry) -> List[Dict[str, Any]]:
        """Check for filesystem operations"""
        
        issues = []
        
        # Check if plugin requires filesystem but doesn't declare it
        if not plugin_entry.metadata.requires_filesystem:
            # Would check for file operations
            pass
        
        return issues
    
    async def _check_code_quality(self, plugin_entry: PluginRegistryEntry) -> List[Dict[str, Any]]:
        """Check for code quality issues"""
        
        issues = []
        
        # Check for common code quality issues
        # - Missing documentation
        # - No error handling
        # - Hard-coded secrets
        # etc.
        
        return issues
    
    async def _generate_recommendations(self, scan_result: SecurityScanResult) -> List[str]:
        """Generate security recommendations based on scan results"""
        
        recommendations = []
        
        if scan_result.score < 80:
            recommendations.append("Consider improving plugin security by addressing identified issues")
        
        if scan_result.score < 60:
            recommendations.append("Plugin requires significant security improvements before deployment")
        
        # Add specific recommendations based on issues found
        for issue in scan_result.issues:
            if issue.get("type") == "dangerous_import":
                recommendations.append(f"Review usage of {issue.get('module')} for security implications")
        
        return recommendations


# ============================================================================
# Example Usage and Testing
# ============================================================================

async def main():
    """Example usage of the Plugin Registry and Marketplace"""
    
    print("🏪 Plugin Framework Registry and Marketplace - Example Usage")
    print("=" * 70)
    
    # Initialize registry and marketplace
    print("\n📝 Initializing registry and marketplace...")
    registry = PluginRegistry()
    marketplace = PluginMarketplace(registry)
    scanner = PluginSecurityScanner()
    
    # Create example plugin entry
    print("\n🔌 Creating example plugin entry...")
    
    from plugin_framework_core import PluginMetadata, PluginType
    
    metadata = PluginMetadata(
        id="example_network_plugin",
        name="Example Network Plugin",
        version="1.2.0",
        description="A sample network monitoring plugin for demonstration",
        author="Registry Example",
        plugin_type=PluginType.NETWORK,
        requires_network=True
    )
    
    entry = PluginRegistryEntry(
        metadata=metadata,
        status=PluginStatus.PUBLISHED,
        publisher_id="example_publisher",
        category="monitoring",
        tags=["network", "monitoring", "example"],
        statistics=PluginStatistics(
            download_count=150,
            avg_rating=4.2,
            rating_count=8
        )
    )
    
    # Register plugin
    print(f"📋 Registering plugin: {entry.metadata.id}")
    success = await registry.register_plugin(entry)
    print(f"Registration result: {'✅ Success' if success else '❌ Failed'}")
    
    # Search marketplace
    print(f"\n🔍 Searching marketplace for 'network' plugins...")
    search_results = await marketplace.search_marketplace("network")
    print(f"Found {search_results['count']} plugins")
    
    for plugin in search_results['results'][:3]:
        print(f"  - {plugin['name']} v{plugin['version']} ({plugin['statistics']['downloads']} downloads)")
    
    # Browse plugins by category
    print(f"\n📂 Browsing plugins in 'monitoring' category...")
    browse_results = await marketplace.browse_plugins("monitoring")
    print(f"Found {len(browse_results['plugins'])} plugins in category")
    
    # Add rating
    print(f"\n⭐ Adding rating for plugin...")
    await marketplace.add_rating(entry.metadata.id, "example_user", 5, "Great plugin!")
    
    # Security scan
    print(f"\n🔒 Performing security scan...")
    scan_result = await scanner.scan_plugin(entry)
    print(f"Security scan: {scan_result.status.value} (score: {scan_result.score}/100)")
    
    # Get plugin details
    print(f"\n📄 Getting detailed plugin information...")
    details = await marketplace.get_plugin_details(entry.metadata.id)
    if details:
        print(f"Plugin: {details['name']}")
        print(f"Author: {details['author']}")
        print(f"Rating: {details['statistics']['rating']:.1f} ({details['statistics']['rating_count']} reviews)")
        print(f"Downloads: {details['statistics']['downloads']}")
    
    # Resolve dependencies
    print(f"\n🔗 Resolving plugin dependencies...")
    resolution = await marketplace.resolve_dependencies(entry.metadata.id)
    print(f"Dependency resolution: {'✅ Success' if resolution['success'] else '❌ Failed'}")
    print(f"Install order: {resolution['install_order']}")
    
    print("\n🎉 Registry and Marketplace demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
