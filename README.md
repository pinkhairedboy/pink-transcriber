# Pink Transcriber

Local voice transcription server for macOS. Transcribes audio files through Unix socket using Parakeet TDT 0.6B v3 model running on Apple Silicon.

Processes audio ~15x faster than realtime on M4 Pro (60 sec file in ~4 sec).

## Requirements

- macOS 12+ with Apple Silicon (M1-M5)
- Python 3.12
- ffmpeg
- uv

## Install

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pink-transcriber
uv tool install -e . --python python3.12
```

First run downloads model (~2.4GB) to `./models/` in project directory.

## Run Server

From anywhere:

```bash
pink-transcriber-server

# Dev mode (verbose logging)
DEV=1 pink-transcriber-server
```

Server loads model into RAM (~2GB) and listens on Unix socket `/tmp/pink-transcriber.sock`.

**Note:** First run after installation is slower (Python compiles dependencies). Subsequent runs are faster.

## Use Client

From anywhere:

```bash
pink-transcriber voice.ogg
pink-transcriber --health
```

Supported formats: wav, ogg, mp3, m4a, flac, opus, aiff

## Architecture

- `src/pink_transcriber/server.py` - Main entry point and coordination
- `src/pink_transcriber/model.py` - Model loading and transcription
- `src/pink_transcriber/worker.py` - Async queue and client handler
- `src/pink_transcriber/client.py` - CLI that connects to socket
