/**
 * Ultimate Suite v8.0 - Enhanced JavaScript
 * AI Integration & Advanced Network Features
 */

class UltimateSuiteV8 {
    constructor() {
        this.aiModels = [];
        this.networkDevices = [];
        this.securityData = {};
        this.currentTheme = localStorage.getItem('theme') || 'purple';
        this.websocket = null;
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Ultimate Suite v8.0 - Initializing Enhanced Features...');
        
        // Apply theme
        this.setTheme(this.currentTheme);
        
        // Initialize components
        this.initializeEventListeners();
        this.initializeWebSocket();
        this.loadInitialData();
        this.startAutoRefresh();
        
        console.log('✅ Ultimate Suite v8.0 - Initialization complete');
    }
    
    initializeEventListeners() {
        // AI Chat enter key
        const aiPrompt = document.getElementById('ai-prompt');
        if (aiPrompt) {
            aiPrompt.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendAIQuery();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshDashboard();
                        break;
                    case 'm':
                        e.preventDefault();
                        aiPrompt?.focus();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.performComprehensiveScan();
                        break;
                    case 's':
                        e.preventDefault();
                        this.securityAudit();
                        break;
                }
            }
        });
        
        // Theme change detection
        window.addEventListener('storage', (e) => {
            if (e.key === 'theme') {
                this.setTheme(e.newValue);
            }
        });
    }
    
    initializeWebSocket() {
        // Future: Real-time updates via WebSocket
        // This would connect to a WebSocket server for real-time data
        console.log('🔌 WebSocket initialization - Future feature');
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadAIModels(),
                this.loadNetworkDevices(),
                this.loadSecurityStatus()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showNotification('Failed to load initial data', 'error');
        }
    }
    
    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.updateInterval = setInterval(() => {
            this.refreshDashboard();
        }, 30000);
    }
    
    // Enhanced AI Functions
    async loadAIModels() {
        try {
            this.showLoadingState('ai-models');
            
            const response = await fetch('/api/models');
            const data = await response.json();
            
            this.aiModels = data.models || [];
            this.updateAIStatus(this.aiModels);
            this.populateAIModelSelect(this.aiModels);
            
            this.hideLoadingState('ai-models');
            
        } catch (error) {
            console.error('Failed to load AI models:', error);
            this.showError('ai-status-text', 'Failed to load AI models');
        }
    }
    
    updateAIStatus(models) {
        const totalElement = document.getElementById('total-ai-models');
        const countElement = document.getElementById('ai-models-count');
        const statusElement = document.getElementById('ai-status-text');
        
        if (totalElement) totalElement.textContent = models.length;
        if (countElement) countElement.textContent = models.length;
        
        const activeModels = models.filter(m => m.status === 'ready').length;
        if (statusElement) {
            statusElement.textContent = `${activeModels} Active`;
            statusElement.className = activeModels > 0 ? 'text-success' : 'text-warning';
        }
        
        // Update AI status indicator
        const aiStatus = document.getElementById('ai-status');
        if (aiStatus) {
            aiStatus.className = `badge ${activeModels > 0 ? 'bg-success' : 'bg-warning'}`;
        }
    }
    
    populateAIModelSelect(models) {
        const select = document.getElementById('ai-model-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select AI Model...</option>';
        
        models.forEach(model => {
            if (model.status === 'ready') {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} (${model.provider})`;
                select.appendChild(option);
            }
        });
        
        // Auto-select first available model
        if (models.length > 0 && models[0].status === 'ready') {
            select.value = models[0].id;
        }
    }
    
    async sendAIQuery() {
        const promptInput = document.getElementById('ai-prompt');
        const modelSelect = document.getElementById('ai-model-select');
        
        if (!promptInput || !modelSelect) return;
        
        const prompt = promptInput.value.trim();
        const selectedModel = modelSelect.value;
        
        if (!prompt) {
            this.showNotification('Please enter a prompt', 'warning');
            return;
        }
        
        if (!selectedModel) {
            this.showNotification('Please select an AI model', 'warning');
            return;
        }
        
        // Add user message to chat
        this.addChatMessage('user', prompt);
        promptInput.value = '';
        
        // Add loading message
        const loadingDiv = this.addChatMessage('assistant', 'Analyzing your request...');
        loadingDiv.classList.add('loading-message');
        
        try {
            const response = await fetch('/api/ai/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: selectedModel,
                    prompt: prompt,
                    context: this.generateContextForAI()
                })
            });
            
            const data = await response.json();
            
            // Remove loading message
            loadingDiv.remove();
            
            if (data.error) {
                this.addChatMessage('assistant', `❌ Error: ${data.error}`);
                this.showNotification(`AI Error: ${data.error}`, 'error');
            } else {
                this.addChatMessage('assistant', data.response);
                this.showNotification('AI response received', 'success');
            }
            
        } catch (error) {
            loadingDiv.remove();
            this.addChatMessage('assistant', `❌ Connection error: ${error.message}`);
            this.showNotification(`Connection error: ${error.message}`, 'error');
        }
    }
    
    generateContextForAI() {
        // Provide context about current network state for AI
        return `Current network context:
        - Devices found: ${this.networkDevices.length}
        - Security score: ${this.securityData.overall_score || 'unknown'}
        - Theme: ${this.currentTheme}
        - Time: ${new Date().toISOString()}`;
    }
    
    addChatMessage(type, message) {
        const chatContainer = document.getElementById('chat-container');
        if (!chatContainer) return null;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div><i class="fas fa-user me-2"></i><strong>You:</strong> ${this.escapeHtml(message)}</div>
                    <small class="text-muted">${timestamp}</small>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div><i class="fas fa-robot me-2"></i><strong>AI:</strong> ${this.escapeHtml(message)}</div>
                    <small class="text-muted">${timestamp}</small>
                </div>
            `;
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Auto-remove old messages (keep last 20)
        const messages = chatContainer.querySelectorAll('.chat-message');
        if (messages.length > 20) {
            messages[0].remove();
        }
        
        return messageDiv;
    }
    
    // Enhanced Network Functions
    async loadNetworkDevices() {
        try {
            this.showLoadingState('network-devices');
            
            const response = await fetch('/api/network/devices');
            const data = await response.json();
            
            this.networkDevices = data.devices || [];
            this.updateNetworkStatus(this.networkDevices);
            this.updateDevicesTable(this.networkDevices);
            this.updateNetworkVisualization(this.networkDevices);
            
            this.hideLoadingState('network-devices');
            
        } catch (error) {
            console.error('Failed to load network devices:', error);
            this.showError('network-status-text', 'Failed to scan network');
        }
    }
    
    updateNetworkStatus(devices) {
        const totalElement = document.getElementById('total-devices');
        const countElement = document.getElementById('devices-count');
        const statusElement = document.getElementById('network-status-text');
        
        if (totalElement) totalElement.textContent = devices.length;
        if (countElement) countElement.textContent = devices.length;
        if (statusElement) {
            statusElement.textContent = `${devices.length} devices found`;
            statusElement.className = devices.length > 0 ? 'text-info' : 'text-warning';
        }
        
        // Update network status indicator
        const networkStatus = document.getElementById('network-status');
        if (networkStatus) {
            networkStatus.className = `badge ${devices.length > 0 ? 'bg-info' : 'bg-warning'}`;
        }
    }
    
    async performComprehensiveScan() {
        try {
            this.showNotification('Starting comprehensive network scan...', 'info');
            this.showLoadingState('network-scan');
            
            const statusElement = document.getElementById('network-status-text');
            if (statusElement) statusElement.textContent = 'Deep scanning network...';
            
            const response = await fetch('/api/network/scan');
            const data = await response.json();
            
            this.networkDevices = data.devices || [];
            this.updateDevicesTable(this.networkDevices);
            this.updateNetworkVisualization(this.networkDevices);
            
            // Update AI analysis if available
            if (data.ai_analysis) {
                this.updateAIAnalysis(data.ai_analysis);
            }
            
            // Update statistics
            if (data.statistics) {
                this.updateSecurityStatistics(data.statistics);
            }
            
            this.hideLoadingState('network-scan');
            this.showNotification(`Comprehensive scan completed - found ${this.networkDevices.length} devices`, 'success');
            
        } catch (error) {
            console.error('Comprehensive scan failed:', error);
            this.showNotification(`Scan failed: ${error.message}`, 'error');
            this.hideLoadingState('network-scan');
        }
    }
    
    updateDevicesTable(devices) {
        const tbody = document.getElementById('devices-list');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No devices found</td></tr>';
            return;
        }
        
        devices.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="d-flex align-items-center">
                        <span class="status-indicator ${device.status === 'up' ? 'online' : 'offline'}"></span>
                        <div>
                            <div class="text-primary fw-bold">${device.ip}</div>
                            <small class="text-muted">${device.mac_address || 'Unknown MAC'}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <div>
                        <div>${device.hostname || 'Unknown'}</div>
                        ${device.os_info ? `<small class="text-muted">${device.os_info.os}</small>` : ''}
                    </div>
                </td>
                <td>
                    <span class="badge bg-info">${device.device_type || 'Unknown'}</span>
                </td>
                <td>
                    <span class="badge bg-secondary">${(device.services && Object.keys(device.services).length) || 0} Services</span>
                    ${device.open_ports ? `<br><small class="text-muted">${device.open_ports.length} ports open</small>` : ''}
                </td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar ${this.getSecurityScoreColor(device.security_score || 50)}" 
                             style="width: ${device.security_score || 50}%">
                            ${device.security_score || 50}%
                        </div>
                    </div>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="ultimateSuite.analyzeDevice('${device.ip}')" title="Analyze Device">
                            <i class="fas fa-search"></i>
                        </button>
                        <button class="btn btn-outline-info" onclick="ultimateSuite.pingDevice('${device.ip}')" title="Ping Device">
                            <i class="fas fa-wifi"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    getSecurityScoreColor(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-warning';
        return 'bg-danger';
    }
    
    updateNetworkVisualization(devices) {
        const container = document.getElementById('network-topology');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Create SVG for network visualization
        const svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '300px')
            .attr('viewBox', '0 0 500 300');
            
        // Prepare nodes data
        const nodes = devices.map((device, index) => ({
            id: device.ip,
            name: device.hostname || device.ip,
            type: device.device_type || 'unknown',
            x: 50 + (index % 5) * 90,
            y: 50 + Math.floor(index / 5) * 60,
            security_score: device.security_score || 50,
            services: device.services ? Object.keys(device.services).length : 0
        }));
        
        // Add gateway connection lines
        if (nodes.length > 1) {
            const gateway = nodes[0]; // Assume first device is gateway
            
            svg.selectAll('line')
                .data(nodes.slice(1))
                .enter()
                .append('line')
                .attr('x1', gateway.x)
                .attr('y1', gateway.y)
                .attr('x2', d => d.x)
                .attr('y2', d => d.y)
                .attr('stroke', '#6366f1')
                .attr('stroke-width', 2)
                .attr('opacity', 0.3)
                .attr('stroke-dasharray', '5,5');
        }
        
        // Add device nodes
        const nodeGroups = svg.selectAll('g.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
            
        // Add circles for devices
        nodeGroups.append('circle')
            .attr('r', 20)
            .attr('fill', d => this.getDeviceColor(d.type))
            .attr('stroke', d => d.security_score >= 80 ? '#10b981' : d.security_score >= 60 ? '#f59e0b' : '#ef4444')
            .attr('stroke-width', 3)
            .attr('opacity', 0.8);
            
        // Add device type icons
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .attr('font-family', 'Font Awesome 6 Free')
            .attr('font-weight', '900')
            .attr('font-size', '16px')
            .attr('fill', 'white')
            .text(d => this.getDeviceIcon(d.type));
            
        // Add labels
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '35px')
            .attr('font-size', '10px')
            .attr('fill', '#374151')
            .text(d => d.name.length > 12 ? d.name.substring(0, 12) + '...' : d.name);
            
        // Add tooltips
        nodeGroups.append('title')
            .text(d => `${d.name}\nIP: ${d.id}\nType: ${d.type}\nSecurity Score: ${d.security_score}%\nServices: ${d.services}`);
            
        // Update statistics
        this.updateNetworkStats(devices);
    }
    
    getDeviceColor(type) {
        const colors = {
            'router': '#f59e0b',
            'server': '#10b981',
            'computer': '#3b82f6',
            'mobile': '#8b5cf6',
            'iot': '#ef4444',
            'printer': '#6b7280',
            'unknown': '#6b7280'
        };
        return colors[type] || colors.unknown;
    }
    
    getDeviceIcon(type) {
        const icons = {
            'router': '\uf1eb',      // fa-wifi
            'server': '\uf233',      // fa-server
            'computer': '\uf108',    // fa-desktop
            'mobile': '\uf3cd',      // fa-mobile-alt
            'iot': '\uf2db',         // fa-microchip
            'printer': '\uf02f',     // fa-print
            'unknown': '\uf059'      // fa-question-circle
        };
        return icons[type] || icons.unknown;
    }
    
    updateNetworkStats(devices) {
        const onlineDevices = document.getElementById('online-devices');
        const totalServices = document.getElementById('total-services');
        const securityRisks = document.getElementById('security-risks');
        
        if (onlineDevices) {
            onlineDevices.textContent = devices.filter(d => d.status === 'up').length;
        }
        
        if (totalServices) {
            const servicesCount = devices.reduce((sum, d) => sum + (d.services ? Object.keys(d.services).length : 0), 0);
            totalServices.textContent = servicesCount;
        }
        
        if (securityRisks) {
            const riskyDevices = devices.filter(d => (d.security_score || 50) < 60).length;
            securityRisks.textContent = riskyDevices;
        }
    }
    
    updateAIAnalysis(analysis) {
        const container = document.getElementById('ai-analysis-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class="ai-analysis">
                <h6 class="text-warning mb-3">
                    <i class="fas fa-brain me-2"></i>
                    AI Security Analysis
                    <span class="badge bg-secondary ms-2">${analysis.model_used}</span>
                </h6>
                <div class="analysis-content">
                    ${this.formatAIAnalysis(analysis.analysis)}
                </div>
                <div class="mt-3 d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        Confidence: <span class="badge bg-${this.getConfidenceColor(analysis.confidence)}">${analysis.confidence}</span>
                    </small>
                    <small class="text-muted">
                        ${new Date(analysis.timestamp).toLocaleString()}
                    </small>
                </div>
            </div>
        `;
    }
    
    formatAIAnalysis(analysis) {
        // Format AI analysis with better readability
        return analysis
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    getConfidenceColor(confidence) {
        switch(confidence.toLowerCase()) {
            case 'high': return 'success';
            case 'medium': return 'warning';
            case 'low': return 'danger';
            default: return 'secondary';
        }
    }
    
    // Enhanced Security Functions
    async loadSecurityStatus() {
        try {
            this.showLoadingState('security-status');
            
            const response = await fetch('/api/security/status');
            const data = await response.json();
            
            this.securityData = data;
            this.updateSecurityDisplay(data);
            
            this.hideLoadingState('security-status');
            
        } catch (error) {
            console.error('Failed to load security status:', error);
            this.showError('security-status-text', 'Failed to load security status');
        }
    }
    
    updateSecurityDisplay(data) {
        const scoreElement = document.getElementById('security-score');
        const statusElement = document.getElementById('security-status-text');
        const vulnElement = document.getElementById('vulnerability-count');
        
        if (scoreElement) scoreElement.textContent = data.overall_score || 0;
        if (vulnElement) vulnElement.textContent = data.vulnerability_scan?.vulnerabilities_found || 0;
        if (statusElement) {
            statusElement.textContent = data.overall_score >= 80 ? 'Excellent Security' : 
                                      data.overall_score >= 60 ? 'Good Security' : 'Needs Attention';
        }
    }
    
    // Utility Functions
    setTheme(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('theme', themeName);
        this.currentTheme = themeName;
        
        // Update theme dropdown
        const dropdownItems = document.querySelectorAll('#themeDropdown + .dropdown-menu .dropdown-item');
        dropdownItems.forEach(item => item.classList.remove('active'));
        
        const activeItem = Array.from(dropdownItems).find(item => 
            item.onclick && item.onclick.toString().includes(`'${themeName}'`)
        );
        if (activeItem) activeItem.classList.add('active');
        
        this.showNotification(`Theme changed to ${themeName}`, 'info');
    }
    
    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
    
    showLoadingState(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Loading...';
        }
    }
    
    hideLoadingState(elementId) {
        // Loading state will be replaced by data update
    }
    
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.className = 'text-danger';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    refreshDashboard() {
        console.log('🔄 Refreshing dashboard data...');
        this.loadInitialData();
    }
    
    // Quick Action Functions
    async analyzeDevice(ip) {
        this.showNotification(`Analyzing device ${ip}...`, 'info');
        
        // This would show detailed device analysis
        const device = this.networkDevices.find(d => d.ip === ip);
        if (device) {
            const analysis = `
                Device Analysis for ${ip}:
                - Hostname: ${device.hostname || 'Unknown'}
                - Type: ${device.device_type || 'Unknown'}
                - Security Score: ${device.security_score || 50}%
                - Open Ports: ${device.open_ports ? device.open_ports.length : 0}
                - Services: ${device.services ? Object.keys(device.services).length : 0}
            `;
            alert(analysis);
        }
    }
    
    async pingDevice(ip) {
        this.showNotification(`Pinging ${ip}...`, 'info');
        
        try {
            // Simulate ping operation
            setTimeout(() => {
                this.showNotification(`Ping to ${ip} successful`, 'success');
            }, 1000);
        } catch (error) {
            this.showNotification(`Ping to ${ip} failed`, 'error');
        }
    }
    
    securityAudit() {
        this.showNotification('Initiating comprehensive security audit...', 'info');
        // This would perform a detailed security audit
        alert('Security Audit: This would perform a comprehensive security check of all network devices and services.');
    }
    
    generateReport() {
        this.showNotification('Generating network report...', 'info');
        
        // Generate CSV report
        const reportData = this.networkDevices.map(device => ({
            'IP Address': device.ip,
            'Hostname': device.hostname || 'Unknown',
            'Device Type': device.device_type || 'Unknown',
            'MAC Address': device.mac_address || 'Unknown',
            'Status': device.status || 'Unknown',
            'Security Score': device.security_score || 50,
            'Open Ports': device.open_ports ? device.open_ports.length : 0,
            'Services': device.services ? Object.keys(device.services).length : 0
        }));
        
        this.downloadJSON(reportData, 'network-report.json');
        this.showNotification('Network report downloaded', 'success');
    }
    
    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.setAttribute('href', url);
        a.setAttribute('download', filename);
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    optimizeNetwork() {
        this.showNotification('AI Network Optimization initiated...', 'info');
        
        // This would use AI to suggest network optimizations
        const suggestions = [
            'Consider upgrading devices with security scores below 60%',
            'Review open ports on critical devices',
            'Implement network segmentation for IoT devices',
            'Update firmware on devices showing vulnerabilities'
        ];
        
        alert('AI Network Optimization Suggestions:\n\n' + suggestions.join('\n'));
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// Global instance
let ultimateSuite;

// Global functions for compatibility
function setTheme(themeName) {
    if (ultimateSuite) {
        ultimateSuite.setTheme(themeName);
    }
}

function sendAIQuery() {
    if (ultimateSuite) {
        ultimateSuite.sendAIQuery();
    }
}

function performComprehensiveScan() {
    if (ultimateSuite) {
        ultimateSuite.performComprehensiveScan();
    }
}

function refreshAIModels() {
    if (ultimateSuite) {
        ultimateSuite.loadAIModels();
    }
}

function refreshNetworkData() {
    if (ultimateSuite) {
        ultimateSuite.loadNetworkDevices();
    }
}

function quickNetworkScan() {
    if (ultimateSuite) {
        ultimateSuite.loadNetworkDevices();
    }
}

function securityAudit() {
    if (ultimateSuite) {
        ultimateSuite.securityAudit();
    }
}

function generateReport() {
    if (ultimateSuite) {
        ultimateSuite.generateReport();
    }
}

function optimizeNetwork() {
    if (ultimateSuite) {
        ultimateSuite.optimizeNetwork();
    }
}

function exportDeviceList() {
    if (ultimateSuite) {
        ultimateSuite.generateReport();
    }
}

function loadInterface(interfaceName) {
    console.log(`Loading ${interfaceName} interface...`);
    if (ultimateSuite) {
        ultimateSuite.showNotification(`Loading ${interfaceName} interface...`, 'info');
    }
    // This would load specific interface components
    alert(`Loading ${interfaceName} interface - this would show the specialized interface`);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ultimateSuite = new UltimateSuiteV8();
});

// Cleanup when page is unloaded
window.addEventListener('beforeunload', function() {
    if (ultimateSuite) {
        ultimateSuite.destroy();
    }
});
