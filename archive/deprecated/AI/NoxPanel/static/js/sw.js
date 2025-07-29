/**
 * Service Worker for Heimnetz/NoxPanel/NoxGuard Suite v7.0
 * Provides offline capabilities and performance optimizations
 */

const CACHE_NAME = 'heimnetz-suite-v7.0';
const STATIC_CACHE = 'static-v7.0';
const DYNAMIC_CACHE = 'dynamic-v7.0';

// Files to cache for offline functionality
const STATIC_FILES = [
    '/',
    '/static/css/ultimate-dashboard.css',
    '/static/css/enhanced-themes.css',
    '/static/css/visual-enhancements.css',
    '/static/js/enhanced-theme-manager.js',
    '/templates/ultimate_dashboard.html',
    '/noxpanel',
    '/heimnetz',
    '/noxguard'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/api/models',
    '/api/network/devices',
    '/api/security/status'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('📦 Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('✅ Service Worker installed successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ Service Worker installation failed:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }
    
    // Handle static files
    if (isStaticFile(request.url)) {
        event.respondWith(cacheFirst(request));
        return;
    }
    
    // Handle API requests
    if (isApiRequest(request.url)) {
        event.respondWith(networkFirst(request));
        return;
    }
    
    // Handle page requests
    if (isPageRequest(request)) {
        event.respondWith(staleWhileRevalidate(request));
        return;
    }
    
    // Default: network only
    event.respondWith(fetch(request));
});

// Cache-first strategy for static files
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Cache-first failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

// Network-first strategy for API requests
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return new Response(JSON.stringify({
            error: 'Offline',
            message: 'Network unavailable and no cached data'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Stale-while-revalidate strategy for pages
async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    // Fetch fresh version in background
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    });
    
    // Return cached version immediately if available
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Otherwise wait for network
    return fetchPromise;
}

// Helper functions
function isStaticFile(url) {
    return url.includes('/static/') || 
           url.endsWith('.css') || 
           url.endsWith('.js') || 
           url.endsWith('.png') || 
           url.endsWith('.jpg') || 
           url.endsWith('.svg') || 
           url.endsWith('.ico');
}

function isApiRequest(url) {
    return url.includes('/api/');
}

function isPageRequest(request) {
    return request.headers.get('Accept')?.includes('text/html');
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    console.log('🔄 Background sync triggered');
    
    try {
        // Sync offline actions when back online
        const offlineActions = await getOfflineActions();
        
        for (const action of offlineActions) {
            await processOfflineAction(action);
        }
        
        await clearOfflineActions();
        console.log('✅ Background sync completed');
    } catch (error) {
        console.error('❌ Background sync failed:', error);
    }
}

async function getOfflineActions() {
    // In a real implementation, this would get actions from IndexedDB
    return [];
}

async function processOfflineAction(action) {
    // Process queued offline actions
    console.log('Processing offline action:', action);
}

async function clearOfflineActions() {
    // Clear processed offline actions
    console.log('Clearing offline actions');
}

// Push notification handling
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const options = {
        body: event.data.text(),
        icon: '/static/images/icon-192.png',
        badge: '/static/images/badge-72.png',
        vibrate: [200, 100, 200],
        data: {
            timestamp: Date.now(),
            url: '/'
        },
        actions: [
            {
                action: 'open',
                title: 'Open App',
                icon: '/static/images/open-icon.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/images/dismiss-icon.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Heimnetz Suite', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/')
        );
    }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

console.log('🚀 Service Worker script loaded - Heimnetz Suite v7.0');
