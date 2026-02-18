"""
TTS engine for the Anki TTS add-on.
Three-tier fallback: Edge TTS (online) -> Piper (offline, bundled) -> system TTS.
Piper voice model is bundled in voices/, dependencies in vendor/.
Edge TTS is bundled in vendor/ and imported directly.
"""

import os
import sys
import subprocess
import tempfile
import threading
import logging
import platform
import wave
from typing import Optional, Callable

log = logging.getLogger(__name__)

# Status callback — set by __init__.py to show tooltips to the user
_status_callback: Optional[Callable[[str], None]] = None
_edge_import_error: Optional[Exception] = None


def set_status_callback(cb: Callable[[str], None]):
    global _status_callback
    _status_callback = cb


def _notify(msg: str):
    log.info(msg)
    if _status_callback:
        _status_callback(msg)


def _edge_error_reason(exc: Exception) -> str:
    """Return a short user-facing reason for Edge TTS failure."""
    if isinstance(exc, ModuleNotFoundError):
        missing = exc.name or "dependency"
        return f"missing module: {missing}"

    msg = str(exc).strip()
    low = msg.lower()
    if "certificate verify failed" in low or "ssl" in low:
        return "TLS/certificate error"
    if (
        "cannot connect" in low
        or "name or service not known" in low
        or "temporary failure in name resolution" in low
        or "connection reset" in low
        or "connection refused" in low
    ):
        return "network connection failed"
    if msg:
        return msg.splitlines()[0][:120]
    return exc.__class__.__name__


def _notify_edge_unavailable(exc: Exception):
    _notify(
        f"Edge TTS unavailable ({_edge_error_reason(exc)}) — using offline voice"
    )


def _addon_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _vendor_dir() -> str:
    d = os.path.join(_addon_dir(), "vendor")
    os.makedirs(d, exist_ok=True)
    return d


def _ensure_vendor_on_path():
    vd = _vendor_dir()
    if vd not in sys.path:
        sys.path.insert(0, vd)


# ---------------------------------------------------------------------------
# Edge TTS (online, best quality)
# ---------------------------------------------------------------------------

def _import_edge_tts():
    """Import bundled edge_tts from vendor/ (no runtime installs)."""
    global _edge_import_error
    _ensure_vendor_on_path()
    try:
        import edge_tts
        _edge_import_error = None
        return edge_tts
    except Exception as e:
        _edge_import_error = e
        log.warning("edge_tts import failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Piper TTS (offline, bundled)
# ---------------------------------------------------------------------------

def _load_piper_voice():
    """Load the Piper voice model, downloading it on first use if needed."""
    from .model_downloader import ensure_model, format_progress

    def _progress(downloaded: int, total: int):
        _notify(format_progress(downloaded, total))

    model_path = ensure_model(progress_callback=_progress)
    if model_path is None:
        _notify("Voice model unavailable — using system TTS")
        return None

    _ensure_vendor_on_path()
    try:
        from piper.voice import PiperVoice
        return PiperVoice.load(model_path)
    except Exception as e:
        log.error("Failed to load Piper voice: %s", e)
        return None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TTSEngine:
    """Manages TTS with fallback: Edge TTS -> Piper -> system voice."""

    EDGE_VOICE = "en-GB-RyanNeural"

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._edge_tts = None
        self._edge_tts_checked = False
        self._edge_tts_failed = False  # True after first speech failure
        self._piper_voice = None
        self._piper_voice_checked = False

    def _get_edge_tts(self):
        """Lazily load bundled edge_tts on first call."""
        if not self._edge_tts_checked:
            self._edge_tts = _import_edge_tts()
            self._edge_tts_checked = True
            if self._edge_tts is None:
                _notify_edge_unavailable(
                    _edge_import_error or RuntimeError("edge_tts import failed")
                )
        return self._edge_tts

    def _get_piper_voice(self):
        """Lazily load the Piper voice model. Retries if model wasn't available."""
        if not self._piper_voice_checked or self._piper_voice is None:
            self._piper_voice = _load_piper_voice()
            if self._piper_voice is not None:
                self._piper_voice_checked = True
        return self._piper_voice

    def speak(self, text: str, config: dict) -> None:
        """Stop any current speech, then speak text in a background thread."""
        self.stop()
        thread = threading.Thread(
            target=self._speak, args=(text, config), daemon=True
        )
        thread.start()

    def _speak(self, text: str, config: dict) -> None:
        speed = config.get("speed", 1.5)
        fallback = config.get("fallback_to_system", True)

        # Tier 1: Edge TTS (online, best quality)
        # Skip if it failed previously — don't retry every card
        if not self._edge_tts_failed:
            edge_tts = self._get_edge_tts()
            if edge_tts is not None:
                try:
                    self._speak_edge(text, speed, edge_tts)
                    return
                except Exception as e:
                    log.warning("Edge TTS failed, switching to Piper: %s", e)
                    self._edge_tts_failed = True
                    _notify_edge_unavailable(e)

        # Tier 2: Piper (offline, bundled)
        piper_voice = self._get_piper_voice()
        if piper_voice is not None:
            try:
                self._speak_piper(text, speed, piper_voice)
                return
            except Exception as e:
                log.warning("Piper speak failed: %s", e)

        # Tier 3: System TTS
        if fallback:
            self._speak_system(text, speed)

    def _speak_edge(self, text: str, speed: float, edge_tts) -> None:
        """Generate speech with Edge TTS and play the resulting audio."""
        import asyncio

        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

        async def _generate(tmp_path: str):
            comm = edge_tts.Communicate(text, self.EDGE_VOICE, rate=rate_str)
            await comm.save(tmp_path)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp = f.name

        try:
            asyncio.run(_generate(tmp))
            self._play_file(tmp)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def _speak_piper(self, text: str, speed: float, voice) -> None:
        """Generate speech with Piper TTS and play the resulting audio."""
        _ensure_vendor_on_path()
        from piper.config import SynthesisConfig

        # Piper uses length_scale for speed: lower = faster
        length_scale = 1.0 / speed if speed > 0 else 1.0
        syn_config = SynthesisConfig(length_scale=length_scale)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name

        try:
            with wave.open(tmp, "w") as wav_file:
                voice.synthesize_wav(text, wav_file, syn_config=syn_config)
            self._play_file(tmp)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def _speak_system(self, text: str, speed: float) -> None:
        """Use the OS built-in TTS as a last resort."""
        system = platform.system()

        if system == "Darwin":
            rate = str(int(200 * speed))
            cmd = ["say", "-r", rate, text]
        elif system == "Linux":
            rate = str(int(175 * speed))
            cmd = ["espeak", "-s", rate, text]
        elif system == "Windows":
            sapi_rate = int((speed - 1.0) * 5)
            escaped = text.replace("'", "''")
            ps = (
                "Add-Type -AssemblyName System.Speech;"
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                f"$s.Rate = {sapi_rate};"
                f"$s.Speak('{escaped}');"
            )
            cmd = ["powershell", "-Command", ps]
        else:
            return

        self._run_process(cmd)

    def _play_file(self, path: str) -> None:
        """Play an audio file using platform-appropriate command."""
        system = platform.system()

        if system == "Darwin":
            cmd = ["afplay", path]
        elif system == "Linux":
            cmd = ["mpv", "--no-terminal", "--", path]
        elif system == "Windows":
            cmd = [
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path,
            ]
        else:
            return

        self._run_process(cmd)

    def _run_process(self, cmd: list) -> None:
        """Spawn a subprocess, wait for it, and clean up safely."""
        try:
            proc = subprocess.Popen(cmd)
        except OSError:
            return

        with self._lock:
            self._process = proc

        proc.wait(timeout=120)

        with self._lock:
            if self._process is proc:
                self._process = None

    def stop(self) -> None:
        """Stop any in-progress speech."""
        with self._lock:
            proc = self._process

        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

            with self._lock:
                self._process = None
