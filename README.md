# Pink Transcriber

High-performance voice transcription for macOS using NVIDIA Parakeet TDT v3 model.

Processes audio ~15x faster than realtime on M4 Pro (60 sec file in ~4 sec).

## Features

- Fast local transcription (no API calls)
- Unix socket server/client architecture
- MPS (Metal) acceleration on Apple Silicon
- Automatic model caching
- Single instance enforcement

## Requirements

- macOS 12+ with Apple Silicon (M1-M5)
- Python 3.12
- uv package manager

## Installation

**IMPORTANT:** Only editable installation is supported.

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/pinkhairedboy/pink-transcriber
cd pink-transcriber

# Install in editable mode (required)
uv tool install -e . --python python3.12
```

First run downloads Parakeet TDT v3 model (~2.4GB) to `./models/` directory.

**Note:** First run is slower due to Python dependency compilation. Subsequent runs are fast.

## Usage

### Start Server

```bash
# Normal mode (production)
pink-transcriber-server

# Verbose mode (detailed logging)
VERBOSE=1 pink-transcriber-server
```

Server loads model into RAM (~2GB) and listens on `/tmp/pink-transcriber.sock`.

**Stop server:** Press `Ctrl+C` for graceful shutdown.

### Transcribe Audio

```bash
# Transcribe file
pink-transcriber /path/to/audio.ogg

# Check server health
pink-transcriber --health
```

Supported formats: wav, ogg, mp3, m4a, flac, opus, aiff

## Configuration

### Model Location

By default, models are stored in `./models/` (project directory).

To use custom location:
```bash
export PINK_TRANSCRIBER_MODEL_DIR=/custom/path
```

### Verbose Logging

Enable detailed logging for debugging:
```bash
VERBOSE=1 pink-transcriber-server
```

## Architecture

```
src/pink_transcriber/
├── cli/
│   ├── client.py          # CLI client
│   └── server.py          # Server entry point
├── core/
│   └── model.py          # Model loading & transcription
├── daemon/
│   ├── singleton.py      # Single instance enforcement
│   └── worker.py         # Request queue & handler
└── config.py             # Configuration
```

## License

MIT - see LICENSE file

## Author

[pinkhairedboy](https://github.com/pinkhairedboy)
