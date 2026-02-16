"""
TTS engine for the Anki TTS add-on.
Uses Edge TTS (Microsoft) with system TTS as fallback.
Dependencies are auto-installed into a vendor/ subdirectory on first use.
"""

import os
import sys
import subprocess
import tempfile
import threading
import platform
from typing import Optional


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


def _install_edge_tts() -> bool:
    """Install edge-tts into the vendor directory."""
    try:
        vd = _vendor_dir()
        subprocess.check_call(
            [
                sys.executable, "-m", "pip", "install",
                "--target", vd, "--quiet", "--upgrade", "edge-tts",
            ],
            timeout=120,
        )
        _ensure_vendor_on_path()
        return True
    except Exception:
        return False


def _import_edge_tts():
    """Import edge_tts, installing it first if necessary."""
    _ensure_vendor_on_path()
    try:
        import edge_tts
        return edge_tts
    except ImportError:
        if _install_edge_tts():
            try:
                import edge_tts
                return edge_tts
            except ImportError:
                pass
        return None


class TTSEngine:
    """Manages TTS generation and audio playback."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._edge_tts = None
        self._edge_tts_checked = False

    def _get_edge_tts(self):
        """Lazily load edge_tts (auto-installs on first call)."""
        if not self._edge_tts_checked:
            self._edge_tts = _import_edge_tts()
            self._edge_tts_checked = True
        return self._edge_tts

    def speak(self, text: str, config: dict) -> None:
        """Stop any current speech, then speak text in a background thread."""
        self.stop()
        thread = threading.Thread(
            target=self._speak, args=(text, config), daemon=True
        )
        thread.start()

    def _speak(self, text: str, config: dict) -> None:
        speed = config.get("speed", 1.5)
        voice = config.get("voice", "en-GB-RyanNeural")
        fallback = config.get("fallback_to_system", True)

        # Try Edge TTS first
        edge_tts = self._get_edge_tts()
        if edge_tts is not None:
            try:
                self._speak_edge(text, voice, speed, edge_tts)
                return
            except Exception:
                pass

        # Fallback to system TTS
        if fallback:
            self._speak_system(text, speed)

    def _speak_edge(self, text: str, voice: str, speed: float, edge_tts) -> None:
        """Generate speech with Edge TTS and play the resulting audio."""
        import asyncio

        rate_pct = int((speed - 1.0) * 100)
        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

        async def _generate(tmp_path: str):
            comm = edge_tts.Communicate(text, voice, rate=rate_str)
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

    def _speak_system(self, text: str, speed: float) -> None:
        """Use the OS built-in TTS as a fallback."""
        system = platform.system()

        if system == "Darwin":
            rate = str(int(200 * speed))
            cmd = ["say", "-r", rate, text]
        elif system == "Linux":
            rate = str(int(175 * speed))
            cmd = ["espeak", "-s", rate, text]
        elif system == "Windows":
            # SAPI rate ranges from -10 to 10; map 0.5x-2.0x roughly
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
