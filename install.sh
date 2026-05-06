#!/bin/bash
# Install the `logos` CLI — supports macOS and Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
TARGET="$INSTALL_DIR/logos"

# Detect OS
OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM="macOS" ;;
  Linux)  PLATFORM="Linux" ;;
  *)
    echo "ERROR: Unsupported platform: $OS"
    exit 1
    ;;
esac

echo "Detected platform: $PLATFORM"

# Check Python 3
if ! command -v python3 &>/dev/null; then
  echo ""
  echo "ERROR: python3 is required but not found."
  case "$PLATFORM" in
    macOS) echo "Install it with: brew install python" ;;
    Linux) echo "Install it with: sudo apt install python3  (or your distro's equivalent)" ;;
  esac
  exit 1
fi

# Check Docker
if ! command -v docker &>/dev/null; then
  echo ""
  echo "WARNING: Docker not found."
  case "$PLATFORM" in
    macOS) echo "Install Docker Desktop: https://www.docker.com/products/docker-desktop/" ;;
    Linux) echo "Install Docker: https://docs.docker.com/engine/install/" ;;
  esac
fi

# Install CLI
mkdir -p "$INSTALL_DIR"
chmod +x "$SCRIPT_DIR/bin/logos"
ln -sf "$SCRIPT_DIR/bin/logos" "$TARGET"
echo "Installed logos CLI → $TARGET"

# Detect shell rc file
detect_rc() {
  if [[ -n "$ZSH_VERSION" ]] || [[ "$SHELL" == */zsh ]]; then
    echo "$HOME/.zshrc"
  elif [[ -n "$BASH_VERSION" ]] || [[ "$SHELL" == */bash ]]; then
    if [[ "$PLATFORM" == "macOS" ]]; then
      echo "$HOME/.bash_profile"
    else
      echo "$HOME/.bashrc"
    fi
  else
    echo "$HOME/.profile"
  fi
}

RC_FILE="$(detect_rc)"

# Warn if ~/.local/bin is not in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  echo ""
  echo "NOTE: Add ~/.local/bin to your PATH."
  echo "  Run this once:"
  echo ""
  echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> $RC_FILE && source $RC_FILE"
  echo ""
fi

echo ""
echo "Done. Run: logos --dangerously-skip-permissions"
