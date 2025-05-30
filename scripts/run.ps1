# PowerShell script to run the MongoDB GUI application

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
try {
    python -c "import PyQt5; import pymongo; import keyring" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies not found"
    }
} catch {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Run the application
Write-Host "Starting MongoDB GUI..." -ForegroundColor Green
python main.py
