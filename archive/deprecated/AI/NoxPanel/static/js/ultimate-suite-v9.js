/**
 * 🚀 ULTIMATE SUITE v9.0 - ENHANCED JAVASCRIPT
 * =============================================
 * 
 * Enhanced JavaScript for SysAdmin Copilot, Plugin Framework,
 * and improved v8.0 features with real-time monitoring.
 */

class UltimateSuiteV9 {
    constructor() {
        this.config = {
            apiBaseUrl: '',
            updateInterval: 5000,
            chartUpdateInterval: 2000,
            maxChatMessages: 100,
            animationDuration: 300
        };
        
        this.state = {
            activeSection: 'dashboard',
            systemHealth: {},
            networkData: {},
            aiModels: [],
            plugins: [],
            realTimeData: {},
            chatHistory: [],
            charts: {}
        };
        
        this.eventSource = null;
        this.updateTimers = new Map();
        
        this.init();
    }
    
    /**
     * Initialize the Ultimate Suite v9.0
     */
    async init() {
        console.log('🚀 Ultimate Suite v9.0 - Initializing...');
        
        try {
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize Monaco Editor for script editing
            this.initializeScriptEditor();
            
            // Load initial data
            await this.loadInitialData();
            
            // Setup real-time monitoring
            this.setupRealTimeMonitoring();
            
            // Initialize charts
            this.initializeCharts();
            
            console.log('✅ Ultimate Suite v9.0 - Initialization complete!');
            
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.showNotification('Initialization failed', 'error');
        }
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1': this.showSection('dashboard'); e.preventDefault(); break;
                    case '2': this.showSection('sysadmin'); e.preventDefault(); break;
                    case '3': this.showSection('plugins'); e.preventDefault(); break;
                    case '4': this.showSection('network'); e.preventDefault(); break;
                    case '5': this.showSection('ai-chat'); e.preventDefault(); break;
                    case '6': this.showSection('monitoring'); e.preventDefault(); break;
                }
            }
        });
        
        // Form submissions
        const copilotInput = document.getElementById('copilot-message');
        if (copilotInput) {
            copilotInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendCopilotMessage();
                }
            });
        }
        
        const aiChatInput = document.getElementById('ai-chat-input');
        if (aiChatInput) {
            aiChatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendAIMessage();
                }
            });
        }
        
        // Window resize handler
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 250));
    }
    
    /**
     * Initialize Monaco Editor for script editing
     */
    initializeScriptEditor() {
        if (typeof monaco !== 'undefined') {
            require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});
            require(['vs/editor/editor.main'], () => {
                this.scriptEditor = monaco.editor.create(document.getElementById('script-editor'), {
                    value: '# Generated script will appear here...',
                    language: 'powershell',
                    theme: 'vs-dark',
                    automaticLayout: true,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    wordWrap: 'on'
                });
            });
        }
    }
    
    /**
     * Load initial data
     */
    async loadInitialData() {
        const loadingPromises = [
            this.loadSystemStatus(),
            this.loadAIModels(),
            this.loadPlugins(),
            this.loadSystemHealth(),
            this.loadNetworkData()
        ];
        
        await Promise.allSettled(loadingPromises);
    }
    
    /**
     * Load system status
     */
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.updateStatusIndicators(status);
            this.state.systemStatus = status;
            
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }
    
    /**
     * Load AI models
     */
    async loadAIModels() {
        try {
            const response = await fetch('/api/ai/models');
            const data = await response.json();
            
            this.state.aiModels = data.models || [];
            this.updateAIModelsDisplay();
            this.populateAIModelSelect();
            
        } catch (error) {
            console.error('Failed to load AI models:', error);
            this.updateAIModelsDisplay([]);
        }
    }
    
    /**
     * Load plugins
     */
    async loadPlugins() {
        try {
            const response = await fetch('/api/plugins');
            const data = await response.json();
            
            this.state.plugins = data.plugins || [];
            this.updatePluginsDisplay();
            
        } catch (error) {
            console.error('Failed to load plugins:', error);
            this.updatePluginsDisplay([]);
        }
    }
    
    /**
     * Load system health
     */
    async loadSystemHealth() {
        try {
            const response = await fetch('/api/sysadmin/health');
            const health = await response.json();
            
            this.state.systemHealth = health;
            this.updateHealthDisplay(health);
            
        } catch (error) {
            console.error('Failed to load system health:', error);
        }
    }
    
    /**
     * Load network data
     */
    async loadNetworkData() {
        try {
            const response = await fetch('/api/network/topology');
            const networkData = await response.json();
            
            this.state.networkData = networkData;
            this.updateNetworkDisplay(networkData);
            
        } catch (error) {
            console.error('Failed to load network data:', error);
        }
    }
    
    /**
     * Setup real-time monitoring
     */
    setupRealTimeMonitoring() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource('/api/monitoring/realtime');
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleRealTimeUpdate(data);
            } catch (error) {
                console.error('Error parsing real-time data:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('Real-time monitoring connection error:', error);
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                if (this.eventSource.readyState === EventSource.CLOSED) {
                    this.setupRealTimeMonitoring();
                }
            }, 5000);
        };
    }
    
    /**
     * Handle real-time updates
     */
    handleRealTimeUpdate(data) {
        this.state.realTimeData = data;
        
        // Update system health
        if (data.system_health) {
            this.updateHealthDisplay(data.system_health);
        }
        
        // Update network status
        if (data.network_status) {
            this.updateNetworkStatus(data.network_status);
        }
        
        // Update charts
        this.updateRealTimeCharts(data);
        
        // Update plugin status
        if (data.plugin_status) {
            this.updatePluginStatus(data.plugin_status);
        }
    }
    
    /**
     * Initialize charts
     */
    initializeCharts() {
        // Performance Chart
        const performanceCanvas = document.getElementById('performance-chart');
        if (performanceCanvas) {
            this.state.charts.performance = new Chart(performanceCanvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: '#00a8ff',
                            backgroundColor: 'rgba(0, 168, 255, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Memory %',
                            data: [],
                            borderColor: '#7c4dff',
                            backgroundColor: 'rgba(124, 77, 255, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#ffffff' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#b0bec5' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { color: '#b0bec5' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }
        
        // Network Chart
        const networkCanvas = document.getElementById('network-chart');
        if (networkCanvas) {
            this.state.charts.network = new Chart(networkCanvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Upload KB/s',
                            data: [],
                            borderColor: '#00e676',
                            backgroundColor: 'rgba(0, 230, 118, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Download KB/s',
                            data: [],
                            borderColor: '#ff6b35',
                            backgroundColor: 'rgba(255, 107, 53, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#ffffff' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#b0bec5' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        y: {
                            min: 0,
                            ticks: { color: '#b0bec5' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }
        
        // Disk Chart
        const diskCanvas = document.getElementById('disk-chart');
        if (diskCanvas) {
            this.state.charts.disk = new Chart(diskCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Free'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#ff5252', '#00e676'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#ffffff' }
                        }
                    }
                }
            });
        }
    }
    
    /**
     * Show section
     */
    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Remove active class from nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
            this.state.activeSection = sectionId;
        }
        
        // Add active class to nav item
        const navItem = document.querySelector(`[href="#${sectionId}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }
        
        // Load section-specific data
        this.loadSectionData(sectionId);
    }
    
    /**
     * Load section-specific data
     */
    async loadSectionData(sectionId) {
        switch(sectionId) {
            case 'sysadmin':
                await this.loadMaintenanceSuggestions();
                await this.loadTaskHistory();
                break;
            case 'plugins':
                await this.loadPlugins();
                break;
            case 'network':
                await this.loadNetworkData();
                break;
            case 'monitoring':
                this.refreshCharts();
                break;
        }
    }
    
    /**
     * SysAdmin Copilot Functions
     */
    async sendCopilotMessage() {
        const messageInput = document.getElementById('copilot-message');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        const chatArea = document.getElementById('copilot-chat');
        
        // Add user message
        this.addChatMessage(chatArea, 'user', message);
        messageInput.value = '';
        
        // Add loading indicator
        const loadingId = this.addChatMessage(chatArea, 'copilot', this.createLoadingIndicator('Analyzing...'));
        
        try {
            const response = await fetch('/api/sysadmin/troubleshoot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ problem: message })
            });
            
            const result = await response.json();
            
            // Remove loading message
            this.removeChatMessage(loadingId);
            
            if (result.ai_analysis) {
                this.addChatMessage(chatArea, 'copilot', this.formatAIResponse(result.ai_analysis));
            } else {
                this.addChatMessage(chatArea, 'copilot', result.error || 'Sorry, I could not analyze this problem.');
            }
            
        } catch (error) {
            this.removeChatMessage(loadingId);
            this.addChatMessage(chatArea, 'copilot', 'Error: Failed to get response');
            console.error('Copilot message failed:', error);
        }
    }
    
    async generateScript() {
        const descriptionInput = document.getElementById('script-description');
        const description = descriptionInput.value.trim();
        
        if (!description) {
            this.showNotification('Please enter a script description', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/sysadmin/generate-script', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    description: description,
                    auto_execute: false 
                })
            });
            
            const result = await response.json();
            
            if (result.script_generated && this.scriptEditor) {
                this.scriptEditor.setValue(result.script_info.script_content);
                this.scriptEditor.getModel().setLanguage(result.script_info.script_type);
                this.showNotification('Script generated successfully!', 'success');
                
                // Store task ID for execution
                this.currentTaskId = result.task_id;
            } else {
                this.showNotification(result.error || 'Failed to generate script', 'error');
            }
            
        } catch (error) {
            console.error('Script generation failed:', error);
            this.showNotification('Script generation failed', 'error');
        }
    }
    
    async executeGeneratedScript() {
        if (!this.currentTaskId) {
            this.showNotification('No script to execute', 'warning');
            return;
        }
        
        const confirmation = confirm('Are you sure you want to execute this script?');
        if (!confirmation) return;
        
        try {
            const response = await fetch(`/api/sysadmin/execute-task/${this.currentTaskId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Script executed successfully!', 'success');
                this.showExecutionResult(result);
            } else {
                this.showNotification('Script execution failed', 'error');
                this.showExecutionResult(result);
            }
            
            // Refresh task history
            await this.loadTaskHistory();
            
        } catch (error) {
            console.error('Script execution failed:', error);
            this.showNotification('Script execution failed', 'error');
        }
    }
    
    /**
     * Plugin Management Functions
     */
    async togglePlugin(pluginId, currentState) {
        const action = currentState ? 'disable' : 'enable';
        
        try {
            const response = await fetch(`/api/plugins/${pluginId}/${action}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Plugin ${action}d successfully!`, 'success');
                await this.loadPlugins();
            } else {
                this.showNotification(`Failed to ${action} plugin`, 'error');
            }
            
        } catch (error) {
            console.error(`Plugin ${action} failed:`, error);
            this.showNotification(`Plugin ${action} failed`, 'error');
        }
    }
    
    async installPlugin() {
        const pluginPath = prompt('Enter plugin path or URL:');
        if (!pluginPath) return;
        
        try {
            const response = await fetch('/api/plugins/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plugin_path: pluginPath })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Plugin installed successfully!', 'success');
                await this.loadPlugins();
            } else {
                this.showNotification(result.error || 'Plugin installation failed', 'error');
            }
            
        } catch (error) {
            console.error('Plugin installation failed:', error);
            this.showNotification('Plugin installation failed', 'error');
        }
    }
    
    async createPlugin() {
        const pluginName = prompt('Enter plugin name:');
        if (!pluginName) return;
        
        const pluginType = prompt('Enter plugin type (utility, monitoring, security):', 'utility');
        
        try {
            const response = await fetch('/api/plugins/create-template', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: pluginName,
                    type: pluginType || 'utility'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Plugin template created successfully!', 'success');
                console.log('Plugin template path:', result.plugin_path);
            } else {
                this.showNotification(result.error || 'Plugin template creation failed', 'error');
            }
            
        } catch (error) {
            console.error('Plugin template creation failed:', error);
            this.showNotification('Plugin template creation failed', 'error');
        }
    }
    
    /**
     * Network Functions
     */
    async startNetworkScan(scanType = 'quick') {
        const resultsDiv = document.getElementById('scan-results');
        resultsDiv.innerHTML = this.createLoadingIndicator(`Starting ${scanType} scan...`);
        
        try {
            const response = await fetch(`/api/network/scan?type=${scanType}`);
            const result = await response.json();
            
            if (result.error) {
                resultsDiv.innerHTML = `<div class="text-danger">Error: ${result.error}</div>`;
            } else {
                this.displayScanResults(result);
                this.updateNetworkStats(result);
            }
            
        } catch (error) {
            console.error('Network scan failed:', error);
            resultsDiv.innerHTML = '<div class="text-danger">Network scan failed</div>';
        }
    }
    
    /**
     * AI Chat Functions
     */
    async sendAIMessage() {
        const messageInput = document.getElementById('ai-chat-input');
        const modelSelect = document.getElementById('ai-model-select');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        const chatArea = document.getElementById('ai-chat-area');
        const selectedModel = modelSelect.value;
        
        // Add user message
        this.addAIChatMessage(chatArea, 'user', message);
        messageInput.value = '';
        
        // Add loading indicator
        const loadingId = this.addAIChatMessage(chatArea, 'ai', this.createLoadingIndicator('Thinking...'));
        
        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    model: selectedModel,
                    context: this.getAIContext()
                })
            });
            
            const result = await response.json();
            
            // Remove loading message
            this.removeAIChatMessage(loadingId);
            
            if (result.response) {
                this.addAIChatMessage(chatArea, 'ai', result.response);
            } else {
                this.addAIChatMessage(chatArea, 'ai', result.error || 'Sorry, I could not process your request.');
            }
            
        } catch (error) {
            this.removeAIChatMessage(loadingId);
            this.addAIChatMessage(chatArea, 'ai', 'Error: Failed to get AI response');
            console.error('AI chat failed:', error);
        }
    }
    
    /**
     * Utility Functions
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    createLoadingIndicator(text = 'Loading...') {
        return `<div class="loading-container">
            <div class="loading"></div>
            <span>${text}</span>
        </div>`;
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 15px 20px;
            backdrop-filter: blur(20px);
            box-shadow: var(--shadow-medium);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            max-width: 400px;
        `;
        
        // Add type-specific styling
        const colors = {
            success: '#00e676',
            error: '#ff5252',
            warning: '#ffab00',
            info: '#00a8ff'
        };
        
        notification.style.borderColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    formatAIResponse(response) {
        // Basic markdown-like formatting
        return response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    addChatMessage(container, sender, message) {
        const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${sender === 'user' ? '👤 You' : '🤖 Copilot'}</strong>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">${message}</div>
        `;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
        
        return messageId;
    }
    
    removeChatMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
    
    // Add more utility methods...
    
    updateStatusIndicators(status) {
        const aiCount = document.getElementById('ai-count');
        const pluginCount = document.getElementById('plugin-count');
        
        if (aiCount) {
            aiCount.textContent = `${status.components?.ai_models_count || 0} Models`;
        }
        
        if (pluginCount) {
            pluginCount.textContent = `${status.components?.plugins_count || 0} Plugins`;
        }
    }
    
    updateHealthDisplay(health) {
        const healthScore = document.getElementById('health-score');
        const sidebarHealthScore = document.getElementById('sidebar-health-score');
        const healthStatus = document.getElementById('health-status');
        const sidebarHealthStatus = document.getElementById('sidebar-health-status');
        
        if (healthScore) {
            healthScore.textContent = health.overall_score || '--';
            healthScore.className = `health-score health-${health.health_status || 'unknown'}`;
        }
        
        if (sidebarHealthScore) {
            sidebarHealthScore.textContent = health.overall_score || '--';
            sidebarHealthScore.className = `health-score health-${health.health_status || 'unknown'}`;
        }
        
        if (healthStatus) {
            healthStatus.textContent = this.capitalize(health.health_status || 'Unknown');
        }
        
        if (sidebarHealthStatus) {
            sidebarHealthStatus.textContent = this.capitalize(health.health_status || 'Unknown');
        }
        
        // Update individual metrics
        if (health.metrics) {
            this.updateElement('cpu-usage', Math.round(health.metrics.cpu_percent || 0));
            this.updateElement('memory-usage', Math.round(health.metrics.memory_percent || 0));
            
            // Calculate average disk usage
            if (health.metrics.disk_usage) {
                const diskValues = Object.values(health.metrics.disk_usage);
                const avgDisk = diskValues.reduce((a, b) => a + b, 0) / diskValues.length;
                this.updateElement('disk-usage', Math.round(avgDisk));
            }
        }
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    // More methods would be implemented here...
}

// Global instance
let ultimateSuite;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ultimateSuite = new UltimateSuiteV9();
});

// Global functions for HTML onclick events
function showSection(sectionId) {
    if (ultimateSuite) {
        ultimateSuite.showSection(sectionId);
    }
}

function sendCopilotMessage() {
    if (ultimateSuite) {
        ultimateSuite.sendCopilotMessage();
    }
}

function generateScript() {
    if (ultimateSuite) {
        ultimateSuite.generateScript();
    }
}

function executeGeneratedScript() {
    if (ultimateSuite) {
        ultimateSuite.executeGeneratedScript();
    }
}

function togglePlugin(pluginId, currentState) {
    if (ultimateSuite) {
        ultimateSuite.togglePlugin(pluginId, currentState);
    }
}

function installPlugin() {
    if (ultimateSuite) {
        ultimateSuite.installPlugin();
    }
}

function createPlugin() {
    if (ultimateSuite) {
        ultimateSuite.createPlugin();
    }
}

function startNetworkScan(scanType) {
    if (ultimateSuite) {
        ultimateSuite.startNetworkScan(scanType);
    }
}

function sendAIMessage() {
    if (ultimateSuite) {
        ultimateSuite.sendAIMessage();
    }
}

function clearChat() {
    const chatArea = document.getElementById('ai-chat-area');
    if (chatArea) {
        chatArea.innerHTML = '<div class="ai-message">AI Assistant is ready! Ask me about your system, network, or any technical questions.</div>';
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UltimateSuiteV9;
}

console.log('🎉 Ultimate Suite v9.0 JavaScript - Loaded!');
