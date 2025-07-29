#!/bin/bash
set -e

echo "🚀 NoxPanel Suite Container Environment Setup"
echo "============================================="

# System information
echo "📊 Container System Information:"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "CPU Cores: $(nproc)"
echo "Disk Space: $(df -h / | tail -1 | awk '{print $4}' | sed 's/G/GB/')"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p /workspace/{logs,data,cache,uploads}
mkdir -p /workspace/AI/NoxPanel/frontend/node_modules
mkdir -p /workspace/.vscode-server

# Set proper permissions
chown -R vscode:vscode /workspace
chmod -R 755 /workspace

# Python environment setup
echo "🐍 Setting up Python environment..."
if [ -f "/workspace/requirements-dev.txt" ]; then
    pip install --upgrade pip
    pip install -r /workspace/requirements-dev.txt
    echo "✅ Python dependencies installed"
else
    echo "⚠️ requirements-dev.txt not found, skipping Python setup"
fi

# Node.js setup for frontend
echo "📦 Setting up Node.js environment..."
if [ -d "/workspace/AI/NoxPanel/frontend" ]; then
    cd /workspace/AI/NoxPanel/frontend
    if [ -f "package.json" ]; then
        npm install --legacy-peer-deps
        echo "✅ Node.js dependencies installed"
    fi
    cd /workspace
else
    echo "⚠️ Frontend directory not found, skipping Node.js setup"
fi

# PHP setup (if needed)
echo "🐘 Checking PHP environment..."
if command -v php &> /dev/null; then
    php_version=$(php -v | head -n1 | cut -d' ' -f2)
    echo "✅ PHP $php_version available"
    
    # Install Composer if not present
    if ! command -v composer &> /dev/null; then
        curl -sS https://getcomposer.org/installer | php
        mv composer.phar /usr/local/bin/composer
        echo "✅ Composer installed"
    fi
else
    echo "⚠️ PHP not available in container"
fi

# Git configuration
echo "🔧 Configuring Git..."
git config --global --add safe.directory /workspace
git config --global core.autocrlf input
git config --global core.fileMode false

# Performance optimization
echo "⚡ Applying performance optimizations..."

# Increase file watcher limits
echo fs.inotify.max_user_watches=524288 >> /etc/sysctl.conf
echo fs.inotify.max_user_instances=512 >> /etc/sysctl.conf

# Create performance benchmark script
cat > /workspace/.devcontainer/benchmark.sh << 'EOF'
#!/bin/bash
echo "🔍 Running NoxPanel Container Performance Benchmark..."

start_time=$(date +%s.%N)

# Test 1: File indexing speed
echo "📁 Testing file indexing..."
find /workspace -name "*.py" -o -name "*.js" -o -name "*.php" | wc -l > /tmp/file_count.txt
indexing_time=$(echo "$(date +%s.%N) - $start_time" | bc)

# Test 2: Python import speed
echo "🐍 Testing Python import speed..."
python_start=$(date +%s.%N)
python -c "import sys; import json; import requests; print('Python imports: OK')" 2>/dev/null || echo "Python imports: FAILED"
python_time=$(echo "$(date +%s.%N) - $python_start" | bc)

# Test 3: Node.js startup speed
echo "📦 Testing Node.js startup..."
node_start=$(date +%s.%N)
node -e "console.log('Node.js startup: OK')" 2>/dev/null || echo "Node.js startup: FAILED"
node_time=$(echo "$(date +%s.%N) - $node_start" | bc)

# Test 4: Git operations speed
echo "🔧 Testing Git performance..."
git_start=$(date +%s.%N)
git status > /dev/null 2>&1
git_time=$(echo "$(date +%s.%N) - $git_start" | bc)

total_time=$(echo "$(date +%s.%N) - $start_time" | bc)

echo "📊 Performance Results:"
echo "  Total Setup Time: ${total_time}s"
echo "  File Indexing: ${indexing_time}s"
echo "  Python Imports: ${python_time}s"
echo "  Node.js Startup: ${node_time}s"
echo "  Git Operations: ${git_time}s"
echo "  Files Indexed: $(cat /tmp/file_count.txt)"

# Save results for comparison
cat > /workspace/.devcontainer/benchmark_results.json << EOJ
{
  "timestamp": "$(date -Iseconds)",
  "container_startup": "${total_time}",
  "file_indexing": "${indexing_time}",
  "python_imports": "${python_time}",
  "nodejs_startup": "${node_time}",
  "git_operations": "${git_time}",
  "files_indexed": $(cat /tmp/file_count.txt)
}
EOJ

echo "✅ Benchmark completed - results saved to benchmark_results.json"
EOF

chmod +x /workspace/.devcontainer/benchmark.sh

echo "✅ NoxPanel Container Environment Setup Complete!"
echo "🎯 Run '/workspace/.devcontainer/benchmark.sh' to test performance"
