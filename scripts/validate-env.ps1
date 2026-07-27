param(
    [string]$EnvFile = ".env"
)

$errors = @()

# Check .env exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ .env file not found at $EnvFile. Copy .env.example to .env" -ForegroundColor Red
    exit 1
}

# Check required tools
$tools = @(
    @{Name="Python"; Command="python --version"},
    @{Name="Node"; Command="node --version"},
    @{Name="npm"; Command="npm --version"},
    @{Name="Tesseract"; Command="tesseract --version"}
)

Write-Host "`n🔍 Checking Required Tools..." -ForegroundColor Cyan
foreach ($tool in $tools) {
    try {
        $output = Invoke-Expression $tool.Command 2>&1
        Write-Host "  ✅ $($tool.Name): $($output -join ' ')" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ $($tool.Name): Not found" -ForegroundColor Red
        $errors += "Missing: $($tool.Name)"
    }
}

# Check Python packages
Write-Host "`n📦 Checking Python Dependencies..." -ForegroundColor Cyan
if (Test-Path "backend/requirements.txt") {
    try {
        $installed = pip list --format=columns 2>&1
        Write-Host "  ✅ Python packages installed ($(($installed | Measure-Object -Line).Lines) packages)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not verify Python packages. Run: pip install -r backend/requirements.txt" -ForegroundColor Yellow
    }
}

# Check Node packages
Write-Host "`n📦 Checking Node Dependencies..." -ForegroundColor Cyan
if (Test-Path "frontend/node_modules") {
    Write-Host "  ✅ node_modules exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  node_modules not found. Run: cd frontend && npm install" -ForegroundColor Yellow
    $errors += "Missing: node_modules"
}

# Docker
Write-Host "`n🐳 Checking Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "  ✅ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Docker not found (optional for production)" -ForegroundColor Yellow
}

# Port check
Write-Host "`n🔌 Checking Port Availability..." -ForegroundColor Cyan
$ports = @(80, 8000, 5173)
foreach ($port in $ports) {
    $connection = netstat -an | Select-String ":$port "
    if ($connection) {
        Write-Host "  ⚠️  Port $port is in use" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ Port $port is available" -ForegroundColor Green
    }
}

Write-Host ""
if ($errors.Count -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
} else {
    Write-Host "⚠️  $($errors.Count) issues found:" -ForegroundColor Yellow
    foreach ($err in $errors) {
        Write-Host "  - $err" -ForegroundColor Yellow
    }
}
