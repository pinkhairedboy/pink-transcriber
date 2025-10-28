#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Pink Transcriber (Dev Mode)"
echo ""

# Check venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: venv not found"
    echo "Run: ./install.sh first"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Start server in dev mode
echo "Starting server with verbose logging..."
echo "Press Ctrl+C to stop"
echo ""

DEV=1 python -m pink_transcriber.server
