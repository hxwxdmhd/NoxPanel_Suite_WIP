# NoxPanel Suite WSL2 Setup Guide

## Prerequisites
1. Enable WSL2: `wsl --install`
2. Install Ubuntu 22.04: `wsl --install -d Ubuntu-22.04`
3. Install VS Code WSL extension

## Setup Commands (Run in WSL2)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PHP 8.2
sudo apt install -y php8.2 php8.2-cli php8.2-curl php8.2-json php8.2-mbstring

# Install Docker
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# Clone project (if needed)
git clone /mnt/k/Project\ Heimnetz/ ~/noxpanel-suite
cd ~/noxpanel-suite

# Create Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## VS Code WSL2 Settings Override

```json
{
  "remote.WSL.fileWatcher.polling": true,
  "remote.WSL.fileWatcher.pollingInterval": 5000,
  "terminal.integrated.defaultProfile.linux": "bash",
  "python.defaultInterpreterPath": "~/.venv/bin/python"
}
```

## Performance Benefits
- Native Linux performance for Docker operations
- Better file system performance for large projects
- Isolated environment without Windows file system overhead
- Direct access to Linux-native development tools
