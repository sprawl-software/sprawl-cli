# Sprawl CLI — Windows PowerShell Production Installer
# ============================================================
# Features:
#   - Architecture detection (AMD64, ARM64, x86)
#   - Python version pinning (>= 3.10 required)
#   - Automated pipx bootstrapping and PATH check
#   - Idempotent: safe to run multiple times
# ============================================================

$ErrorActionPreference = "Stop"

# ------------------------------------
# Terminal Output Helpers
# ------------------------------------
function Write-Cyan($msg)    { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host "[✔] $msg" -ForegroundColor Green }
function Write-Warn($msg)    { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-ErrorMsg($msg){ Write-Host "[✗] $msg" -ForegroundColor Red }
function Write-Fatal($msg)   { Write-ErrorMsg $msg; exit 1 }

# ------------------------------------
# Configuration Pins
# ------------------------------------
$MinPythonMajor = 3
$MinPythonMinor = 10
$SprawlGithubRepo = "sprawl-software/sprawl-cli"
$SprawlVersion = $env:SPRAWL_VERSION
$SprawlBranch = if ($env:SPRAWL_BRANCH) { $env:SPRAWL_BRANCH } else { "main" }

# ------------------------------------
# Banner
# ------------------------------------
Write-Host "" -ForegroundColor Cyan
Write-Host "//===================================================================//" -ForegroundColor Cyan
Write-Host "//  SPRAWL.software v2.0.3 (Windows Native)                          //" -ForegroundColor Cyan
Write-Host "//   _____ ____  ____  ___ _       ____                 ___          //" -ForegroundColor Cyan
Write-Host "//  / ___// __ \/ __ \/   | |     / / /           _____/ (_)         //" -ForegroundColor Cyan
Write-Host "//  \__ \/ /_/ / /_/ / /| | | /| / / /           / ___/ / /          //" -ForegroundColor Cyan
Write-Host "// ___/ / ____/ _, _/ ___ | |/ |/ / /___   _    / /__/ / /           //" -ForegroundColor Cyan
Write-Host "///____/_/   /_/ |_/_/  |_|__/|__/_____/  (_)   \___/_/_/            //" -ForegroundColor Cyan
Write-Host "//                                                                   //" -ForegroundColor Cyan
Write-Host "// AI Governance // BSL 1.1 // Editor-agnostic // Zero dependencies  //" -ForegroundColor Cyan
Write-Host "//===================================================================//" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------
# 1. Architecture Detection
# ------------------------------------
$Arch = $env:PROCESSOR_ARCHITECTURE
Write-Cyan "Detected architecture: $Arch"

# ------------------------------------
# 2. Python Detection & Version Check
# ------------------------------------
Write-Cyan "Checking Python installation..."

$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Fatal "Python is not installed or not in PATH. Please install Python >= 3.10 from https://python.org or via 'winget install Python.Python.3.12'"
}

$PyVersionOutput = & $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
$PyParts = $PyVersionOutput.Trim().Split(".")
$PyMajor = [int]$PyParts[0]
$PyMinor = [int]$PyParts[1]

Write-Cyan "Detected Python version: $PyVersionOutput ($PythonCmd)"

if ($PyMajor -lt $MinPythonMajor -or ($PyMajor -eq $MinPythonMajor -and $PyMinor -lt $MinPythonMinor)) {
    Write-Fatal "Sprawl CLI requires Python >= $MinPythonMajor.$MinPythonMinor, found $PyVersionOutput. Please upgrade your Python installation."
}

Write-Success "Python $PyVersionOutput meets the minimum requirements (>= $MinPythonMajor.$MinPythonMinor)."

# ------------------------------------
# 3. Git Detection & Verification
# ------------------------------------
Write-Cyan "Checking Git installation..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fatal "Git is not installed or not in PATH. Please install Git via 'winget install Git.Git' or from https://git-scm.com"
}
Write-Success "Git is installed."

# ------------------------------------
# 4. Pipx Bootstrap & Verification
# ------------------------------------
Write-Cyan "Checking pipx..."

if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Warn "pipx is not installed. Bootstrapping pipx automatically via pip..."
    & $PythonCmd -m pip install --user --upgrade pipx
    & $PythonCmd -m pipx ensurepath
    Write-Success "pipx installed successfully."

    # Refresh PATH in current PowerShell session
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $env:Path = "$UserPath;$MachinePath"
} else {
    Write-Success "pipx is already installed."
}

# ------------------------------------
# 5. Install Sprawl CLI
# ------------------------------------
Write-Cyan "Starting Sprawl CLI installation..."

if ((Test-Path "pyproject.toml") -and (Get-Content "pyproject.toml" | Select-String 'name = "sprawl-cli"')) {
    Write-Cyan "Local repository detected — installing from source..."
    pipx install . --force
    Write-Success "Sprawl CLI installed from local source."
} elseif ($SprawlVersion) {
    Write-Cyan "Installing pinned version: $SprawlVersion..."
    $ArchiveUrl = "https://github.com/$SprawlGithubRepo/archive/refs/tags/$SprawlVersion.zip"
    $TempZip = Join-Path $env:TEMP "sprawl-$SprawlVersion.zip"
    Invoke-WebRequest -Uri $ArchiveUrl -OutFile $TempZip
    pipx install $TempZip --force
    Remove-Item $TempZip -Force -ErrorAction SilentlyContinue
    Write-Success "Sprawl CLI $SprawlVersion installed from pinned release."
} elseif ($SprawlBranch) {
    Write-Cyan "Installing from branch: $SprawlBranch..."
    pipx install "git+https://github.com/$SprawlGithubRepo.git@$SprawlBranch" --force --pip-args="--no-cache-dir"
    Write-Success "Sprawl CLI installed from branch $SprawlBranch."
} else {
    Write-Cyan "Installing latest version from GitHub main branch..."
    pipx install "git+https://github.com/$SprawlGithubRepo.git" --force --pip-args="--no-cache-dir"
    Write-Success "Sprawl CLI installed from GitHub main branch."
}

# ------------------------------------
# 6. Post-Installation Report
# ------------------------------------
Write-Host ""
Write-Success "Installation Complete! ✨"
Write-Cyan "The 'sprawl' command is now globally available on your system."
Write-Host ""
Write-Host "    IMPORTANT: You may need to restart your terminal if 'sprawl' is not immediately recognized." -ForegroundColor Yellow
Write-Host ""
Write-Host "    Architecture: $Arch"
Write-Host "    Python:       $PyVersionOutput"
Write-Host ""
Write-Host "    Boot the engine with:"
Write-Host "       sprawl --help"
Write-Host "       sprawl doctor     # Validates environment health"
Write-Host ""
