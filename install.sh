#!/bin/bash
# Install the `logos` CLI to ~/.local/bin (no sudo required)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
TARGET="$INSTALL_DIR/logos"

mkdir -p "$INSTALL_DIR"
chmod +x "$SCRIPT_DIR/bin/logos"
ln -sf "$SCRIPT_DIR/bin/logos" "$TARGET"
echo "Installed logos CLI → $TARGET"

# Warn if ~/.local/bin is not in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  echo ""
  echo "NOTE: Add this to your ~/.zshrc (or ~/.bashrc):"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo "Then run: source ~/.zshrc"
fi

echo ""
echo "Done. Run: logos --dangerously-skip-permissions"
