#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_DEST="$HOME/Library/LaunchAgents/com.pink.transcriber.plist"

echo "Uninstalling pink-transcriber LaunchAgent"
echo ""

if [ ! -f "$PLIST_DEST" ]; then
    echo "Service not installed"
    exit 0
fi

# Unload the service
echo "Stopping service..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Remove plist file
echo "Removing configuration..."
rm "$PLIST_DEST"

# Remove global symlink if exists
if [ -L "/usr/local/bin/pink-transcriber" ]; then
    echo "Removing global CLI symlink (requires sudo)..."
    sudo rm /usr/local/bin/pink-transcriber 2>/dev/null || true
fi

echo ""
echo "✓ Service uninstalled successfully"
echo ""
echo "To completely remove pink-transcriber:"
echo "  1. Delete this directory: $SCRIPT_DIR"
echo "  2. Optional: Clean logs if any"
echo ""
echo "Note: Models cache (~4.7GB) is in: $SCRIPT_DIR/models/"
echo ""
