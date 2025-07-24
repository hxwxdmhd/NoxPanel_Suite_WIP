// NoxPanel Dashboard JavaScript
class NoxDashboard {
    constructor() {
        this.currentTab = 'scripts';
        this.logs = [];
        this.startTime = Date.now();
        this.init();
    }

    init() {
        this.updateUptime();
        this.setupEventListeners();
        setInterval(() => this.updateUptime(), 1000);
    }

    setupEventListeners() {
        // Modal close events
        window.onclick = (event) => {
            const modal = document.getElementById('output-modal');
            if (event.target === modal) {
                this.closeModal();
            }
        };
    }

    showTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected tab
        document.getElementById(tabName + '-tab').classList.add('active');
        document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
        this.currentTab = tabName;
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

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new NoxDashboard();
    dashboard.addLog('NoxPanel dashboard initialized');
});
