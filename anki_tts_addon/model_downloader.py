"""
On-demand downloader for the Piper TTS voice model.

The ONNX model (~60MB) is not bundled with the add-on to keep the package
small. Instead, it is downloaded from HuggingFace on first use and cached
in the voices/ directory alongside the bundled .onnx.json config.
"""

import os
import logging
import threading
import urllib.request
from typing import Optional, Callable

log = logging.getLogger(__name__)

MODEL_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/"
    "en/en_GB/alan/medium/en_GB-alan-medium.onnx"
)

_MIN_MODEL_SIZE = 1_000_000  # 1MB — reject truncated files

_download_lock = threading.Lock()


def format_progress(downloaded: int, total: int) -> str:
    """Format a human-readable download progress string."""
    mb_down = downloaded / 1_000_000
    if total > 0:
        mb_total = total / 1_000_000
        return f"Downloading voice model... {mb_down:.0f}/{mb_total:.0f} MB"
    return f"Downloading voice model... {mb_down:.0f} MB"


def _model_path() -> str:
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(addon_dir, "voices", "en_GB-alan-medium.onnx")


def is_model_available() -> bool:
    """Check if the ONNX model exists and isn't truncated."""
    path = _model_path()
    if not os.path.isfile(path):
        return False
    return os.path.getsize(path) > _MIN_MODEL_SIZE


def download_model(progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
    """Download the Piper voice model from HuggingFace.

    Args:
        progress_callback: Called with (bytes_downloaded, total_bytes) during
            download. total_bytes is 0 if the server doesn't send Content-Length.

    Returns:
        Path to the downloaded model file.

    Raises:
        OSError: On network or disk errors.
    """
    dest = _model_path()
    part = dest + ".part"
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    log.info("Downloading Piper voice model from %s", MODEL_URL)
    try:
        resp = urllib.request.urlopen(MODEL_URL, timeout=30)
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0

        with open(part, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total)

        if downloaded < _MIN_MODEL_SIZE:
            raise OSError(f"Downloaded file too small ({downloaded} bytes), expected >1MB")
        os.replace(part, dest)
        log.info("Voice model downloaded: %s (%d bytes)", dest, downloaded)
        return dest
    except BaseException:
        # Clean up partial file on any failure
        try:
            os.unlink(part)
        except OSError:
            pass
        raise


def ensure_model(progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
    """Thread-safe wrapper: download only if not already present.

    Returns the model path on success, None on failure.
    """
    if is_model_available():
        return _model_path()

    with _download_lock:
        # Re-check after acquiring lock — another thread may have finished
        if is_model_available():
            return _model_path()

        try:
            return download_model(progress_callback)
        except Exception as e:
            log.error("Model download failed: %s", e)
            return None
