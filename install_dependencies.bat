@echo off
echo Ultimate Suite v11.0 - Automated Dependency Installation
echo ============================================================

echo Installing Docker Desktop...
winget install Docker.DockerDesktop

echo Upgrading pip and installing AI frameworks...
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate
pip install onnxruntime-gpu
pip install scikit-learn numpy pandas

echo Installing web frameworks...
pip install fastapi uvicorn[standard]
pip install aiohttp aiofiles
pip install redis

echo Installing security frameworks...
pip install cryptography passlib[bcrypt]
pip install python-jose[cryptography]
pip install python-multipart

echo Installing cloud SDKs...
pip install boto3
pip install azure-identity azure-mgmt-core
pip install google-cloud-core

echo Installing development tools...
pip install pytest pytest-asyncio
pip install black flake8 mypy
pip install prometheus-client

echo Installation complete! 
echo Please restart your terminal and run: docker --version
pause
