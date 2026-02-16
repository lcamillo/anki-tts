"""
Anki TTS - Automatic Text-to-Speech for Anki Reviews

Reads card content aloud as you review, using Edge TTS (Microsoft neural
voices) with automatic fallback to system TTS when offline.

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
    QComboBox,
    QGroupBox,
)
from aqt.utils import tooltip
from typing import Optional

from .tts_engine import TTSEngine
from .text_processing import extract_speakable_text


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
    text = extract_speakable_text(question_html)
    if text:
        engine().speak(text, conf)


def on_reviewer_did_show_answer(card) -> None:
    """Read the answer aloud if configured to do so."""
    conf = get_config()
    if not conf.get("enabled", True) or not conf.get("speak_answer", False):
        return

    answer_html = card.answer()
    text = extract_speakable_text(answer_html, strip_question=True)
    if text:
        engine().speak(text, conf)


def on_reviewer_will_end() -> None:
    """Stop TTS when leaving the reviewer."""
    engine().stop()


# ---------------------------------------------------------------------------
# Voice options
# ---------------------------------------------------------------------------

VOICES = [
    ("Ryan (British Male)", "en-GB-RyanNeural"),
    ("Sonia (British Female)", "en-GB-SoniaNeural"),
    ("Jenny (US Female)", "en-US-JennyNeural"),
    ("Guy (US Male)", "en-US-GuyNeural"),
    ("Natasha (Australian Female)", "en-AU-NatashaNeural"),
    ("William (Australian Male)", "en-AU-WilliamNeural"),
]


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

        # -- Voice --
        voice_group = QGroupBox("Voice")
        voice_layout = QVBoxLayout()
        self.voice_combo = QComboBox()
        current_voice = self.conf.get("voice", "en-GB-RyanNeural")
        for label, voice_id in VOICES:
            self.voice_combo.addItem(label, voice_id)
            if voice_id == current_voice:
                self.voice_combo.setCurrentIndex(
                    self.voice_combo.count() - 1
                )
        voice_layout.addWidget(self.voice_combo)
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
        self.fallback_cb = QCheckBox("Fall back to system TTS if offline")
        self.fallback_cb.setChecked(
            self.conf.get("fallback_to_system", True)
        )
        opts_layout.addWidget(self.fallback_cb)
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)

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

    def _save(self):
        self.conf["enabled"] = self.enabled_cb.isChecked()
        self.conf["voice"] = self.voice_combo.currentData()
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


def setup_menu():
    menu = QMenu("Anki TTS", mw)

    toggle_action = QAction("Toggle TTS", mw)
    toggle_action.triggered.connect(toggle_tts)
    menu.addAction(toggle_action)

    settings_action = QAction("Settings...", mw)
    settings_action.triggered.connect(lambda: SettingsDialog(mw).exec())
    menu.addAction(settings_action)

    mw.form.menubar.addMenu(menu)


# ---------------------------------------------------------------------------
# Bootstrap — must wait for profile to load before accessing mw.form / config
# ---------------------------------------------------------------------------

def _on_profile_did_open():
    setup_menu()
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
    gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
    gui_hooks.reviewer_will_end.append(on_reviewer_will_end)


def _on_profile_will_close():
    global _engine
    if _engine is not None:
        _engine.stop()
        _engine = None


gui_hooks.profile_did_open.append(_on_profile_did_open)
gui_hooks.profile_will_close.append(_on_profile_will_close)
