/**
 * NoxPanel v4.3 - Enhanced Visual Components & Charts
 * Responsive design with Chart.js integration and visual feedback
 */

class NoxPanelVisuals {
    constructor() {
        this.charts = {};
        this.initializeCharts();
        this.setupVisualFeedback();
    }

    initializeCharts() {
        // Initialize Chart.js if available
        if (typeof Chart !== 'undefined') {
            Chart.defaults.responsive = true;
            Chart.defaults.maintainAspectRatio = false;
        }
    }

    /**
     * Create a system metrics chart
     */
    createSystemChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || typeof Chart === 'undefined') return null;

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Used', 'Available'],
                datasets: [{
                    data: [data.used, 100 - data.used],
                    backgroundColor: [
                        data.used > 80 ? '#dc3545' : data.used > 60 ? '#ffc107' : '#28a745',
                        '#e9ecef'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });
    }

    /**
     * Create disk usage visualization
     */
    createDiskUsageChart(containerId, diskData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let html = '<div class="disk-usage-container">';

        diskData.forEach(disk => {
            const usagePercent = ((disk.used / disk.total) * 100).toFixed(1);
            const usageClass = usagePercent > 80 ? 'danger' : usagePercent > 60 ? 'warning' : 'good';

            html += `
                <div class="disk-usage-visual">
                    <div class="disk-info">
                        <h6><i class="fas fa-hdd"></i> ${disk.device}</h6>
                        <small>${this.formatBytes(disk.used)} / ${this.formatBytes(disk.total)}</small>
                    </div>
                    <div class="disk-progress">
                        <div class="disk-progress-bar status-${usageClass}"
                             style="width: ${usagePercent}%"></div>
                    </div>
                    <div class="status-indicator status-${usageClass}">
                        ${usagePercent}%
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Create process table with visual enhancements
     */
    createProcessTable(containerId, processData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let html = `
            <div class="process-table-container">
                <table class="table process-table">
                    <thead>
                        <tr>
                            <th>PID</th>
                            <th>Process Name</th>
                            <th>CPU %</th>
                            <th>Memory %</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        processData.forEach(process => {
            const cpuClass = process.cpu > 50 ? 'danger' : process.cpu > 20 ? 'warning' : 'good';
            const memClass = process.memory > 50 ? 'danger' : process.memory > 20 ? 'warning' : 'good';

            html += `
                <tr>
                    <td><code>${process.pid}</code></td>
                    <td><strong>${process.name}</strong></td>
                    <td>
                        <span class="status-indicator status-${cpuClass}">
                            ${process.cpu.toFixed(1)}%
                        </span>
                    </td>
                    <td>
                        <span class="status-indicator status-${memClass}">
                            ${process.memory.toFixed(1)}%
                        </span>
                    </td>
                    <td>
                        <span class="status-indicator status-good">
                            <i class="fas fa-play-circle"></i> Running
                        </span>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    /**
     * Create animated gauge for metrics
     */
    createGauge(containerId, value, label, color = '#007bff') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const radius = 50;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (value / 100) * circumference;

        container.innerHTML = `
            <div class="gauge-container">
                <svg class="gauge-svg" width="120" height="120">
                    <circle class="gauge-background" cx="60" cy="60" r="${radius}"></circle>
                    <circle class="gauge-progress" cx="60" cy="60" r="${radius}"
                            style="stroke: ${color}; stroke-dasharray: ${circumference}; stroke-dashoffset: ${offset}">
                    </circle>
                </svg>
                <div class="gauge-text">${value}%</div>
            </div>
            <div class="text-center mt-2">
                <small class="text-muted">${label}</small>
            </div>
        `;
    }

    /**
     * Create metrics grid with visual cards
     */
    createMetricsGrid(containerId, metrics) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let html = '<div class="metrics-grid">';

        metrics.forEach(metric => {
            const icon = this.getMetricIcon(metric.type);
            const gradient = this.getMetricGradient(metric.type);

            html += `
                <div class="metric-card" style="background: ${gradient}">
                    <div class="metric-icon">${icon}</div>
                    <div class="metric-value">${metric.value}</div>
                    <div class="metric-label">${metric.label}</div>
                    <div class="realtime-indicator">
                        <div class="realtime-dot"></div>
                        Live
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Enhanced command result display with visual formatting
     */
    showEnhancedCommandResult(command, result, type = 'success') {
        let resultArea = document.getElementById('command-result-area');
        if (!resultArea) {
            resultArea = document.createElement('div');
            resultArea.id = 'command-result-area';
            resultArea.className = 'command-result-area';
            document.querySelector('.dashboard-grid').parentNode.insertBefore(resultArea, document.querySelector('.dashboard-grid'));
        }

        // Parse result based on command type
        let formattedContent = '';

        if (command.includes('system check')) {
            formattedContent = this.formatSystemCheckResult(result);
        } else if (command.includes('disk usage')) {
            formattedContent = this.formatDiskUsageResult(result);
        } else if (command.includes('processes')) {
            formattedContent = this.formatProcessResult(result);
        } else if (command.includes('services')) {
            formattedContent = this.formatServicesResult(result);
        } else {
            formattedContent = this.formatGenericResult(result);
        }

        resultArea.className = `command-result-area command-${type}`;
        resultArea.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-3">
                <div class="d-flex align-items-center gap-2">
                    <i class="fas fa-terminal text-primary"></i>
                    <h6 class="mb-0">Command: ${command}</h6>
                    <div class="realtime-indicator">
                        <div class="realtime-dot"></div>
                        Just now
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-primary" onclick="this.copyResult()" title="Copy Result">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="this.parentElement.parentElement.parentElement.style.display='none'">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            ${formattedContent}
        `;

        resultArea.style.display = 'block';

        // Smooth scroll to result
        resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    formatSystemCheckResult(result) {
        const lines = result.split('\n');
        let html = '<div class="system-check-result">';

        lines.forEach(line => {
            if (line.includes('CPU Usage:')) {
                const value = parseFloat(line.match(/(\d+\.?\d*)%/)[1]);
                html += `<div id="cpu-gauge-container"></div>`;
                setTimeout(() => this.createGauge('cpu-gauge-container', value, 'CPU Usage', '#007bff'), 100);
            } else if (line.includes('Memory Usage:')) {
                const value = parseFloat(line.match(/(\d+\.?\d*)%/)[1]);
                html += `<div id="memory-gauge-container"></div>`;
                setTimeout(() => this.createGauge('memory-gauge-container', value, 'Memory Usage', '#28a745'), 100);
            } else if (line.includes('Disk Usage:')) {
                const value = parseFloat(line.match(/(\d+\.?\d*)%/)[1]);
                html += `<div id="disk-gauge-container"></div>`;
                setTimeout(() => this.createGauge('disk-gauge-container', value, 'Disk Usage', '#ffc107'), 100);
            } else if (line.trim()) {
                html += `<div class="metric-line">${line}</div>`;
            }
        });

        html += '</div>';
        return html;
    }

    formatDiskUsageResult(result) {
        const lines = result.split('\n');
        let html = '<div class="disk-usage-result">';
        let diskData = [];

        // Parse disk data
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.includes(':') && !line.includes('Disk Usage Report')) {
                const device = line.trim();
                const totalMatch = lines[i + 1]?.match(/Total: ([\d.]+) GB/);
                const freeMatch = lines[i + 2]?.match(/Free: ([\d.]+) GB/);
                const usedMatch = lines[i + 3]?.match(/Used: ([\d.]+)%/);

                if (totalMatch && freeMatch && usedMatch) {
                    diskData.push({
                        device: device,
                        total: parseFloat(totalMatch[1]) * 1024 * 1024 * 1024,
                        free: parseFloat(freeMatch[1]) * 1024 * 1024 * 1024,
                        used: parseFloat(totalMatch[1]) - parseFloat(freeMatch[1]) * 1024 * 1024 * 1024,
                        percentage: parseFloat(usedMatch[1])
                    });
                }
            }
        }

        html += '<div id="disk-visualization"></div>';
        setTimeout(() => this.createDiskUsageChart('disk-visualization', diskData), 100);

        html += '</div>';
        return html;
    }

    formatProcessResult(result) {
        // Parse process data and create visual table
        const lines = result.split('\n').filter(line => line.trim() && !line.includes('-'));
        let processData = [];

        lines.forEach(line => {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 4 && !isNaN(parts[0])) {
                processData.push({
                    pid: parseInt(parts[0]),
                    name: parts[1],
                    cpu: parseFloat(parts[2]) || 0,
                    memory: parseFloat(parts[3]) || 0
                });
            }
        });

        let html = '<div id="process-table-container"></div>';
        setTimeout(() => this.createProcessTable('process-table-container', processData), 100);

        return html;
    }

    formatServicesResult(result) {
        return `<pre class="service-output">${result}</pre>`;
    }

    formatGenericResult(result) {
        return `<pre class="generic-output">${result}</pre>`;
    }

    /**
     * Setup visual feedback for interactions
     */
    setupVisualFeedback() {
        // Add loading states to buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-action-btn') || e.target.closest('.quick-action-btn')) {
                const btn = e.target.classList.contains('quick-action-btn') ? e.target : e.target.closest('.quick-action-btn');

                // Add loading state
                btn.classList.add('command-loading');
                const originalContent = btn.innerHTML;
                btn.innerHTML = `<span class="loading-spinner"></span> Processing...`;

                // Remove loading state after 3 seconds (or when command completes)
                setTimeout(() => {
                    btn.classList.remove('command-loading');
                    btn.innerHTML = originalContent;
                }, 3000);
            }
        });
    }

    /**
     * Utility functions
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getMetricIcon(type) {
        const icons = {
            cpu: '<i class="fas fa-microchip"></i>',
            memory: '<i class="fas fa-memory"></i>',
            disk: '<i class="fas fa-hdd"></i>',
            network: '<i class="fas fa-network-wired"></i>',
            process: '<i class="fas fa-cogs"></i>'
        };
        return icons[type] || '<i class="fas fa-chart-bar"></i>';
    }

    getMetricGradient(type) {
        const gradients = {
            cpu: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            memory: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            disk: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            network: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            process: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
        };
        return gradients[type] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }

    /**
     * Copy result to clipboard
     */
    copyResult() {
        const resultArea = document.getElementById('command-result-area');
        if (resultArea) {
            const text = resultArea.innerText;
            navigator.clipboard.writeText(text).then(() => {
                // Show feedback
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 1000);
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.noxVisuals = new NoxPanelVisuals();
});

// Export for global access
window.NoxPanelVisuals = NoxPanelVisuals;
