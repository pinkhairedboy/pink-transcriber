"""Configuration and constants for pink-transcriber."""

import os
from pathlib import Path

# Socket path for Unix domain socket
SOCKET_PATH = Path("/tmp/pink-transcriber.sock")

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = frozenset({
    '.aiff', '.flac', '.m4a', '.mp3', '.ogg', '.opus', '.wav'
})

# Verbose mode flag (enable detailed logging)
VERBOSE_MODE = os.getenv('VERBOSE') == '1'

# Process identifiers for singleton detection
SINGLETON_IDENTIFIERS = ['pink-transcriber', 'pink_transcriber', 'Pink Transcriber']

# Legacy: support DEV=1 for backward compatibility
if os.getenv('DEV') == '1':
    VERBOSE_MODE = True


def get_model_cache_dir() -> Path:
    """
    Get model cache directory path.

    Priority:
    1. PINK_TRANSCRIBER_MODEL_DIR environment variable
    2. Package directory (./models/) if writable
    3. Fallback: ~/.local/share/pink-transcriber/models
    """
    # 1. Environment override
    if custom := os.getenv('PINK_TRANSCRIBER_MODEL_DIR'):
        custom_path = Path(custom)
        custom_path.mkdir(parents=True, exist_ok=True)
        return custom_path

    # 2. Package location (works for editable installs with -e flag)
    package_dir = Path(__file__).resolve().parent.parent.parent
    models_dir = package_dir / "models"

    # Test if writable
    try:
        models_dir.mkdir(exist_ok=True)
        test_file = models_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return models_dir
    except (PermissionError, OSError):
        pass

    # 3. Fallback: user data directory
    user_data = Path.home() / ".local" / "share" / "pink-transcriber" / "models"
    user_data.mkdir(parents=True, exist_ok=True)
    return user_data
