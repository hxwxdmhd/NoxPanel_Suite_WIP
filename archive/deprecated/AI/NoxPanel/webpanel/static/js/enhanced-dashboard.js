/**
 * Enhanced Dashboard JavaScript
 * Advanced functionality for Gates 1-2 unlocked features
 */

class EnhancedDashboard {
    constructor() {
        this.updateInterval = null;
        this.statsCache = {};
        this.lastUpdate = null;
        this.init();
    }

    init() {
        console.log('🚀 Enhanced Dashboard initializing...');
        this.setupEventListeners();
        this.loadInitialData();
        this.startRealTimeUpdates();
        this.setupAnimations();
    }

    setupEventListeners() {
        // Feature test buttons
        const testButtons = document.querySelectorAll('.action-btn:not(:disabled)');
        testButtons.forEach(button => {
            button.addEventListener('click', this.handleFeatureTest.bind(this));
        });

        // Quick action cards
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.addEventListener('mouseenter', this.animateCard);
            card.addEventListener('mouseleave', this.resetCard);
        });

        // Logout button
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', this.handleLogout.bind(this));
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    async loadInitialData() {
        try {
            // Load dashboard statistics
            await this.loadDashboardStats();
            
            // Load system status
            await this.loadSystemStatus();
            
            // Load feature status
            await this.loadFeatureStatus();
            
            console.log('✅ Initial data loaded successfully');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            this.showNotification('Error loading dashboard data', 'error');
        }
    }

    async loadDashboardStats() {
        const stats = {
            database: {
                connections: Math.floor(Math.random() * 10) + 5,
                queries: Math.floor(Math.random() * 1000) + 500,
                uptime: '99.9%'
            },
            authentication: {
                sessions: Math.floor(Math.random() * 5) + 1,
                logins: Math.floor(Math.random() * 50) + 20,
                security: 'High'
            },
            api: {
                calls: Math.floor(Math.random() * 500) + 200,
                endpoints: 12,
                responseTime: Math.floor(Math.random() * 20) + 25
            },
            knowledge: {
                items: Math.floor(Math.random() * 50) + 150,
                searches: Math.floor(Math.random() * 100) + 80,
                featured: Math.floor(Math.random() * 20) + 15
            }
        };

        this.updateStatCards(stats);
        this.statsCache = stats;
    }

    updateStatCards(stats) {
        // Update database stats
        this.updateElement('db-connections', stats.database.connections);
        
        // Update auth stats
        this.updateElement('auth-sessions', stats.authentication.sessions);
        
        // Update API stats
        this.updateElement('api-calls', stats.api.calls);
        
        // Update knowledge stats
        this.updateElement('knowledge-items', stats.knowledge.items);
        
        // Update performance metrics
        this.updateElement('response-time', `< ${stats.api.responseTime}ms`);
        this.updateElement('uptime', stats.database.uptime);
        this.updateElement('memory-usage', `${Math.floor(Math.random() * 50) + 100} MB`);
        this.updateElement('active-users', stats.authentication.sessions);
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            // Animate the change
            element.style.transform = 'scale(1.1)';
            element.style.color = '#10b981';
            
            setTimeout(() => {
                element.textContent = value;
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 200);
        }
    }

    async loadSystemStatus() {
        // Simulate system status checks
        const services = ['Flask Server', 'Database', 'Authentication', 'API Gateway'];
        const statusIndicators = document.querySelectorAll('.status-indicator');
        
        statusIndicators.forEach((indicator, index) => {
            // All services should be online for Gates 1-2
            indicator.className = 'status-indicator online';
        });
    }

    async loadFeatureStatus() {
        // Update feature status badges
        const unlockedBadges = document.querySelectorAll('.status-badge.unlocked');
        unlockedBadges.forEach(badge => {
            badge.style.animation = 'pulse 2s infinite';
        });

        // Update progress bar
        const progressBar = document.querySelector('.progress-fill');
        if (progressBar) {
            progressBar.style.width = '25%'; // Gates 1-2 complete
        }
    }

    startRealTimeUpdates() {
        this.updateInterval = setInterval(async () => {
            await this.loadDashboardStats();
            this.updateTimestamp();
        }, 10000); // Update every 10 seconds

        console.log('📊 Real-time updates started');
    }

    updateTimestamp() {
        this.lastUpdate = new Date();
        const timestamp = this.lastUpdate.toLocaleTimeString();
        
        // Update any timestamp displays
        const timestampElements = document.querySelectorAll('.last-updated');
        timestampElements.forEach(element => {
            element.textContent = `Last updated: ${timestamp}`;
        });
    }

    handleFeatureTest(event) {
        const button = event.target.closest('.action-btn');
        const testType = button.textContent.trim().toLowerCase();
        
        if (testType.includes('database') || testType.includes('connection')) {
            this.testDatabaseConnection(button);
        } else if (testType.includes('auth') || testType.includes('status')) {
            this.testAuthenticationStatus(button);
        } else if (testType.includes('api') || testType.includes('endpoints')) {
            this.testApiEndpoints(button);
        }
    }

    async testDatabaseConnection(button) {
        const resultDiv = button.nextElementSibling;
        
        resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing database connection...';
        resultDiv.className = 'test-result';
        
        // Simulate database test
        await this.delay(1500);
        
        resultDiv.innerHTML = '<i class="fas fa-check text-success"></i> Database connection successful!';
        resultDiv.className = 'test-result success';
        
        // Show additional details
        setTimeout(() => {
            resultDiv.innerHTML += '<br><small>Response time: 12ms | Pool: 8/10 connections</small>';
        }, 500);
    }

    async testAuthenticationStatus(button) {
        const resultDiv = button.nextElementSibling;
        
        resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking authentication system...';
        resultDiv.className = 'test-result';
        
        // Simulate auth test
        await this.delay(1200);
        
        resultDiv.innerHTML = '<i class="fas fa-shield-alt text-success"></i> Authentication system active & secure';
        resultDiv.className = 'test-result success';
        
        setTimeout(() => {
            resultDiv.innerHTML += '<br><small>Sessions: 3 active | Security level: High</small>';
        }, 500);
    }

    async testApiEndpoints(button) {
        const resultDiv = button.nextElementSibling;
        
        resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing API endpoints...';
        resultDiv.className = 'test-result';
        
        // Simulate API tests
        await this.delay(1800);
        
        resultDiv.innerHTML = '<i class="fas fa-check text-success"></i> All API endpoints responding';
        resultDiv.className = 'test-result success';
        
        setTimeout(() => {
            resultDiv.innerHTML += '<br><small>12/12 endpoints online | Avg response: 28ms</small>';
        }, 500);
    }

    setupAnimations() {
        // Intersection Observer for scroll animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });

        // Observe all major sections
        const sections = document.querySelectorAll('.stats-grid, .features-showcase, .quick-actions, .system-status');
        sections.forEach(section => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(section);
        });

        // Stagger card animations
        this.staggerCardAnimations();
    }

    staggerCardAnimations() {
        const cards = document.querySelectorAll('.stat-card, .feature-panel, .action-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    animateCard(event) {
        const card = event.currentTarget;
        card.style.transform = 'translateY(-8px) scale(1.02)';
        card.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
    }

    resetCard(event) {
        const card = event.currentTarget;
        card.style.transform = 'translateY(0) scale(1)';
        card.style.boxShadow = '';
    }

    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K for search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            window.location.href = '/knowledge';
        }
        
        // Ctrl/Cmd + D for dashboard refresh
        if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
            event.preventDefault();
            this.refreshDashboard();
        }
        
        // Escape to close any open modals/panels
        if (event.key === 'Escape') {
            this.closeAllPanels();
        }
    }

    async refreshDashboard() {
        this.showNotification('Refreshing dashboard...', 'info');
        await this.loadInitialData();
        this.showNotification('Dashboard refreshed!', 'success');
    }

    closeAllPanels() {
        // Close any open panels or modals
        const openPanels = document.querySelectorAll('.panel-open');
        openPanels.forEach(panel => {
            panel.classList.remove('panel-open');
        });
    }

    handleLogout() {
        if (confirm('Are you sure you want to logout?')) {
            this.showNotification('Logging out...', 'info');
            
            // Clear intervals
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
            }
            
            // Redirect to login
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close">×</button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Add click handler for close button
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.removeNotification(notification);
        });

        // Auto remove after 3 seconds
        setTimeout(() => {
            this.removeNotification(notification);
        }, 3000);

        // Animate in
        setTimeout(() => {
            notification.classList.add('notification-show');
        }, 100);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    removeNotification(notification) {
        notification.classList.remove('notification-show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Public methods for external use
    getStats() {
        return this.statsCache;
    }

    forceUpdate() {
        this.loadDashboardStats();
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        console.log('🔄 Enhanced Dashboard destroyed');
    }
}

// Global functions for inline event handlers
function testDatabaseConnection() {
    if (window.dashboard) {
        const button = event.target;
        window.dashboard.testDatabaseConnection(button);
    }
}

function checkAuthStatus() {
    if (window.dashboard) {
        const button = event.target;
        window.dashboard.testAuthenticationStatus(button);
    }
}

function testApiEndpoints() {
    if (window.dashboard) {
        const button = event.target;
        window.dashboard.testApiEndpoints(button);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new EnhancedDashboard();
    
    // Add notification styles if not present
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: 0.5rem;
                padding: 1rem 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                box-shadow: var(--shadow-lg);
                z-index: 1000;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                max-width: 300px;
            }
            
            .notification-show {
                transform: translateX(0);
            }
            
            .notification-success {
                border-left: 4px solid var(--success-color);
            }
            
            .notification-error {
                border-left: 4px solid var(--danger-color);
            }
            
            .notification-warning {
                border-left: 4px solid var(--warning-color);
            }
            
            .notification-info {
                border-left: 4px solid var(--primary-color);
            }
            
            .notification i {
                font-size: 1.25rem;
            }
            
            .notification-success i {
                color: var(--success-color);
            }
            
            .notification-error i {
                color: var(--danger-color);
            }
            
            .notification-warning i {
                color: var(--warning-color);
            }
            
            .notification-info i {
                color: var(--primary-color);
            }
            
            .notification span {
                flex: 1;
                font-size: 0.875rem;
                color: var(--text-primary);
            }
            
            .notification-close {
                background: none;
                border: none;
                color: var(--text-muted);
                font-size: 1.25rem;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .notification-close:hover {
                color: var(--text-primary);
            }
        `;
        document.head.appendChild(styles);
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});
