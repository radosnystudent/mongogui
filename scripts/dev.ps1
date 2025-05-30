# PowerShell script for MongoDB GUI project development tasks

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  install        Install production dependencies" -ForegroundColor Cyan
    Write-Host "  install-dev    Install development dependencies" -ForegroundColor Cyan
    Write-Host "  format         Format code with Black" -ForegroundColor Cyan
    Write-Host "  format-check   Check code formatting with Black" -ForegroundColor Cyan
    Write-Host "  lint           Lint code with Ruff" -ForegroundColor Cyan
    Write-Host "  lint-fix       Lint and fix code with Ruff" -ForegroundColor Cyan
    Write-Host "  type-check     Run type checking with Mypy" -ForegroundColor Cyan
    Write-Host "  security       Run security checks with Bandit" -ForegroundColor Cyan
    Write-Host "  test           Run tests with pytest" -ForegroundColor Cyan
    Write-Host "  test-cov       Run tests with coverage" -ForegroundColor Cyan
    Write-Host "  build          Build the package" -ForegroundColor Cyan
    Write-Host "  clean          Clean build artifacts" -ForegroundColor Cyan
    Write-Host "  all            Run all checks" -ForegroundColor Cyan
    Write-Host "  dev-setup      Set up development environment" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\dev.ps1 <command>" -ForegroundColor Yellow
}

function Install-Prod {
    Write-Host "Installing production dependencies..." -ForegroundColor Green
    pip install -r requirements.txt
}

function Install-Dev {
    Write-Host "Installing development dependencies..." -ForegroundColor Green
    pip install -r requirements.txt -r requirements-dev.txt
}

function Format-Code {
    Write-Host "Formatting code with Black..." -ForegroundColor Green
    black .
}

function Check-Format {
    Write-Host "Checking code formatting with Black..." -ForegroundColor Green
    black --check .
}

function Lint-Code {
    Write-Host "Linting code with Ruff..." -ForegroundColor Green
    ruff check .
}

function Lint-Fix {
    Write-Host "Linting and fixing code with Ruff..." -ForegroundColor Green
    ruff check --fix .
}

function Type-Check {
    Write-Host "Running type checking with Mypy..." -ForegroundColor Green
    mypy .
}

function Security-Check {
    Write-Host "Running security checks with Bandit..." -ForegroundColor Green
    bandit -r . -f json -o bandit-report.json
    bandit -r .
}

function Run-Tests {
    Write-Host "Running tests with pytest..." -ForegroundColor Green
    pytest
}

function Run-Tests-Cov {
    Write-Host "Running tests with coverage..." -ForegroundColor Green
    pytest --cov=. --cov-report=html --cov-report=term
}

function Build-Package {
    Write-Host "Building package..." -ForegroundColor Green
    python -m build
}

function Clean-Artifacts {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Green
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force "*.egg-info" }
    if (Test-Path ".mypy_cache") { Remove-Item -Recurse -Force ".mypy_cache" }
    if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }
    if (Test-Path ".ruff_cache") { Remove-Item -Recurse -Force ".ruff_cache" }
    if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }
    if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
    if (Test-Path "bandit-report.json") { Remove-Item -Force "bandit-report.json" }
}

function Run-All {
    Write-Host "Running all checks..." -ForegroundColor Green
    Format-Code
    Lint-Code
    Type-Check
    Security-Check
    Run-Tests
}

function Dev-Setup {
    Write-Host "Setting up development environment..." -ForegroundColor Green
    Install-Dev
    Write-Host "Development environment setup complete!" -ForegroundColor Green
    Write-Host "Run '.\dev.ps1 help' to see available commands." -ForegroundColor Yellow
}

# Update python version check or shebang if present

switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Prod }
    "install-dev" { Install-Dev }
    "format" { Format-Code }
    "format-check" { Check-Format }
    "lint" { Lint-Code }
    "lint-fix" { Lint-Fix }
    "type-check" { Type-Check }
    "security" { Security-Check }
    "test" { Run-Tests }
    "test-cov" { Run-Tests-Cov }
    "build" { Build-Package }
    "clean" { Clean-Artifacts }
    "all" { Run-All }
    "dev-setup" { Dev-Setup }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
