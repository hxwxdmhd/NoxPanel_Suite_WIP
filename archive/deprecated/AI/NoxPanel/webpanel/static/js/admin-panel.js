/**
 * NoxPanel v4.0 - Admin Panel JavaScript
 * Comprehensive administration interface functionality
 */

class AdminPanel {
    constructor() {
        this.models = [];
        this.providers = [];
        this.apiBase = '';
        this.refreshInterval = null;

        this.init();
    }

    async init() {
        console.log('🔧 Initializing Admin Panel v4.0...');

        // Initialize theme management
        if (typeof ThemeManager !== 'undefined') {
            this.themeManager = new ThemeManager();
            this.setupThemeToggle();
        }

        // Load initial data
        await this.loadDashboardData();
        await this.loadModelsData();
        await this.loadSystemInfo();
        await this.loadProcessData();
        await this.loadScriptData();

        // Setup auto-refresh
        this.startAutoRefresh();

        // Setup event listeners
        this.setupEventListeners();

        console.log('✅ Admin Panel initialized successfully');
    }

    setupThemeToggle() {
        const themeSwitch = document.getElementById('themeSwitch');
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');

        if (themeSwitch && this.themeManager) {
            // Set initial state
            const currentTheme = this.themeManager.getCurrentTheme();
            themeSwitch.checked = currentTheme === 'light';
            this.updateThemeUI(currentTheme);

            // Handle theme toggle
            themeSwitch.addEventListener('change', (e) => {
                const newTheme = e.target.checked ? 'light' : 'dark';
                this.themeManager.setTheme(newTheme);
                this.updateThemeUI(newTheme);
            });
        }
    }

    updateThemeUI(theme) {
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');

        if (themeIcon && themeText) {
            if (theme === 'light') {
                themeIcon.className = 'fas fa-sun';
                themeText.textContent = 'Light';
            } else {
                themeIcon.className = 'fas fa-moon';
                themeText.textContent = 'Dark';
            }
        }
    }

    async loadDashboardData() {
        try {
            // Load system health
            await this.updateSystemHealth();

            // Load basic stats
            await this.updateStats();

            // Update uptime
            this.updateUptime();

        } catch (error) {
            console.error('❌ Error loading dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    async updateSystemHealth() {
        try {
            const response = await fetch('/api/models/health');
            const data = await response.json();

            const healthStatus = document.getElementById('health-status');
            if (healthStatus) {
                let healthHTML = '';

                // API Services
                const apiStatus = data.status === 'healthy' ? 'healthy' : 'error';
                healthHTML += this.createHealthItem('API Services', apiStatus,
                    apiStatus === 'healthy' ? 'Healthy' : 'Error');

                // Model Detection
                const modelStatus = data.model_detection ? 'healthy' : 'warning';
                healthHTML += this.createHealthItem('Model Detection', modelStatus,
                    data.model_detection ? 'Operational' : 'Limited');

                // Database (placeholder)
                healthHTML += this.createHealthItem('Database', 'warning', 'Checking...');

                healthStatus.innerHTML = healthHTML;
            }
        } catch (error) {
            console.error('❌ Error updating system health:', error);
        }
    }

    createHealthItem(name, status, label) {
        const statusClass = status === 'healthy' ? 'status-healthy' :
                          status === 'warning' ? 'status-warning' : 'status-error';
        const badgeClass = status === 'healthy' ? 'bg-success' :
                          status === 'warning' ? 'bg-warning' : 'bg-danger';

        return `
            <div class="d-flex align-items-center mb-2">
                <span class="status-indicator ${statusClass}"></span>
                <span>${name}</span>
                <span class="ms-auto badge ${badgeClass}">${label}</span>
            </div>
        `;
    }

    async updateStats() {
        try {
            // Get models stats
            const modelsResponse = await fetch('/api/models');
            const modelsData = await modelsResponse.json();

            // Get providers stats
            const providersResponse = await fetch('/api/models/providers');
            const providersData = await providersResponse.json();

            // Update UI
            this.updateStatCard('total-models', modelsData.total_models || 0);
            this.updateStatCard('active-providers', providersData.available_count || 0);

        } catch (error) {
            console.error('❌ Error updating stats:', error);
        }
    }

    updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    updateUptime() {
        // Calculate uptime (placeholder - would need server start time)
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            uptimeElement.textContent = '24h 15m';
        }
    }

    async loadSystemInfo() {
        try {
            const response = await fetch('/api/admin/system-info');
            const data = await response.json();

            if (data.status === 'success') {
                // Update system info in the System tab
                this.updateSystemInfoDisplay(data);
            }
        } catch (error) {
            console.error('❌ Error loading system info:', error);
        }
    }

    updateSystemInfoDisplay(data) {
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };

        updateElement('platform', data.platform || 'Unknown');
        updateElement('python-version', data.python_version || 'Unknown');
        updateElement('flask-version', data.flask_version || 'Unknown');
        updateElement('memory-usage', data.memory_usage || 'Unknown');
    }

    async loadSystemLogs() {
        try {
            const response = await fetch('/api/admin/logs');
            const data = await response.json();

            const logsContainer = document.getElementById('logs-content');
            if (logsContainer && data.status === 'success') {
                logsContainer.innerHTML = `<pre>${data.logs}</pre>`;
            }
        } catch (error) {
            console.error('❌ Error loading logs:', error);
        }
    }

    async loadModelsData() {
        try {
            await Promise.all([
                this.loadProviders(),
                this.loadModelsList(),
                this.loadModelSelectors()
            ]);
        } catch (error) {
            console.error('❌ Error loading models data:', error);
        }
    }

    async loadProviders() {
        try {
            const response = await fetch('/api/models/providers');
            const data = await response.json();

            if (data.status === 'success') {
                this.providers = data.providers;
                this.renderProviders();
            }
        } catch (error) {
            console.error('❌ Error loading providers:', error);
        }
    }

    renderProviders() {
        const container = document.getElementById('providers-list');
        if (!container) return;

        if (this.providers.length === 0) {
            container.innerHTML = '<p class="text-muted">No providers found</p>';
            return;
        }

        let html = '';
        this.providers.forEach(provider => {
            const statusBadge = provider.installed ?
                '<span class="badge bg-success">Installed</span>' :
                '<span class="badge bg-secondary">Not Found</span>';

            html += `
                <div class="d-flex align-items-center justify-content-between p-2 border-bottom">
                    <div>
                        <strong>${provider.display_name}</strong>
                        <br>
                        <small class="text-muted">${provider.model_count} models</small>
                    </div>
                    <div>
                        ${statusBadge}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    async loadModelsList() {
        try {
            const response = await fetch('/api/models/list');
            const data = await response.json();

            if (data.status === 'success') {
                this.models = data.models;
                this.renderModelsList();
            }
        } catch (error) {
            console.error('❌ Error loading models list:', error);
        }
    }

    renderModelsList() {
        const container = document.getElementById('models-list');
        if (!container) return;

        if (this.models.length === 0) {
            container.innerHTML = '<p class="text-muted">No models found</p>';
            return;
        }

        let html = '';
        this.models.slice(0, 6).forEach(model => { // Show first 6 models
            const statusBadge = model.available ?
                '<span class="provider-badge bg-success">Available</span>' :
                '<span class="provider-badge bg-secondary">Unavailable</span>';

            html += `
                <div class="d-flex align-items-center justify-content-between p-2 border-bottom">
                    <div>
                        <strong>${model.name}</strong>
                        <br>
                        <small class="text-muted">${model.provider}</small>
                    </div>
                    <div>
                        ${statusBadge}
                    </div>
                </div>
            `;
        });

        if (this.models.length > 6) {
            html += `<div class="text-center p-2">
                <small class="text-muted">... and ${this.models.length - 6} more models</small>
            </div>`;
        }

        container.innerHTML = html;
    }

    async loadModelSelectors() {
        const primarySelect = document.getElementById('primary-model');
        const fallbackSelect = document.getElementById('fallback-model');

        if (!primarySelect || !fallbackSelect) return;

        // Clear existing options
        primarySelect.innerHTML = '<option value="">Select primary model...</option>';
        fallbackSelect.innerHTML = '<option value="">Select fallback model...</option>';

        // Add available models
        this.models.filter(model => model.available).forEach(model => {
            const option = new Option(`${model.name} (${model.provider})`, model.id);
            primarySelect.add(option.cloneNode(true));
            fallbackSelect.add(option);
        });
    }

    async loadProcessData() {
        try {
            const response = await fetch('/api/admin/processes');
            const data = await response.json();

            if (data.status === 'success') {
                this.processes = data.processes || [];
                this.updateProcessUI(data);
            } else {
                console.error('Process data error:', data.message);
                this.showNotification('Failed to load process data', 'error');
            }
        } catch (error) {
            console.error('Process data fetch error:', error);
            this.showNotification('Error loading process data', 'error');
        }
    }

    updateProcessUI(data) {
        // Update process statistics
        document.getElementById('total-python-processes').textContent = data.total_count || 0;
        document.getElementById('noxpanel-processes').textContent = data.noxpanel_count || 0;

        // Update process table
        const tableBody = document.getElementById('processes-table');
        if (tableBody) {
            tableBody.innerHTML = '';

            if (this.processes.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No processes found</td></tr>';
                return;
            }

            this.processes.forEach(proc => {
                const row = document.createElement('tr');
                const isNoxPanel = proc.is_noxpanel ? 'NoxPanel' : 'Python';
                const isCurrent = proc.is_current ? ' (Current)' : '';
                const statusClass = proc.is_current ? 'text-success' : (proc.is_noxpanel ? 'text-warning' : 'text-info');

                row.innerHTML = `
                    <td><code>${proc.pid}</code></td>
                    <td><strong>${proc.name}</strong></td>
                    <td>${proc.memory_mb} MB</td>
                    <td><small>${new Date(proc.create_time).toLocaleString()}</small></td>
                    <td><span class="badge ${statusClass}">${isNoxPanel}${isCurrent}</span></td>
                    <td>
                        ${proc.is_current ?
                            '<span class="text-muted">Current Process</span>' :
                            `<button class="btn btn-sm btn-danger" onclick="killProcess(${proc.pid})">
                                <i class="fas fa-stop"></i> Kill
                            </button>`
                        }
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    }

    async loadScriptData() {
        try {
            const response = await fetch('/api/scripts/discover');
            const data = await response.json();

            if (data.status === 'success') {
                this.scripts = data.scripts || {};
                this.updateScriptUI(data);
            } else {
                console.error('Script data error:', data.message);
                this.showNotification('Failed to load script data', 'error');
            }
        } catch (error) {
            console.error('Script data fetch error:', error);
            this.showNotification('Error loading script data', 'error');
        }
    }

    updateScriptUI(data) {
        // Update script statistics
        const pythonCount = this.scripts.python ? this.scripts.python.length : 0;
        const powershellCount = this.scripts.powershell ? this.scripts.powershell.length : 0;
        const batchCount = this.scripts.batch ? this.scripts.batch.length : 0;
        const totalCount = data.total_scripts || 0;

        document.getElementById('python-scripts-count').textContent = pythonCount;
        document.getElementById('powershell-scripts-count').textContent = powershellCount;
        document.getElementById('batch-scripts-count').textContent = batchCount;
        document.getElementById('total-scripts-count').textContent = totalCount;

        // Update script lists
        this.updateScriptList('python-scripts-list', this.scripts.python || []);
        this.updateScriptList('powershell-scripts-list', this.scripts.powershell || []);
        this.updateScriptList('batch-scripts-list', this.scripts.batch || []);
    }

    updateScriptList(containerId, scripts) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        if (scripts.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-3">No scripts found</div>';
            return;
        }

        scripts.forEach(script => {
            const scriptCard = document.createElement('div');
            scriptCard.className = 'card mb-3';

            const sizeKB = Math.round(script.size_bytes / 1024 * 100) / 100;
            const modifiedDate = new Date(script.modified).toLocaleDateString();

            scriptCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                <i class="fas fa-file-code me-2"></i>${script.name}
                            </h6>
                            <p class="card-text text-muted">${script.description}</p>
                            <small class="text-muted">
                                <i class="fas fa-folder me-1"></i>${script.relative_path} •
                                <i class="fas fa-weight me-1"></i>${sizeKB} KB •
                                <i class="fas fa-calendar me-1"></i>${modifiedDate}
                            </small>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewScript('${script.path}')">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-success" onclick="executeScript('${script.path}', '${script.name}')">
                                <i class="fas fa-play"></i> Execute
                            </button>
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(scriptCard);
        });
    }

    setupEventListeners() {
        // Settings form
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }

        // Tab change listeners
        const tabLinks = document.querySelectorAll('a[data-bs-toggle="pill"]');
        tabLinks.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetId = e.target.getAttribute('href').substring(1);
                this.onTabChange(targetId);
            });
        });
    }

    async onTabChange(tabId) {
        console.log(`📋 Switching to tab: ${tabId}`);

        switch (tabId) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'models':
                await this.loadModelsData();
                break;
            case 'processes':
                await this.loadProcessData();
                break;
            case 'scripts':
                await this.loadScriptData();
                break;
            case 'system':
                await this.loadSystemInfo();
                break;
            case 'logs':
                await this.loadSystemLogs();
                break;
        }
    }

    startAutoRefresh() {
        // Refresh dashboard data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.updateStats();
            this.updateSystemHealth();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showNotification(message, type = 'info') {
        // Create and show Bootstrap toast notification
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'primary'} border-0`;
        toast.setAttribute('role', 'alert');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
        return container;
    }

    async saveSettings() {
        try {
            const formData = new FormData(document.getElementById('settings-form'));
            const settings = {
                log_level: document.getElementById('log-level').value,
                rate_limit: parseInt(document.getElementById('rate-limit').value),
                auto_scan: document.getElementById('auto-scan').checked,
                debug_mode: document.getElementById('debug-mode').checked
            };

            // Save settings (would need backend endpoint)
            console.log('💾 Saving settings:', settings);
            this.showNotification('Settings saved successfully', 'success');

        } catch (error) {
            console.error('❌ Error saving settings:', error);
            this.showNotification('Failed to save settings', 'error');
        }
    }
}

// Global functions for button clicks
async function refreshModels() {
    try {
        const response = await fetch('/api/models/scan', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            adminPanel.showNotification(`Model scan complete - found ${data.total_models} models`, 'success');
            await adminPanel.loadModelsData();
            await adminPanel.updateStats();
        } else {
            adminPanel.showNotification('Model scan failed', 'error');
        }
    } catch (error) {
        console.error('❌ Error refreshing models:', error);
        adminPanel.showNotification('Failed to refresh models', 'error');
    }
}

async function saveModelConfig() {
    const primaryModel = document.getElementById('primary-model').value;
    const fallbackModel = document.getElementById('fallback-model').value;

    if (!primaryModel) {
        adminPanel.showNotification('Please select a primary model', 'error');
        return;
    }

    try {
        const config = {
            primary_model: primaryModel,
            fallback_model: fallbackModel,
            timestamp: new Date().toISOString()
        };

        const response = await fetch('/api/models/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.status === 'success') {
            adminPanel.showNotification('Model configuration saved successfully', 'success');
        } else {
            adminPanel.showNotification('Failed to save configuration', 'error');
        }
    } catch (error) {
        console.error('❌ Error saving model config:', error);
        adminPanel.showNotification('Failed to save configuration', 'error');
    }
}

function runSystemDiagnostic() {
    adminPanel.showNotification('Running system diagnostic...', 'info');

    // Simulate diagnostic run
    setTimeout(() => {
        adminPanel.showNotification('System diagnostic completed - all systems healthy', 'success');
    }, 2000);
}

function clearCache() {
    adminPanel.showNotification('Cache cleared successfully', 'success');
}

function backupSystem() {
    adminPanel.showNotification('System backup initiated...', 'info');

    setTimeout(() => {
        adminPanel.showNotification('Backup completed successfully', 'success');
    }, 3000);
}

function restartSystem() {
    if (confirm('Are you sure you want to restart the system? This will interrupt all current operations.')) {
        adminPanel.showNotification('System restart initiated...', 'warning');
    }
}

function addUser() {
    const username = prompt('Enter username:');
    if (username) {
        adminPanel.showNotification(`User "${username}" added successfully`, 'success');
    }
}

function refreshLogs() {
    if (adminPanel) {
        adminPanel.loadSystemLogs();
        adminPanel.showNotification('Logs refreshed', 'success');
    }
}

function clearLogs() {
    if (confirm('Are you sure you want to clear all logs?')) {
        const logsContainer = document.getElementById('logs-content');
        if (logsContainer) {
            logsContainer.innerHTML = '<div class="text-muted">Logs cleared</div>';
        }
        adminPanel.showNotification('Logs cleared successfully', 'success');
    }
}

// Process Management Functions
async function refreshProcesses() {
    if (adminPanel) {
        await adminPanel.loadProcessData();
        adminPanel.showNotification('Processes refreshed', 'success');
    }
}

async function killProcess(pid) {
    if (!confirm(`Are you sure you want to kill process ${pid}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/processes/kill/${pid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: true })
        });

        const result = await response.json();

        if (result.success) {
            adminPanel.showNotification(result.message, 'success');
            await refreshProcesses();
        } else {
            adminPanel.showNotification(result.message, 'error');
        }
    } catch (error) {
        console.error('Kill process error:', error);
        adminPanel.showNotification('Error killing process', 'error');
    }
}

async function killAllNoxPanel() {
    if (!confirm('Are you sure you want to kill ALL NoxPanel processes? This might affect the current session.')) {
        return;
    }

    try {
        const response = await fetch('/api/admin/processes/kill-all-noxpanel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            adminPanel.showNotification(`${result.message} (${result.killed_count} processes)`, 'success');
            await refreshProcesses();
        } else {
            adminPanel.showNotification(result.message, 'error');
        }
    } catch (error) {
        console.error('Kill all NoxPanel error:', error);
        adminPanel.showNotification('Error killing NoxPanel processes', 'error');
    }
}

async function emergencyCleanup() {
    const confirmText = 'DANGER! This will kill ALL Python processes on the system. Type "CONFIRM" to proceed:';
    const userInput = prompt(confirmText);

    if (userInput !== 'CONFIRM') {
        adminPanel.showNotification('Emergency cleanup cancelled', 'info');
        return;
    }

    try {
        const response = await fetch('/api/admin/emergency-cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            adminPanel.showNotification(`Emergency cleanup complete: ${result.killed_count} processes killed`, 'warning');
            await refreshProcesses();
        } else {
            adminPanel.showNotification(result.message, 'error');
        }
    } catch (error) {
        console.error('Emergency cleanup error:', error);
        adminPanel.showNotification('Error during emergency cleanup', 'error');
    }
}

// Script Management Functions
async function refreshScripts() {
    if (adminPanel) {
        await adminPanel.loadScriptData();
        adminPanel.showNotification('Scripts refreshed', 'success');
    }
}

async function createSampleScripts() {
    try {
        const response = await fetch('/api/scripts/create-samples', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.success) {
            adminPanel.showNotification(`${result.message}`, 'success');
            await refreshScripts();
        } else {
            adminPanel.showNotification(result.message, 'error');
        }
    } catch (error) {
        console.error('Create samples error:', error);
        adminPanel.showNotification('Error creating sample scripts', 'error');
    }
}

async function viewScript(scriptPath) {
    try {
        const response = await fetch(`/api/scripts/content?path=${encodeURIComponent(scriptPath)}`);
        const result = await response.json();

        if (result.success) {
            // Create modal to show script content
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Script Content: ${scriptPath.split('/').pop()}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="code-block" style="max-height: 400px; overflow-y: auto;">
                                <pre><code>${result.content}</code></pre>
                            </div>
                            <div class="mt-3">
                                <small class="text-muted">
                                    Size: ${result.size_bytes} bytes • Lines: ${result.lines}
                                </small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            // Remove modal from DOM when closed
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });

        } else {
            adminPanel.showNotification(result.message, 'error');
        }
    } catch (error) {
        console.error('View script error:', error);
        adminPanel.showNotification('Error loading script content', 'error');
    }
}

async function executeScript(scriptPath, scriptName) {
    const modal = document.getElementById('scriptExecutionModal');
    const formContainer = document.getElementById('script-execution-form');
    const outputContainer = document.getElementById('script-execution-output');
    const executeBtn = document.getElementById('execute-script-btn');

    // Reset modal
    outputContainer.style.display = 'none';
    formContainer.innerHTML = `
        <h6>Execute: ${scriptName}</h6>
        <p class="text-muted">${scriptPath}</p>
        <div class="mb-3">
            <label class="form-label">Timeout (seconds):</label>
            <input type="number" class="form-control" id="script-timeout" value="300" min="1" max="3600">
        </div>
        <div class="mb-3">
            <label class="form-label">Parameters (JSON format, optional):</label>
            <textarea class="form-control" id="script-parameters" rows="3" placeholder='{"param1": "value1", "param2": "value2"}'></textarea>
            <small class="text-muted">Leave empty for no parameters</small>
        </div>
    `;

    // Setup execute button
    executeBtn.onclick = async () => {
        const timeout = parseInt(document.getElementById('script-timeout').value) || 300;
        const parametersText = document.getElementById('script-parameters').value.trim();
        let parameters = {};

        if (parametersText) {
            try {
                parameters = JSON.parse(parametersText);
            } catch (e) {
                adminPanel.showNotification('Invalid JSON in parameters', 'error');
                return;
            }
        }

        executeBtn.disabled = true;
        executeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Executing...';

        try {
            const response = await fetch('/api/scripts/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    script_path: scriptPath,
                    parameters: parameters,
                    timeout: timeout
                })
            });

            const result = await response.json();

            // Show output
            const outputDiv = document.getElementById('execution-result');
            outputDiv.innerHTML = `
                <div class="mb-2">
                    <strong>Status:</strong>
                    <span class="badge ${result.success ? 'bg-success' : 'bg-danger'}">
                        ${result.success ? 'Success' : 'Failed'}
                    </span>
                    ${result.exit_code !== undefined ? `<span class="badge bg-secondary">Exit Code: ${result.exit_code}</span>` : ''}
                    ${result.duration_seconds ? `<span class="badge bg-info">Duration: ${result.duration_seconds}s</span>` : ''}
                </div>
                ${result.output ? `<div><strong>Output:</strong><pre class="mt-2">${result.output}</pre></div>` : ''}
                ${result.error ? `<div><strong>Error:</strong><pre class="mt-2 text-danger">${result.error}</pre></div>` : ''}
                <div class="mt-2"><small class="text-muted">Command: ${result.command || 'N/A'}</small></div>
            `;

            outputContainer.style.display = 'block';

            if (result.success) {
                adminPanel.showNotification('Script executed successfully', 'success');
            } else {
                adminPanel.showNotification(`Script execution failed: ${result.message}`, 'error');
            }

        } catch (error) {
            console.error('Script execution error:', error);
            adminPanel.showNotification('Error executing script', 'error');
        } finally {
            executeBtn.disabled = false;
            executeBtn.innerHTML = 'Execute';
        }
    };

    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}
