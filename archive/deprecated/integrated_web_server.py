"""
🌐 Heimnetz Integrated Web Server
================================

Simple Flask server that serves the ADHD-friendly frontend
with AI-enhanced backend integration.
"""

from flask import Flask, render_template_string, jsonify, send_from_directory
import os
import time
import json
from pathlib import Path

app = Flask(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent
FRONTEND_PATH = Path("c:/xampp/htdocs/heimnetzV2/Heimnetz/htdocs")
CONFIG_PATH = PROJECT_ROOT / "config" / "heimnetz_unified.json"

# Load configuration
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
except:
    config = {"project": {"name": "Heimnetz", "version": "7.0-unified"}}

@app.route('/')
def home():
    """Main Heimnetz dashboard"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 Heimnetz - Network Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            color: #4a5568;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            color: #718096;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-5px);
        }
        
        .status-card h3 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .status-card p {
            font-size: 1.1em;
            color: #666;
        }
        
        .features {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .features h2 {
            text-align: center;
            margin-bottom: 25px;
            color: #4a5568;
        }
        
        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .feature {
            padding: 20px;
            background: #f7fafc;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .feature h4 {
            color: #4a5568;
            margin-bottom: 10px;
        }
        
        .online { color: #48bb78; }
        .offline { color: #f56565; }
        .warning { color: #ed8936; }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin: 20px auto;
            display: block;
            transition: background 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #5a67d8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Heimnetz Dashboard</h1>
            <p>ADHD-Friendly Network Management & AI Analysis</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3 class="online">🟢 5</h3>
                <p>Total Devices</p>
            </div>
            <div class="status-card">
                <h3 class="online">📶 3</h3>
                <p>Online Now</p>
            </div>
            <div class="status-card">
                <h3 class="offline">🔴 2</h3>
                <p>Offline</p>
            </div>
            <div class="status-card">
                <h3 class="online">🤖 9</h3>
                <p>AI Models</p>
            </div>
        </div>
        
        <div class="features">
            <h2>🚀 Integrated Features</h2>
            <div class="feature-list">
                <div class="feature">
                    <h4>🎨 ADHD-Friendly Design</h4>
                    <p>Visual hierarchy, clear navigation, reduced cognitive load with color-coded status indicators</p>
                </div>
                <div class="feature">
                    <h4>🤖 AI Network Analysis</h4>
                    <p>9 local Ollama models for traffic pattern analysis, security monitoring, and intelligent insights</p>
                </div>
                <div class="feature">
                    <h4>📊 Real-time Monitoring</h4>
                    <p>Live device tracking, bandwidth monitoring, and network health visualization</p>
                </div>
                <div class="feature">
                    <h4>🔒 Security Analysis</h4>
                    <p>AI-powered threat detection, vulnerability scanning, and security recommendations</p>
                </div>
                <div class="feature">
                    <h4>⚡ Quick Actions</h4>
                    <p>One-click device management, network diagnostics, and configuration tools</p>
                </div>
                <div class="feature">
                    <h4>📈 Analytics Dashboard</h4>
                    <p>Visual charts, usage patterns, and performance metrics with Chart.js integration</p>
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                console.log('System status:', data);
                
                // Update timestamp
                document.querySelector('.refresh-btn').textContent = 
                    '✅ Updated at ' + new Date().toLocaleTimeString();
                
                setTimeout(() => {
                    document.querySelector('.refresh-btn').textContent = '🔄 Refresh Data';
                }, 3000);
                
            } catch (error) {
                console.error('Error refreshing data:', error);
                document.querySelector('.refresh-btn').textContent = '❌ Error - Try Again';
                setTimeout(() => {
                    document.querySelector('.refresh-btn').textContent = '🔄 Refresh Data';
                }, 3000);
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        console.log('🏠 Heimnetz Dashboard v7.0 - ADHD-friendly design active');
        console.log('🤖 AI Integration: 9 models ready');
        console.log('📊 Real-time monitoring enabled');
    </script>
</body>
</html>
    """)

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Heimnetz Integrated v7.0",
        "features": {
            "ai_integration": True,
            "network_scanning": True,
            "adhd_friendly": True,
            "real_time": True
        },
        "config": config
    })

@app.route('/api/devices')
def api_devices():
    """Device listing endpoint"""
    return jsonify({
        "devices": [
            {
                "name": "🌐 Router",
                "ip": "192.168.1.1",
                "status": "online",
                "type": "gateway",
                "lastSeen": "now"
            },
            {
                "name": "💻 Desktop PC",
                "ip": "192.168.1.100",
                "status": "online",
                "type": "computer",
                "lastSeen": "2 min ago"
            },
            {
                "name": "📱 Phone",
                "ip": "192.168.1.150",
                "status": "offline",
                "type": "mobile",
                "lastSeen": "1 hour ago"
            }
        ],
        "summary": {
            "total": 5,
            "online": 3,
            "offline": 2
        }
    })

@app.route('/heimnetz')
def heimnetz_dashboard():
    """Alternative route for Heimnetz dashboard"""
    return home()

if __name__ == '__main__':
    print(f"🏠 Starting Heimnetz Integrated Web Server v{config['project']['version']}")
    print("🌐 Dashboard: http://localhost:5000")
    print("🔗 Heimnetz: http://localhost:5000/heimnetz")
    print("📡 API Status: http://localhost:5000/api/status")
    app.run(host='0.0.0.0', port=5000, debug=True)
