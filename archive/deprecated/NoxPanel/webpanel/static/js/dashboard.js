// NoxPanel Dashboard JavaScript
class NoxDashboard {
    constructor() {
        this.currentTab = 'scripts';
        this.logs = [];
        this.startTime = Date.now();
        this.devices = [];
        this.socket = null;
        this.systemMetrics = {};
        this.backgroundTasks = {};
        this.init();
    }

    init() {
        this.updateUptime();
        this.setupEventListeners();
        this.initializeWebSocket();
        this.loadDevices();
        this.loadSystemMetrics();
        this.loadPlugins();

        setInterval(() => this.updateUptime(), 1000);
        setInterval(() => this.requestSystemStatus(), 10000); // Request every 10 seconds
    }

    initializeWebSocket() {
        try {
            // Initialize Socket.IO connection
            this.socket = io();

            this.socket.on('connect', () => {
                this.addLog('🔌 WebSocket connected - Real-time updates enabled');
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                this.addLog('⚠️ WebSocket disconnected - Attempting to reconnect...');
                this.updateConnectionStatus(false);
            });

            this.socket.on('device_update', (data) => {
                this.handleDeviceUpdate(data);
            });

            this.socket.on('system_metrics', (metrics) => {
                this.updateSystemMetrics(metrics);
            });

            this.socket.on('scan_complete', (data) => {
                this.handleScanComplete(data);
            });

            this.socket.on('user_created', (data) => {
                this.addLog(`👤 New user created: ${data.username} (${data.role})`);
                this.refreshUserList();
            });

            this.socket.on('plugin_loaded', (data) => {
                this.addLog(`🧩 Plugin loaded: ${data.plugin_name}`);
                this.loadPlugins();
            });

            this.socket.on('error', (data) => {
                this.addLog(`❌ WebSocket error: ${data.message}`);
            });

        } catch (error) {
            this.addLog(`❌ WebSocket initialization failed: ${error.message}`);
            console.error('WebSocket initialization error:', error);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.querySelector('.connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
            statusElement.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
        }
    }

    requestSystemStatus() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('request_system_status');
        }
    }

    handleDeviceUpdate(data) {
        this.addLog(`📡 Device update: ${data.devices_found} devices found`);
        this.loadDevices(); // Refresh device list
    }

    updateSystemMetrics(metrics) {
        this.systemMetrics = metrics;
        this.updateSystemDashboard(metrics);
    }

    updateSystemDashboard(metrics) {
        // Update CPU usage
        const cpuElement = document.querySelector('.cpu-usage');
        if (cpuElement) {
            cpuElement.textContent = `${metrics.cpu.percent.toFixed(1)}%`;
            cpuElement.className = `cpu-usage ${this.getUsageClass(metrics.cpu.percent)}`;
        }

        // Update Memory usage
        const memoryElement = document.querySelector('.memory-usage');
        if (memoryElement) {
            memoryElement.textContent = `${metrics.memory.percent.toFixed(1)}%`;
            memoryElement.className = `memory-usage ${this.getUsageClass(metrics.memory.percent)}`;
        }

        // Update Disk usage
        const diskElement = document.querySelector('.disk-usage');
        if (diskElement) {
            diskElement.textContent = `${metrics.disk.percent.toFixed(1)}%`;
            diskElement.className = `disk-usage ${this.getUsageClass(metrics.disk.percent)}`;
        }

        // Update timestamp
        const timestampElement = document.querySelector('.metrics-timestamp');
        if (timestampElement) {
            timestampElement.textContent = new Date(metrics.timestamp * 1000).toLocaleTimeString();
        }
    }

    getUsageClass(percentage) {
        if (percentage > 80) return 'high-usage';
        if (percentage > 60) return 'medium-usage';
        return 'low-usage';
    }

    handleScanComplete(data) {
        const taskElement = document.querySelector(`[data-task-id="${data.task_id}"]`);
        if (taskElement) {
            taskElement.innerHTML = `
                <span class="task-status completed">✅ Completed</span>
                <span class="task-result">${data.devices_found} devices found</span>
            `;
        }

        this.addLog(`✅ Network scan completed: ${data.devices_found} devices found`);
        this.loadDevices(); // Refresh device list
    }

    async runScript(scriptName) {
        this.addLog(`Executing script: ${scriptName}`);

        try {
            const response = await fetch(`/run/${scriptName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify({ args: [] })
            });

            const result = await response.json();

            if (result.status === 'ok') {
                this.addLog(`Script completed successfully: ${scriptName}`);
                this.showOutput(scriptName, result.stdout, result.stderr, result.returncode);
            } else {
                this.addLog(`Script failed: ${scriptName} - ${result.message}`);
                this.showOutput(scriptName, result.stdout || '', result.stderr || result.message, result.returncode || 1);
            }
        } catch (error) {
            this.addLog(`Error executing script: ${scriptName} - ${error.message}`);
            this.showOutput(scriptName, '', error.message, 1);
        }
    }

    showOutput(scriptName, stdout, stderr, returncode) {
        const modal = document.getElementById('output-modal');
        const title = document.getElementById('modal-title');
        const content = document.getElementById('output-content');

        title.textContent = `Output: ${scriptName}`;

        let output = '';
        if (stdout) {
            output += `STDOUT:\n${stdout}\n\n`;
        }
        if (stderr) {
            output += `STDERR:\n${stderr}\n\n`;
        }
        output += `Exit Code: ${returncode}`;

        content.textContent = output;
        modal.style.display = 'block';
    }

    closeModal() {
        document.getElementById('output-modal').style.display = 'none';
    }

    viewScript(scriptName) {
        // This would typically fetch and display the script content
        this.addLog(`Viewing script: ${scriptName}`);
        alert(`View script functionality would show: ${scriptName}`);
    }

    addLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.logs.unshift({ timestamp, message });

        // Keep only last 100 logs
        if (this.logs.length > 100) {
            this.logs = this.logs.slice(0, 100);
        }

        this.updateLogsDisplay();
    }

    updateLogsDisplay() {
        const logsContent = document.getElementById('logs-content');
        logsContent.innerHTML = this.logs.map(log =>
            `<div class="log-entry">
                <span class="timestamp">${log.timestamp}</span>
                <span class="message">${log.message}</span>
            </div>`
        ).join('');
    }

    clearLogs() {
        this.logs = [];
        this.updateLogsDisplay();
        this.addLog('Logs cleared');
    }

    updateUptime() {
        const uptime = Date.now() - this.startTime;
        const seconds = Math.floor(uptime / 1000) % 60;
        const minutes = Math.floor(uptime / (1000 * 60)) % 60;
        const hours = Math.floor(uptime / (1000 * 60 * 60));

        const uptimeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            uptimeElement.textContent = uptimeStr;
        }
    }

    toggleTheme() {
        // Theme toggle functionality - could expand to support light theme
        document.body.classList.toggle('light-theme');
    }

    getToken() {
        // In a real implementation, this would get the auth token
        return localStorage.getItem('nox_token') || 'demo_token';
    }

    async loadDevices() {
        try {
            const response = await fetch('/api/devices');
            const result = await response.json();

            if (result.status === 'ok') {
                this.devices = result.devices;
                this.updateDevicesDisplay();
                this.addLog(`Loaded ${result.total} devices (${result.online} online)`);
            } else {
                this.addLog(`Failed to load devices: ${result.message}`);
            }
        } catch (error) {
            this.addLog(`Error loading devices: ${error.message}`);
        }
    }

    updateDevicesDisplay() {
        // Add devices tab content if it exists
        const devicesTab = document.getElementById('devices-tab');
        if (devicesTab) {
            const devicesGrid = devicesTab.querySelector('.devices-grid') || this.createDevicesGrid(devicesTab);

            if (this.devices.length === 0) {
                devicesGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-network-wired"></i>
                        <h3>No Devices Found</h3>
                        <p>Run a network scan to discover devices.</p>
                        <button class="btn btn-primary" onclick="dashboard.scanNetwork()">
                            <i class="fas fa-search"></i> Scan Network
                        </button>
                    </div>
                `;
            } else {
                devicesGrid.innerHTML = this.devices.map(device => `
                    <div class="device-card">
                        <div class="device-header">
                            <i class="fas fa-${this.getDeviceIcon(device.type)}"></i>
                            <h3>${device.name || device.ip}</h3>
                        </div>
                        <div class="device-info">
                            <div class="info-item">
                                <span class="label">IP:</span>
                                <span class="value">${device.ip}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">MAC:</span>
                                <span class="value">${device.mac_address || 'Unknown'}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Status:</span>
                                <span class="value ${device.online ? 'online' : 'offline'}">
                                    ${device.online ? 'Online' : 'Offline'}
                                </span>
                            </div>
                            <div class="info-item">
                                <span class="label">Last Seen:</span>
                                <span class="value">${device.last_seen || 'Never'}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        }
    }

    createDevicesGrid(devicesTab) {
        const devicesGrid = document.createElement('div');
        devicesGrid.className = 'devices-grid';
        devicesTab.appendChild(devicesGrid);
        return devicesGrid;
    }

    getDeviceIcon(type) {
        const icons = {
            'router': 'router',
            'switch': 'network-wired',
            'access_point': 'wifi',
            'nas': 'hdd',
            'printer': 'print',
            'camera': 'camera',
            'computer': 'desktop',
            'phone': 'mobile-alt',
            'unknown': 'question'
        };
        return icons[type] || 'question';
    }

    async scanNetwork() {
        this.addLog('🔍 Starting background network scan...');

        try {
            const response = await fetch('/api/devices/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            const result = await response.json();

            if (result.status === 'ok') {
                this.addBackgroundTask(result.task_id, 'Network Scan', 'running');
                this.addLog(`📤 Network scan task submitted: ${result.task_id}`);
            } else {
                this.addLog(`❌ Network scan failed: ${result.message}`);
            }
        } catch (error) {
            this.addLog(`❌ Network scan error: ${error.message}`);
        }
    }

    addBackgroundTask(taskId, taskName, status) {
        this.backgroundTasks[taskId] = {
            name: taskName,
            status: status,
            startTime: Date.now()
        };
        this.updateBackgroundTasksDisplay();
    }

    updateBackgroundTasksDisplay() {
        const tasksContainer = document.querySelector('.background-tasks');
        if (!tasksContainer) return;

        const tasksList = Object.entries(this.backgroundTasks).map(([taskId, task]) => `
            <div class="task-item" data-task-id="${taskId}">
                <span class="task-name">${task.name}</span>
                <span class="task-status ${task.status}">
                    ${task.status === 'running' ? '⏳ Running' : task.status}
                </span>
            </div>
        `).join('');

        tasksContainer.innerHTML = tasksList || '<div class="no-tasks">No background tasks</div>';
    }

    async loadPlugins() {
        try {
            const response = await fetch('/api/plugins');
            const result = await response.json();

            if (result.status === 'ok') {
                this.updatePluginsDisplay(result.plugins);
                this.addLog(`🧩 Loaded ${result.total_available} plugins (${result.total_loaded} active)`);
            } else {
                this.addLog(`❌ Failed to load plugins: ${result.message}`);
            }
        } catch (error) {
            this.addLog(`❌ Plugin loading error: ${error.message}`);
        }
    }

    updatePluginsDisplay(plugins) {
        const pluginsTab = document.getElementById('plugins-tab');
        if (!pluginsTab) return;

        const pluginsGrid = pluginsTab.querySelector('.plugins-grid') || this.createPluginsGrid(pluginsTab);

        if (Object.keys(plugins).length === 0) {
            pluginsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-puzzle-piece"></i>
                    <h3>No Plugins Found</h3>
                    <p>No plugins are available in the plugins directory.</p>
                </div>
            `;
        } else {
            pluginsGrid.innerHTML = Object.entries(plugins).map(([name, plugin]) => `
                <div class="plugin-card ${plugin.loaded ? 'loaded' : 'unloaded'}">
                    <div class="plugin-header">
                        <i class="fas fa-puzzle-piece"></i>
                        <h3>${plugin.name || name}</h3>
                        <span class="plugin-status ${plugin.loaded ? 'loaded' : 'unloaded'}">
                            ${plugin.loaded ? '🟢 Loaded' : '⚪ Available'}
                        </span>
                    </div>
                    <div class="plugin-info">
                        <p class="plugin-description">${plugin.description || 'No description available'}</p>
                        <div class="plugin-details">
                            <span class="plugin-version">v${plugin.version || '1.0.0'}</span>
                            <span class="plugin-author">${plugin.author || 'Unknown'}</span>
                        </div>
                    </div>
                    <div class="plugin-actions">
                        ${!plugin.loaded ? `
                            <button class="btn btn-primary" onclick="dashboard.loadPlugin('${name}')">
                                <i class="fas fa-play"></i> Load
                            </button>
                        ` : `
                            <button class="btn btn-secondary" disabled>
                                <i class="fas fa-check"></i> Loaded
                            </button>
                        `}
                    </div>
                </div>
            `).join('');
        }
    }

    createPluginsGrid(pluginsTab) {
        const pluginsGrid = document.createElement('div');
        pluginsGrid.className = 'plugins-grid';
        pluginsTab.appendChild(pluginsGrid);
        return pluginsGrid;
    }

    async loadPlugin(pluginName) {
        try {
            const response = await fetch(`/api/plugins/${pluginName}/load`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            const result = await response.json();

            if (result.status === 'ok') {
                this.addLog(`🧩 Plugin ${pluginName} loaded successfully`);
                // Plugin list will be updated via WebSocket event
            } else {
                this.addLog(`❌ Failed to load plugin ${pluginName}: ${result.message}`);
            }
        } catch (error) {
            this.addLog(`❌ Plugin load error: ${error.message}`);
        }
    }

    async loadSystemMetrics() {
        try {
            const response = await fetch('/api/system/metrics');
            const result = await response.json();

            if (result.status === 'ok') {
                this.updateSystemMetrics(result.metrics);
            }
        } catch (error) {
            console.error('System metrics error:', error);
        }
    }
}

// Global functions for HTML onclick events
let dashboard;

function showTab(tabName) {
    dashboard.showTab(tabName);
}

function runScript(scriptName) {
    dashboard.runScript(scriptName);
}

function viewScript(scriptName) {
    dashboard.viewScript(scriptName);
}

function clearLogs() {
    dashboard.clearLogs();
}

function closeModal() {
    dashboard.closeModal();
}

function toggleTheme() {
    dashboard.toggleTheme();
}

// Add network scanning function to global scope
function scanNetwork() {
    dashboard.scanNetwork();
}

// Add plugin loading function to global scope
function loadPlugin(pluginName) {
    dashboard.loadPlugin(pluginName);
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new NoxDashboard();
    dashboard.addLog('NoxPanel dashboard initialized');
});
