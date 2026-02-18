"""
Anki TTS - Automatic Text-to-Speech for Anki Reviews

Reads card content aloud using Edge TTS (Ryan, online) with fallback to
Piper (Alan, offline) and then system TTS.

Install: Tools -> Add-ons -> Install from file -> select anki_tts.ankiaddon
"""

from aqt import mw, gui_hooks
from aqt.qt import (
    QAction,
    QMenu,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QGroupBox,
)
from aqt.utils import tooltip
from typing import Optional
import threading

from .tts_engine import TTSEngine, set_status_callback
from .text_processing import extract_speakable_text
from .model_downloader import ensure_model, is_model_available, format_progress


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def get_config() -> dict:
    return mw.addonManager.getConfig(__name__) or {}


def save_config(conf: dict):
    mw.addonManager.writeConfig(__name__, conf)


# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------

_engine: Optional[TTSEngine] = None


def engine() -> TTSEngine:
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    return _engine


def _show_status(msg: str):
    """Show a tooltip on the main thread (safe from background threads)."""
    mw.taskman.run_on_main(lambda: tooltip(msg))


# ---------------------------------------------------------------------------
# Reviewer hooks
# ---------------------------------------------------------------------------

def on_reviewer_did_show_question(card) -> None:
    """Called every time the reviewer shows a new question."""
    conf = get_config()
    if not conf.get("enabled", True) or not conf.get("speak_question", True):
        return

    engine().stop()

    question_html = card.question()
    text = extract_speakable_text(question_html, active_ord=card.ord)
    if text:
        engine().speak(text, conf)


def on_reviewer_did_show_answer(card) -> None:
    """Read the answer aloud if configured to do so."""
    conf = get_config()
    if not conf.get("enabled", True) or not conf.get("speak_answer", False):
        return

    answer_html = card.answer()
    text = extract_speakable_text(
        answer_html, strip_question=True, active_ord=card.ord
    )
    if text:
        engine().speak(text, conf)


def on_reviewer_will_end() -> None:
    """Stop TTS when leaving the reviewer."""
    engine().stop()


# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anki TTS Settings")
        self.setMinimumWidth(360)
        self.conf = get_config()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # -- Enabled --
        self.enabled_cb = QCheckBox("Enable TTS during reviews")
        self.enabled_cb.setChecked(self.conf.get("enabled", True))
        layout.addWidget(self.enabled_cb)

        # -- Voice info --
        voice_group = QGroupBox("Voice")
        voice_layout = QVBoxLayout()
        voice_layout.addWidget(QLabel("Ryan (British Male) — Edge TTS online"))
        voice_layout.addWidget(QLabel("Alan (British Male) — Piper offline fallback"))
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # -- Speed --
        speed_group = QGroupBox("Speed")
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Rate:"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 2.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(self.conf.get("speed", 1.5))
        self.speed_spin.setSuffix("x")
        speed_layout.addWidget(self.speed_spin)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # -- Reading options --
        opts_group = QGroupBox("Reading Options")
        opts_layout = QVBoxLayout()
        self.speak_q_cb = QCheckBox("Read question aloud")
        self.speak_q_cb.setChecked(self.conf.get("speak_question", True))
        opts_layout.addWidget(self.speak_q_cb)
        self.speak_a_cb = QCheckBox("Read answer aloud")
        self.speak_a_cb.setChecked(self.conf.get("speak_answer", False))
        opts_layout.addWidget(self.speak_a_cb)
        self.fallback_cb = QCheckBox("Fall back to system TTS as last resort")
        self.fallback_cb.setChecked(
            self.conf.get("fallback_to_system", True)
        )
        opts_layout.addWidget(self.fallback_cb)
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)

        # -- Test Voice --
        test_btn = QPushButton("Test Voice")
        test_btn.clicked.connect(self._test_voice)
        layout.addWidget(test_btn)

        # -- Buttons --
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _test_voice(self):
        """Preview the current speed setting with the bundled Piper voice."""
        test_conf = {
            "speed": self.speed_spin.value(),
            "fallback_to_system": self.fallback_cb.isChecked(),
        }
        engine().speak("This is a test of the Anki text to speech voice.", test_conf)

    def _save(self):
        self.conf["enabled"] = self.enabled_cb.isChecked()
        self.conf["speed"] = self.speed_spin.value()
        self.conf["speak_question"] = self.speak_q_cb.isChecked()
        self.conf["speak_answer"] = self.speak_a_cb.isChecked()
        self.conf["fallback_to_system"] = self.fallback_cb.isChecked()
        save_config(self.conf)
        tooltip("Anki TTS settings saved")
        self.accept()


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

def toggle_tts():
    conf = get_config()
    conf["enabled"] = not conf.get("enabled", True)
    save_config(conf)
    state = "enabled" if conf["enabled"] else "disabled"
    tooltip(f"Anki TTS {state}")


def download_voice_model():
    """Manually trigger voice model download in a background thread."""
    if is_model_available():
        tooltip("Voice model already downloaded")
        return

    def _progress(downloaded: int, total: int):
        _show_status(format_progress(downloaded, total))

    def _run():
        path = ensure_model(progress_callback=_progress)
        if path:
            _show_status("Voice model downloaded successfully")
        else:
            _show_status("Voice model download failed")

    threading.Thread(target=_run, daemon=True).start()
    tooltip("Downloading voice model in background...")


# ---------------------------------------------------------------------------
# Bootstrap — must wait for profile to load before accessing mw.form / config
# ---------------------------------------------------------------------------

_menu_added = False
_hooks_registered = False


def _on_profile_did_open():
    global _menu_added, _hooks_registered
    set_status_callback(_show_status)

    # Only add the menu once (persists across profile switches)
    if not _menu_added:
        menu = QMenu("Anki TTS", mw)

        toggle_action = QAction("Toggle TTS", mw)
        toggle_action.setShortcut("Ctrl+Shift+T")
        toggle_action.triggered.connect(toggle_tts)
        menu.addAction(toggle_action)

        settings_action = QAction("Settings...", mw)
        settings_action.triggered.connect(lambda: SettingsDialog(mw).exec())
        menu.addAction(settings_action)

        download_action = QAction("Download Voice Model", mw)
        download_action.triggered.connect(download_voice_model)
        menu.addAction(download_action)

        mw.form.menubar.addMenu(menu)
        _menu_added = True

    # Register reviewer hooks (flag prevents duplicates on profile re-open)
    if not _hooks_registered:
        gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
        gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
        gui_hooks.reviewer_will_end.append(on_reviewer_will_end)
        _hooks_registered = True


def _on_profile_will_close():
    global _engine, _hooks_registered
    if _engine is not None:
        _engine.stop()
        _engine = None

    # Remove hooks so they aren't duplicated on next profile open
    if _hooks_registered:
        gui_hooks.reviewer_did_show_question.remove(on_reviewer_did_show_question)
        gui_hooks.reviewer_did_show_answer.remove(on_reviewer_did_show_answer)
        gui_hooks.reviewer_will_end.remove(on_reviewer_will_end)
        _hooks_registered = False


gui_hooks.profile_did_open.append(_on_profile_did_open)
gui_hooks.profile_will_close.append(_on_profile_will_close)
