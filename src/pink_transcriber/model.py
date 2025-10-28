"""
Model loading and transcription logic.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

DEV_MODE = os.getenv('DEV') == '1'

_model: Optional[Any] = None
_device: Optional[str] = None


def load_model(project_root: Path) -> None:
    """Load Parakeet TDT v3 model with MPS support."""
    global _model, _device

    # Set cache directory BEFORE any imports (portable)
    model_cache_dir = project_root / "models"
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
        if DEV_MODE:
            print("Loading Parakeet TDT v3 model...", flush=True)
        else:
            print("Loading model...")

        _model = nemo_asr.models.ASRModel.from_pretrained(
            "nvidia/parakeet-tdt-0.6b-v3"
        )

        # Use MPS (Metal) if available, otherwise CPU
        if torch.backends.mps.is_available():
            try:
                _model = _model.to('mps')
                _device = 'MPS'
            except Exception:
                _model = _model.to('cpu')
                _device = 'CPU'
        else:
            _model = _model.to('cpu')
            _device = 'CPU'

        if DEV_MODE:
            print(f"✓ Model loaded on {_device}", flush=True)

    except ImportError as e:
        print(f"Failed to import dependencies: {e}", file=sys.stderr)
        print("Please install: pip install nemo_toolkit[asr] torch soundfile", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load model: {e}", file=sys.stderr)
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
