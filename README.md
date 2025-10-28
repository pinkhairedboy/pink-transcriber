# Pink Transcriber

Local voice transcription daemon for macOS. Transcribes audio files through Unix socket using Parakeet TDT 0.6B v3 model running on Apple Silicon.

Processes audio ~15x faster than realtime (60 sec file in ~4 sec).

## How it works

Server runs as background daemon (LaunchAgent), loads ML model into RAM (~2GB), listens on Unix socket. Client CLI connects to socket, sends file path, receives transcribed text.

## Requirements

- macOS 12+ with Apple Silicon (M1-M5)
- Python 3.12
- ffmpeg

## Installation

```bash
./install.sh
```

This will:
- Download Parakeet model (~3GB)
- Install dependencies
- Create global `pink-transcriber` command
- Install LaunchAgent (auto-start on boot)

## Usage

```bash
pink-transcriber voice.ogg
# Outputs transcribed text to stdout

pink-transcriber --health
# Checks if daemon is running
```

Supported formats: wav, ogg, mp3, m4a, flac, opus, aiff

## Development

```bash
./dev.sh         # Run server in terminal with verbose logging
./uninstall.sh   # Remove LaunchAgent and global command
```

## Architecture

- `src/pink_transcriber/server.py` - Main daemon entry point and coordination
- `src/pink_transcriber/model.py` - Model loading and transcription
- `src/pink_transcriber/worker.py` - Async queue and client handler
- `src/pink_transcriber/client.py` - CLI that connects to socket
- Socket: `pink-transcriber.sock` in project directory
- LaunchAgent: `~/Library/LaunchAgents/com.pink.transcriber.plist`
