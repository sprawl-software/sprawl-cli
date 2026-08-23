#!/usr/bin/env bash
# Sprawl CLI — Production Installer
# ============================================================
# Features:
#   - Architecture detection (x86_64, ARM64/aarch64)
#   - Python version pinning (>= 3.10 required)
#   - SHA256 checksum verification for GitHub release archives
#   - Multi-OS package manager detection (apt, brew, dnf, pacman)
#   - Idempotent: safe to run multiple times
# ============================================================

set -euo pipefail

# ------------------------------------
# Terminal Color Constants
# ------------------------------------
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log_info()    { echo -e "${CYAN}[*]${NC} $*"; }
log_success() { echo -e "${GREEN}[✔]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
log_error()   { echo -e "${RED}[✗]${NC} $*" >&2; }
log_fatal()   { log_error "$*"; exit 1; }

# Temp folder cleanup trap
TMPDIR=""
cleanup() {
    if [ -n "${TMPDIR}" ] && [ -d "${TMPDIR}" ]; then
        rm -rf "${TMPDIR}"
    fi
}
trap cleanup EXIT

# ------------------------------------
# Version Pins
# ------------------------------------
SPRAWL_MIN_PYTHON_MAJOR=3
SPRAWL_MIN_PYTHON_MINOR=10
SPRAWL_GITHUB_REPO="sprawl-software/sprawl-cli"
# Optional: pin to a specific tag (set to "" to always use latest)
SPRAWL_VERSION="${SPRAWL_VERSION:-}"

# ------------------------------------
# Banner
# ------------------------------------
echo -e "${CYAN}"
echo -e "//===================================================================//"
echo -e "//   _____ ____  ____  ___ _       ____                 ___          //"
echo -e "//  / ___// __ \\/ __ \\/   | |     / / /           _____/ (_)         //"
echo -e "//  \\__ \\/ /_/ / /_/ / /| | | /| / / /           / ___/ / /          //"
echo -e "// ___/ / ____/ _, _/ ___ | |/ |/ / /___   _    / /__/ / /           //"
echo -e "//  /____/_/   /_/ |_/_/  |_|__/|__/_____/  (_)   \\___/_/_/          //"
echo -e "//                                                                   //"
echo -e "//  [ OS: BrainBlend AI // FRAMEWORK: Atomic Agentic Fabric ]        //"
echo -e "//  [ ARCHITECT: Younes_Baghor // INSTALLER: v2.0.3          ]       //"
echo -e "//===================================================================//${NC}"
echo ""

# ------------------------------------
# 1. Architecture Detection
# ------------------------------------
ARCH="$(uname -m)"
log_info "Detected architecture: ${BOLD}${ARCH}${NC}"

case "${ARCH}" in
    x86_64)
        ARCH_LABEL="amd64"
        ;;
    aarch64 | arm64)
        ARCH_LABEL="arm64"
        log_info "ARM64 architecture confirmed. Sprawl is fully supported on ARM64."
        ;;
    armv7l | armv6l)
        log_warn "32-bit ARM detected (${ARCH}). Some optional native extensions may not be available."
        ARCH_LABEL="armhf"
        ;;
    *)
        log_warn "Unknown architecture: ${ARCH}. Proceeding with generic install — report issues at https://github.com/${SPRAWL_GITHUB_REPO}/issues"
        ARCH_LABEL="unknown"
        ;;
esac

# ------------------------------------
# 2. OS Detection
# ------------------------------------
OS="$(uname -s)"
log_info "Detected OS: ${BOLD}${OS}${NC}"

# ------------------------------------
# 3. Python Version Pinning
# ------------------------------------
log_info "Verifying Python version (requires ${SPRAWL_MIN_PYTHON_MAJOR}.${SPRAWL_MIN_PYTHON_MINOR}+)..."

if ! command -v python3 &>/dev/null; then
    log_fatal "python3 not found. Sprawl requires Python ${SPRAWL_MIN_PYTHON_MAJOR}.${SPRAWL_MIN_PYTHON_MINOR}+. Please install it and retry."
fi

PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PY_VERSION="${PY_MAJOR}.${PY_MINOR}"

if [ "${PY_MAJOR}" -lt "${SPRAWL_MIN_PYTHON_MAJOR}" ] || \
   ([ "${PY_MAJOR}" -eq "${SPRAWL_MIN_PYTHON_MAJOR}" ] && [ "${PY_MINOR}" -lt "${SPRAWL_MIN_PYTHON_MINOR}" ]); then
    log_fatal "Python ${PY_VERSION} found, but Sprawl requires Python >= ${SPRAWL_MIN_PYTHON_MAJOR}.${SPRAWL_MIN_PYTHON_MINOR}. Please upgrade Python."
fi

log_success "Python ${PY_VERSION} OK."

# ------------------------------------
# 4. pipx Verification / Installation
# ------------------------------------
prompt_sudo() {
    log_warn "Installing 'pipx' requires root privileges (sudo)."
    if [ -t 0 ]; then
        read -p "Allow installation via sudo? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_fatal "Root permission denied. Please install 'pipx' manually and rerun the installer."
        fi
    else
        log_info "Piped install detected — executing sudo command..."
    fi
}

if ! command -v pipx &>/dev/null; then
    log_warn "'pipx' not found. Attempting automatic installation..."

    if command -v apt-get &>/dev/null; then
        log_info "Detected Debian/Ubuntu — using apt-get..."
        prompt_sudo
        sudo apt-get update -qq && sudo apt-get install -y pipx
    elif command -v brew &>/dev/null; then
        log_info "Detected macOS/Homebrew — using brew..."
        brew install pipx
    elif command -v dnf &>/dev/null; then
        log_info "Detected Fedora — using dnf..."
        prompt_sudo
        sudo dnf install -y pipx
    elif command -v pacman &>/dev/null; then
        log_info "Detected Arch Linux — using pacman..."
        prompt_sudo
        sudo pacman -S --noconfirm python-pipx
    else
        log_warn "No compatible package manager detected. Falling back to pip user install..."
        python3 -m pip install --user pipx
    fi

    python3 -m pipx ensurepath
    export PATH="${PATH}:${HOME}/.local/bin"
fi

log_success "pipx is active."

# ------------------------------------
# 5. Checksum Verification Helper
# ------------------------------------
verify_checksum() {
    local file="$1"
    local expected_sha256="$2"

    if [ -z "${expected_sha256}" ]; then
        log_warn "No checksum provided for ${file} — skipping verification."
        return 0
    fi

    local actual=""
    if command -v sha256sum &>/dev/null; then
        actual=$(sha256sum "${file}" | awk '{print $1}')
    elif command -v shasum &>/dev/null; then
        actual=$(shasum -a 256 "${file}" | awk '{print $1}')
    else
        log_error "No sha256sum or shasum tool found to verify checksum!"
        log_fatal "Cannot guarantee archive integrity without verification tools. Please install sha256sum or shasum."
    fi

    if [ "${actual}" != "${expected_sha256}" ]; then
        log_fatal "CHECKSUM MISMATCH for ${file}!\n  Expected: ${expected_sha256}\n  Got:      ${actual}\nAborting install. The archive may be corrupted or tampered with."
    fi

    log_success "Checksum verified for ${file}."
}

# ------------------------------------
# 6. Install Sprawl CLI
# ------------------------------------
log_info "Starting Sprawl CLI installation..."

if [ -f "pyproject.toml" ] && grep -q 'name = "sprawl-cli"' pyproject.toml 2>/dev/null; then
    # Local development installation (repo cloned)
    log_info "Local repository detected — installing from source..."
    pipx install . --force
    log_success "Sprawl CLI installed from local source."

elif [ -n "${SPRAWL_VERSION}" ]; then
    # Validate version format to prevent path/URL injection
    if [[ ! "${SPRAWL_VERSION}" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
        log_fatal "Invalid version format: ${SPRAWL_VERSION}"
    fi

    log_info "Installing pinned version: ${BOLD}${SPRAWL_VERSION}${NC}..."
    ARCHIVE_URL="https://github.com/${SPRAWL_GITHUB_REPO}/archive/refs/tags/${SPRAWL_VERSION}.tar.gz"
    
    # Secure random temp directory creation (Symlink race prevention)
    TMPDIR="$(mktemp -d)"
    ARCHIVE_FILE="${TMPDIR}/sprawl-${SPRAWL_VERSION}.tar.gz"

    log_info "Downloading: ${ARCHIVE_URL}"
    if command -v curl &>/dev/null; then
        curl -fsSL "${ARCHIVE_URL}" -o "${ARCHIVE_FILE}"
    elif command -v wget &>/dev/null; then
        wget -q "${ARCHIVE_URL}" -O "${ARCHIVE_FILE}"
    else
        log_fatal "Neither curl nor wget found. Please install one and retry."
    fi

    # If a checksum env var is provided, verify it
    verify_checksum "${ARCHIVE_FILE}" "${SPRAWL_SHA256:-}"

    pipx install "${ARCHIVE_FILE}" --force
    log_success "Sprawl CLI ${SPRAWL_VERSION} installed from pinned release."

else
    log_info "Installing the latest version from GitHub main branch..."
    pipx install "git+https://github.com/${SPRAWL_GITHUB_REPO}.git" --force --pip-args="--no-cache-dir"
    log_success "Sprawl CLI installed from GitHub main branch."
fi

# ------------------------------------
# 7. Post-Installation Report
# ------------------------------------
echo ""
log_success "Installation Complete! ✨"
log_info "The 'sprawl' command is now globally available."
echo ""
echo -e "    ${YELLOW}IMPORTANT:${NC} You may need to restart your terminal or run:"
echo "       source ~/.bashrc  (or ~/.zshrc)"
echo ""
echo -e "    Architecture: ${BOLD}${ARCH}${NC} (${ARCH_LABEL})"
echo -e "    Python:       ${BOLD}${PY_VERSION}${NC}"
if command -v sprawl &>/dev/null; then
    INSTALLED_VER="$(sprawl --version 2>/dev/null | head -n 1 || echo "v2.0.3")"
    echo -e "    Engine:       ${BOLD}${INSTALLED_VER}${NC}"
else
    echo -e "    Engine:       ${BOLD}v2.0.3${NC}"
fi
echo ""
echo "    Then boot the engine with:"
echo "       sprawl --help"
echo "       sprawl doctor     # Validates environment health"
echo ""
