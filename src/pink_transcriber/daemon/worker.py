"""
Worker for handling transcription requests.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from dataclasses import dataclass

from pink_transcriber.config import VERBOSE_MODE
from pink_transcriber.core import model


@dataclass
class TranscriptionRequest:
    """Request for transcription."""
    audio_path: str
    result_future: asyncio.Future


async def transcription_worker(queue: asyncio.Queue[TranscriptionRequest]) -> None:
    """Process transcription requests from queue sequentially."""
    while True:
        try:
            request = await queue.get()

            # Sentinel value to stop worker
            if request is None:
                break

            try:
                # Run transcription in executor (blocking operation)
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(None, model.transcribe, request.audio_path)
                request.result_future.set_result(text)

            except Exception as e:
                request.result_future.set_exception(e)

            finally:
                queue.task_done()

        except asyncio.CancelledError:
            break
        except Exception:
            pass


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    queue: asyncio.Queue[TranscriptionRequest]
) -> None:
    """Handle incoming client connection."""
    start_time = time.time() if VERBOSE_MODE else None

    try:
        # Read command or audio file path from client
        data = await reader.readline()
        message = data.decode().strip()

        # Handle health check command
        if message == "HEALTH":
            if model.is_loaded():
                writer.write(b"OK\n")
            else:
                writer.write(b"LOADING\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Regular transcription request
        audio_path = message

        if not audio_path:
            error_msg = f"ERROR: No audio path provided\n".encode()
            writer.write(error_msg)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        if VERBOSE_MODE:
            filename = Path(audio_path).name
            print(f"→ Received request: {filename}", flush=True)

        # Create future for result
        result_future = asyncio.Future()

        # Add to queue
        request = TranscriptionRequest(audio_path=audio_path, result_future=result_future)
        await queue.put(request)

        # Wait for result from worker
        text = await result_future

        if VERBOSE_MODE:
            elapsed = time.time() - start_time
            print(f"✓ Transcribed in {elapsed:.2f}s: {text[:50]}...", flush=True)

        # Send result back to client
        response = text.encode() + b'\n'
        writer.write(response)
        await writer.drain()

    except (BrokenPipeError, ConnectionResetError):
        # Client disconnected - this is normal (e.g., healthcheck)
        pass

    except FileNotFoundError as e:
        if VERBOSE_MODE:
            print(f"✗ File not found: {str(e)}", flush=True)
        try:
            error_msg = f"ERROR: {str(e)}\n".encode()
            writer.write(error_msg)
            await writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass

    except Exception as e:
        if VERBOSE_MODE:
            print(f"✗ Error: {str(e)}", flush=True)
        try:
            error_msg = f"ERROR: {str(e)}\n".encode()
            writer.write(error_msg)
            await writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass

    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except (BrokenPipeError, ConnectionResetError):
            pass
