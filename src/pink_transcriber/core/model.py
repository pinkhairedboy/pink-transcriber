"""
Model loading and transcription logic.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

from pink_transcriber.config import VERBOSE_MODE, get_model_cache_dir

_model: Optional[Any] = None
_device: Optional[str] = None


def load_model() -> None:
    """Load Parakeet TDT v3 model with MPS support."""
    global _model, _device

    # Set cache directory BEFORE any imports (portable)
    model_cache_dir = get_model_cache_dir()
    model_cache_dir.mkdir(exist_ok=True)

    # Configure all cache paths
    os.environ['NEMO_CACHE_DIR'] = str(model_cache_dir)
    os.environ['HF_HOME'] = str(model_cache_dir / "huggingface")
    os.environ['NEMO_LOG_LEVEL'] = 'CRITICAL'
    os.environ['HYDRA_FULL_ERROR'] = '0'
    os.environ['PYTHONWARNINGS'] = 'ignore'

    try:
        import nemo.collections.asr as nemo_asr
        import torch
        import logging

        # Suppress all NeMo loggers
        logging.getLogger('nemo_logger').setLevel(logging.CRITICAL)
        logging.getLogger('nemo').setLevel(logging.CRITICAL)
        logging.getLogger('pytorch_lightning').setLevel(logging.CRITICAL)
        logging.getLogger('lightning').setLevel(logging.CRITICAL)
        logging.getLogger('lightning.pytorch').setLevel(logging.CRITICAL)

        # Load model
        if VERBOSE_MODE:
            print("Loading Parakeet TDT v3 model...", flush=True)

        _model = nemo_asr.models.ASRModel.from_pretrained(
            "nvidia/parakeet-tdt-0.6b-v3"
        )

        # Use CUDA if available, then MPS (Metal), otherwise CPU
        if torch.cuda.is_available():
            try:
                _model = _model.to('cuda')
                _device = 'CUDA'
            except Exception:
                _model = _model.to('cpu')
                _device = 'CPU'
        elif torch.backends.mps.is_available():
            try:
                _model = _model.to('mps')
                _device = 'MPS'
            except Exception:
                _model = _model.to('cpu')
                _device = 'CPU'
        else:
            _model = _model.to('cpu')
            _device = 'CPU'

        if VERBOSE_MODE:
            print(f"✓ Model loaded on {_device}", flush=True)

    except ImportError as e:
        print("\n" + "="*60, file=sys.stderr)
        print("ERROR: Missing dependencies", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"\n{e}\n", file=sys.stderr)
        print("This usually means pink-transcriber was not installed correctly.", file=sys.stderr)
        print("\nPlease reinstall using the correct method:", file=sys.stderr)
        print("  1. cd /path/to/pink-transcriber", file=sys.stderr)
        print("  2. uv tool install -e . --python python3.12", file=sys.stderr)
        print("\nNote: Only editable installation (-e flag) is supported.", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("\n" + "="*60, file=sys.stderr)
        print("ERROR: Failed to load model", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"\n{e}\n", file=sys.stderr)
        print("Possible causes:", file=sys.stderr)
        print("  - Insufficient memory (model requires ~2GB RAM)", file=sys.stderr)
        print("  - Incompatible Python version (requires Python 3.12)", file=sys.stderr)
        print("  - Network issues during model download", file=sys.stderr)
        print("\nIf problem persists, try:", file=sys.stderr)
        print("  - Delete ./models/ directory and restart server", file=sys.stderr)
        print("  - Check system resources with Activity Monitor", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        sys.exit(1)


def transcribe(audio_path: str) -> str:
    """Transcribe audio file to text."""
    if _model is None:
        raise RuntimeError("Model not loaded")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        # Suppress stdout/stderr during transcription
        old_stdout_fd = os.dup(1)
        old_stderr_fd = os.dup(2)
        devnull_fd = os.open(os.devnull, os.O_WRONLY)

        try:
            os.dup2(devnull_fd, 1)
            os.dup2(devnull_fd, 2)

            result = _model.transcribe([audio_path], verbose=False, batch_size=1)

        finally:
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(devnull_fd)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)

        # Extract text from result
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            if hasattr(first_result, 'text'):
                return first_result.text
            else:
                return str(first_result)
        else:
            return str(result) if result else ""

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")


def get_device() -> str:
    """Get current device name."""
    return _device or "Unknown"


def is_loaded() -> bool:
    """Check if model is loaded and ready."""
    return _model is not None
