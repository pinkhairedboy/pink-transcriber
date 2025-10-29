#!/usr/bin/env python3
"""
Pink Transcriber Server
Main entry point - sets up Unix socket server and coordinates model/workers.
"""

from __future__ import annotations

# Set process title early
try:
    import setproctitle
    setproctitle.setproctitle('Pink Transcriber')
except ImportError:
    pass

import os
import asyncio
import signal
from pathlib import Path
from typing import Any

from . import model, worker

DEV_MODE = os.getenv('DEV') == '1'


async def main() -> None:
    """Main server loop."""
    # Dev mode header
    if DEV_MODE:
        print("\n" + "="*50, flush=True)
        print("   Pink Transcriber - Voice Transcription Server", flush=True)
        print("="*50, flush=True)
        print("", flush=True)

    # Models in project directory (editable install keeps code in place)
    # Socket in /tmp for global access
    project_root = Path(__file__).resolve().parent.parent.parent
    socket_path = Path("/tmp/pink-transcriber.sock")

    # Remove old socket if exists
    if socket_path.exists():
        socket_path.unlink()

    # Load model before starting server
    model.load_model(project_root)

    # Create transcription queue
    queue = asyncio.Queue()

    # Start transcription worker
    worker_task = asyncio.create_task(worker.transcription_worker(queue))

    # Create Unix socket server
    async def client_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await worker.handle_client(reader, writer, queue)

    server = await asyncio.start_unix_server(client_handler, path=str(socket_path))

    if DEV_MODE:
        print(f"✓ Server listening on Unix socket", flush=True)
        print(f"  Socket: {socket_path}", flush=True)
        print(f"  Device: {model.get_device()}", flush=True)
        print("", flush=True)
        print("Ready to accept requests. Press Ctrl+C to stop.", flush=True)
        print("", flush=True)
    else:
        print(f"Ready ({model.get_device()})", flush=True)

    # Shutdown flag
    shutdown_event = asyncio.Event()
    loop = asyncio.get_event_loop()

    # Handle shutdown gracefully
    def signal_handler(sig: int, frame: Any) -> None:
        if DEV_MODE:
            print("\n\nShutting down gracefully...", flush=True)
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run until shutdown signal
        await shutdown_event.wait()

        # Stop worker with sentinel
        await queue.put(None)
        try:
            await asyncio.wait_for(worker_task, timeout=2.0)
        except asyncio.TimeoutError:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

        # Stop accepting new connections
        server.close()
        await server.wait_closed()

        # Remove socket
        if socket_path.exists():
            socket_path.unlink()

        if DEV_MODE:
            print("✓ Server stopped", flush=True)

    except Exception as e:
        if DEV_MODE:
            print(f"✗ Error during shutdown: {e}", flush=True)
        # Clean up socket anyway
        if socket_path.exists():
            socket_path.unlink()
        raise


def cli_main() -> None:
    """CLI entry point wrapper."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
