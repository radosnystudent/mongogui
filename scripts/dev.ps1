# PowerShell script for MongoDB GUI project development tasks

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Get-Help {
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
    Write-Host "  all-checks     Run lint, mypy, format-check, sonar, and tests" -ForegroundColor Cyan
    Write-Host "  dev-setup      Set up development environment" -ForegroundColor Cyan
    Write-Host "  sonar          Run SonarQube static analysis" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\dev.ps1 <command>" -ForegroundColor Yellow
}

function Install-ProductionDependencies {
    Write-Host "Installing production dependencies..." -ForegroundColor Green
    pip install -r requirements.txt
}

function Install-DevelopmentDependencies {
    Write-Host "Installing development dependencies..." -ForegroundColor Green
    pip install -r requirements.txt -r requirements-dev.txt
}

function Format-Code {
    Write-Host "Formatting code with Black..." -ForegroundColor Green
    black .
}

function Test-Format {
    Write-Host "Checking code formatting with Black..." -ForegroundColor Green
    black --check .
}

function Invoke-Lint {
    Write-Host "Linting code with Ruff..." -ForegroundColor Green
    ruff check .
}

function Invoke-LintFix {
    Write-Host "Linting and fixing code with Ruff..." -ForegroundColor Green
    ruff check --fix .
}

function Test-Type {
    Write-Host "Running type checking with Mypy..." -ForegroundColor Green
    mypy .
}

function Test-Security {
    Write-Host "Running security checks with Bandit..." -ForegroundColor Green
    bandit -r . -f json -o bandit-report.json
    bandit -r .
}

function Test-Unit {
    Write-Host "Running tests with pytest..." -ForegroundColor Green
    pytest
}

function Test-CodeCoverage {
    Write-Host "Running tests with coverage..." -ForegroundColor Green
    pytest --cov=. --cov-report=html --cov-report=term
}

function New-Package {
    Write-Host "Building package..." -ForegroundColor Green
    python -m build
}

function Remove-BuildArtifacts {
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

function Invoke-All {
    Write-Host "Running all checks..." -ForegroundColor Green
    Format-Code
    Invoke-Lint
    Test-Type
    Test-Security
    Test-Unit
}

function Invoke-AllChecks {
    Write-Host "Running all static checks and tests..." -ForegroundColor Green
    Invoke-Lint
    Test-Type
    Test-Format
    Invoke-SonarCheck
    Test-Unit
}

function Initialize-DevelopmentEnvironment {
    Write-Host "Setting up development environment..." -ForegroundColor Green
    Install-DevelopmentDependencies
    Write-Host "Development environment setup complete!" -ForegroundColor Green
    Write-Host "Run '.\dev.ps1 help' to see available commands." -ForegroundColor Yellow
}

function Invoke-SonarCheck {
    Write-Host "Running SonarQube static analysis..." -ForegroundColor Green
    # Try sonar-scanner (Unix/WSL) or sonar-scanner.bat (Windows)
    $scanner = $null
    if (Get-Command sonar-scanner -ErrorAction SilentlyContinue) {
        $scanner = "sonar-scanner"
    } elseif (Get-Command sonar-scanner.bat -ErrorAction SilentlyContinue) {
        $scanner = "sonar-scanner.bat"
    }
    if ($scanner) {
        & $scanner
    } else {
        Write-Host "sonar-scanner not found. Please install SonarQube Scanner CLI and ensure 'sonar-scanner' or 'sonar-scanner.bat' is in your PATH. Also configure sonar-project.properties in the project root." -ForegroundColor Yellow
        Write-Host "Download: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner-cli/" -ForegroundColor Yellow
    }
}

# Update python version check or shebang if present

switch ($Command.ToLower()) {
    "help" { Get-Help }
    "install" { Install-ProductionDependencies }
    "install-dev" { Install-DevelopmentDependencies }
    "format" { Format-Code }
    "format-check" { Test-Format }
    "lint" { Invoke-Lint }
    "lint-fix" { Invoke-LintFix }
    "type-check" { Test-Type }
    "security" { Test-Security }
    "test" { Test-Unit }
    "test-cov" { Test-CodeCoverage }
    "build" { New-Package }
    "clean" { Remove-BuildArtifacts }
    "all" { Invoke-All }
    "all-checks" { Invoke-AllChecks }
    "dev-setup" { Initialize-DevelopmentEnvironment }
    "sonar" { Invoke-SonarCheck }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Get-Help 
    }
}
