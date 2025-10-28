#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_DEST="$HOME/Library/LaunchAgents/com.pink.transcriber.plist"
PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"

echo "Installing Pink Transcriber"
echo ""

# Check Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "ERROR: Python 3.12 not found"
    echo "Install: brew install python@3.12"
    exit 1
fi

PYTHON_VERSION=$(python3.12 --version | grep -oE '3\.12\.[0-9]+')
if [ -z "$PYTHON_VERSION" ]; then
    echo "ERROR: python3.12 version check failed"
    exit 1
fi

echo "Using Python $PYTHON_VERSION"
echo ""

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate

if ! python -c "import pink_transcriber" &> /dev/null; then
    echo "Installing dependencies (first run, downloads ~3GB model)..."
    echo ""
    pip install --upgrade pip setuptools wheel -q
    pip install -e .
    echo ""
    echo "Dependencies installed"
    echo ""
fi

# Create global symlink
SYMLINK_TARGET="/usr/local/bin/pink-transcriber"
VENV_BIN="$SCRIPT_DIR/venv/bin/pink-transcriber"

if [ ! -L "$SYMLINK_TARGET" ] || [ "$(readlink "$SYMLINK_TARGET")" != "$VENV_BIN" ]; then
    echo "Creating global command 'pink-transcriber' (requires sudo)"
    sudo ln -sf "$VENV_BIN" "$SYMLINK_TARGET"
fi

# Create LaunchAgent
echo "Installing LaunchAgent..."
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_DEST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pink.transcriber</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>-m</string>
        <string>pink_transcriber.server</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/pink-transcriber.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/pink-transcriber.error.log</string>
</dict>
</plist>
EOF

# Unload if already loaded
if launchctl list | grep -q com.pink.transcriber; then
    echo "Stopping existing service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Load the service
echo "Starting service..."
launchctl load "$PLIST_DEST"

echo ""
echo "✓ Pink Transcriber installed"
echo ""
echo "Usage:"
echo "  pink-transcriber voice.ogg"
echo "  pink-transcriber --health"
echo ""
echo "Service commands:"
echo "  Status:    launchctl list | grep pink.transcriber"
echo "  Stop:      launchctl unload ~/Library/LaunchAgents/com.pink.transcriber.plist"
echo "  Start:     launchctl load ~/Library/LaunchAgents/com.pink.transcriber.plist"
echo "  Uninstall: ./uninstall.sh"
echo ""
