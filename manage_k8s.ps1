# 🚀 ULTIMATE SUITE v11.0 - KUBERNETES MANAGEMENT
# ================================================
# PowerShell script for managing Kubernetes deployment

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("deploy", "status", "cleanup", "portforward", "scale", "help")]
    [string]$Action = "help"
)

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "🎯 $Text" -ForegroundColor $Cyan
    Write-Host ("=" * ($Text.Length + 3)) -ForegroundColor $Cyan
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor $Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor $Red
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠️ $Text" -ForegroundColor $Yellow
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️ $Text" -ForegroundColor $Cyan
}

function Test-KubernetesAvailable {
    Write-Header "Testing Kubernetes Environment"
    
    try {
        $kubectlVersion = kubectl version --client 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "kubectl is available"
            Write-Info $kubectlVersion
        } else {
            Write-Error "kubectl not found"
            return $false
        }
        
        # Test cluster connectivity
        kubectl cluster-info >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Kubernetes cluster is accessible"
            return $true
        } else {
            Write-Warning "Kubernetes cluster not accessible"
            Write-Info "Please enable Kubernetes in Docker Desktop settings"
            return $false
        }
    } catch {
        Write-Error "Error testing Kubernetes: $($_.Exception.Message)"
        return $false
    }
}

function Deploy-UltimateSuite {
    Write-Header "Deploying Ultimate Suite v11.0 to Kubernetes"
    
    # Test Kubernetes first
    if (-not (Test-KubernetesAvailable)) {
        Write-Error "Kubernetes environment check failed"
        Write-Info "To enable Kubernetes in Docker Desktop:"
        Write-Info "1. Open Docker Desktop"
        Write-Info "2. Go to Settings > Kubernetes"
        Write-Info "3. Check 'Enable Kubernetes'"
        Write-Info "4. Click 'Apply & Restart'"
        return
    }
    
    # Run Python deployment script
    if (Test-Path "deploy_kubernetes.py") {
        Write-Info "Starting automated Kubernetes deployment..."
        python deploy_kubernetes.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Deployment completed successfully"
            Write-Info "Setting up port forwarding..."
            Start-PortForwarding
        } else {
            Write-Error "Deployment failed"
        }
    } else {
        Write-Error "deploy_kubernetes.py not found"
    }
}

function Get-ClusterStatus {
    Write-Header "Ultimate Suite Kubernetes Status"
    
    $namespace = "ultimate-suite"
    
    # Check if namespace exists
    kubectl get namespace $namespace >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Ultimate Suite namespace not found"
        Write-Info "Run deployment first: .\manage_k8s.ps1 deploy"
        return
    }
    
    Write-Info "Namespace: $namespace"
    Write-Host ""
    
    # Get pods
    Write-Host "📦 PODS:" -ForegroundColor $Cyan
    kubectl get pods -n $namespace
    Write-Host ""
    
    # Get services
    Write-Host "🌐 SERVICES:" -ForegroundColor $Cyan
    kubectl get services -n $namespace
    Write-Host ""
    
    # Get deployments
    Write-Host "🚀 DEPLOYMENTS:" -ForegroundColor $Cyan
    kubectl get deployments -n $namespace
    Write-Host ""
    
    # Get HPA
    Write-Host "📈 HORIZONTAL POD AUTOSCALER:" -ForegroundColor $Cyan
    kubectl get hpa -n $namespace 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Info "HPA not available (metrics server may not be installed)"
    }
    Write-Host ""
    
    # Get resource usage
    Write-Host "💾 RESOURCE USAGE:" -ForegroundColor $Cyan
    kubectl top nodes 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Info "Node metrics not available (metrics server required)"
    }
}

function Start-PortForwarding {
    Write-Header "Setting up Port Forwarding"
    
    $namespace = "ultimate-suite"
    $portForwards = @(
        @{Service="fastapi-service"; Port="8000"; Name="FastAPI Server"},
        @{Service="prometheus-service"; Port="9090"; Name="Prometheus Monitoring"},
        @{Service="grafana-service"; Port="3000"; Name="Grafana Dashboard"}
    )
    
    Write-Info "Starting port forwarding for Ultimate Suite services..."
    
    foreach ($forward in $portForwards) {
        $service = $forward.Service
        $port = $forward.Port
        $name = $forward.Name
        
        Write-Info "Port forwarding $name on port $port"
        
        # Start port forward in background
        Start-Process -FilePath "kubectl" -ArgumentList "port-forward", "service/$service", "${port}:${port}", "-n", "$namespace" -WindowStyle Hidden
        
        Start-Sleep -Seconds 2
    }
    
    Write-Success "Port forwarding started for all services"
    Write-Host ""
    Write-Host "🌐 SERVICE URLS:" -ForegroundColor $Cyan
    Write-Host "├── FastAPI Server: http://localhost:8000" -ForegroundColor $Green
    Write-Host "├── Prometheus: http://localhost:9090" -ForegroundColor $Green
    Write-Host "└── Grafana: http://localhost:3000" -ForegroundColor $Green
    Write-Host ""
    Write-Warning "Port forwarding runs in background. Close terminals to stop."
}

function Scale-Services {
    Write-Header "Scaling Ultimate Suite Services"
    
    $namespace = "ultimate-suite"
    
    # Show current scale
    Write-Info "Current deployment scale:"
    kubectl get deployments -n $namespace
    Write-Host ""
    
    # Interactive scaling
    $deployment = Read-Host "Enter deployment name to scale (fastapi-server, redis, prometheus, grafana)"
    $replicas = Read-Host "Enter number of replicas"
    
    if ($deployment -and $replicas) {
        Write-Info "Scaling $deployment to $replicas replicas..."
        kubectl scale deployment $deployment --replicas=$replicas -n $namespace
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Scaling completed"
            
            # Wait for rollout
            Write-Info "Waiting for rollout to complete..."
            kubectl rollout status deployment/$deployment -n $namespace
        } else {
            Write-Error "Scaling failed"
        }
    }
}

function Remove-UltimateSuite {
    Write-Header "Cleaning up Ultimate Suite Kubernetes Deployment"
    
    $namespace = "ultimate-suite"
    
    # Confirm deletion
    $confirm = Read-Host "Are you sure you want to delete the Ultimate Suite deployment? (y/N)"
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Write-Info "Deleting namespace: $namespace"
        kubectl delete namespace $namespace
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Ultimate Suite deployment cleaned up successfully"
        } else {
            Write-Error "Cleanup failed"
        }
        
        # Stop any running port forwards
        Write-Info "Stopping port forwarding processes..."
        Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*port-forward*" } | Stop-Process -Force
        
    } else {
        Write-Info "Cleanup cancelled"
    }
}

function Show-Help {
    Write-Header "Ultimate Suite Kubernetes Management"
    
    Write-Host "USAGE:" -ForegroundColor $Cyan
    Write-Host "  .\manage_k8s.ps1 [action]" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor $Cyan
    Write-Host "  deploy      - Deploy Ultimate Suite to Kubernetes" -ForegroundColor $Yellow
    Write-Host "  status      - Show cluster and deployment status" -ForegroundColor $Yellow
    Write-Host "  portforward - Setup port forwarding to access services" -ForegroundColor $Yellow
    Write-Host "  scale       - Scale deployments up or down" -ForegroundColor $Yellow
    Write-Host "  cleanup     - Remove Ultimate Suite deployment" -ForegroundColor $Yellow
    Write-Host "  help        - Show this help message" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor $Cyan
    Write-Host "  .\manage_k8s.ps1 deploy     # Deploy to Kubernetes" -ForegroundColor $Green
    Write-Host "  .\manage_k8s.ps1 status     # Check deployment status" -ForegroundColor $Green
    Write-Host "  .\manage_k8s.ps1 scale      # Scale services" -ForegroundColor $Green
    Write-Host ""
    Write-Host "PREREQUISITES:" -ForegroundColor $Cyan
    Write-Host "  • Docker Desktop with Kubernetes enabled" -ForegroundColor $Yellow
    Write-Host "  • kubectl installed and configured" -ForegroundColor $Yellow
    Write-Host "  • Helm installed (optional, for advanced features)" -ForegroundColor $Yellow
    Write-Host ""
    Write-Host "SERVICE URLS (after deployment):" -ForegroundColor $Cyan
    Write-Host "  • FastAPI Server: http://localhost:8000" -ForegroundColor $Green
    Write-Host "  • Prometheus: http://localhost:9090" -ForegroundColor $Green
    Write-Host "  • Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor $Green
}

# Main execution
switch ($Action.ToLower()) {
    "deploy" { Deploy-UltimateSuite }
    "status" { Get-ClusterStatus }
    "portforward" { Start-PortForwarding }
    "scale" { Scale-Services }
    "cleanup" { Remove-UltimateSuite }
    "help" { Show-Help }
    default { Show-Help }
}

Write-Host ""
