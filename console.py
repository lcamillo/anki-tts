"""
Beautiful CLI Console for Anki TTS
Inspired by Claude Code's stunning terminal interface
"""

import sys
import time
import threading
from typing import Optional
from contextlib import contextmanager

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table
from rich.style import Style
from rich.theme import Theme
from rich.align import Align
from rich import box

# Custom theme
ANKI_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "heading": "bold magenta",
    "muted": "dim",
    "highlight": "bold cyan",
    "speed": "bold yellow",
    "card": "bold blue",
    "speech": "bold green",
    "status": "dim cyan",
})

console = Console(theme=ANKI_THEME, highlight=False)


LOGO = """[bold magenta]
   ╭───────────────────────────────────────────────────────╮
   │                                                       │
   │    ░█▀▀█ ░█▄─░█ ░█─▄▀ ▀█▀   ▀▀█▀▀ ▀▀█▀▀ ░█▀▀▀█       │
   │    ░█▄▄█ ░█░█░█ ░█▀▄─ ░█─   ─░█── ─░█── ─▀▀▀▄▄       │
   │    ░█─░█ ░█──▀█ ░█─░█ ▄█▄   ─░█── ─░█── ░█▄▄▄█       │
   │                                                       │
   │[bold cyan]         Text-to-Speech for Anki Flashcards          [/bold cyan]│
   │                                                       │
   ╰───────────────────────────────────────────────────────╯
[/bold magenta]"""


def print_header():
    """Print the beautiful header"""
    console.print(LOGO)


def print_minimal_header():
    """Print a minimal header"""
    console.print()
    console.print("   [bright_blue]╭───────────────────────────────────────────────────────╮[/]")
    console.print("   [bright_blue]│[/]       [bold magenta]Anki TTS[/] [dim]•[/] [cyan]Text-to-Speech for Flashcards[/]        [bright_blue]│[/]")
    console.print("   [bright_blue]╰───────────────────────────────────────────────────────╯[/]")
    console.print()


def success(message: str):
    """Print a success message"""
    console.print(f"   [green]✓[/] [white]{message}[/]")


def error(message: str):
    """Print an error message"""
    console.print(f"   [red]✗[/] [white]{message}[/]")


def warning(message: str):
    """Print a warning message"""
    console.print(f"   [yellow]![/] [white]{message}[/]")


def info(message: str):
    """Print an info message"""
    console.print(f"   [cyan]○[/] [dim]{message}[/]")


def muted(message: str):
    """Print a muted message"""
    console.print(f"   [dim]{message}[/]")


def speech_status(action: str, text: str = ""):
    """Print speech status"""
    if text:
        display_text = text[:55] + "..." if len(text) > 55 else text
        console.print(f"   [bold green]▶[/] [green]{action}[/] [dim]│[/] [white]{display_text}[/]")
    else:
        console.print(f"   [bold green]▶[/] [green]{action}[/]")


def card_detected(card_id: int):
    """Print card detection"""
    console.print(f"   [bold blue]◆[/] [blue]Card[/] [dim]│[/] [white]#{card_id}[/]")


def speed_update(speed: float, rate: int):
    """Print speed update with visual bar"""
    filled = int((speed - 1.0) / 0.8 * 8)
    bar = "[bold yellow]" + "━" * filled + "[/][dim]" + "─" * (8 - filled) + "[/]"
    console.print(f"   [yellow]◉[/] [yellow]Speed[/] [dim]│[/] {bar} [bold white]{speed}x[/] [dim]({rate} wpm)[/]")


def status_update(status: str, style: str = "cyan"):
    """Print status update"""
    console.print(f"   [dim]●[/] [dim]Status:[/] [{style}]{status}[/]")


def divider():
    """Print a divider"""
    console.print(f"   [dim]{'─' * 55}[/]")


def section(title: str):
    """Print a section header"""
    console.print()
    console.print(f"   [bold white]{title}[/]")
    divider()


@contextmanager
def spinner(message: str):
    """Context manager for a spinner animation"""
    with console.status(f"[cyan]{message}[/]", spinner="dots") as status:
        yield status


def print_ready_banner(speed: float = 1.5):
    """Print the ready banner"""
    console.print()
    console.print("   [green]╭───────────────────────────────────────────────────────╮[/]")
    console.print(f"   [green]│[/]       [bold green]Ready[/] [dim]•[/] Speed: [bold yellow]{speed}x[/] [dim]•[/] Auto-quit: 15min        [green]│[/]")
    console.print("   [green]╰───────────────────────────────────────────────────────╯[/]")
    console.print()


def print_quit_message():
    """Print goodbye message"""
    console.print()
    console.print("   [dim]╭───────────────────────────────────────────────────────╮[/]")
    console.print("   [dim]│[/]         Thanks for using [bold magenta]Anki TTS[/] • Goodbye!          [dim]│[/]")
    console.print("   [dim]╰───────────────────────────────────────────────────────╯[/]")
    console.print()


def print_inactivity_warning(minutes: int):
    """Print inactivity warning"""
    console.print()
    warning(f"No activity for {minutes} minutes. Auto-exiting...")


class LiveStatus:
    """
    Claude Code-style live updating status line.
    Shows an animated spinner with real-time status updates.
    """

    def __init__(self):
        self.message = "Initializing..."
        self.style = "cyan"
        self.live = None
        self.running = False
        self._lock = threading.Lock()

    def _create_display(self) -> Text:
        """Create the display text"""
        return Text.from_markup(f"   [cyan]●[/] [{self.style}]{self.message}[/]")

    def start(self, initial_message: str = "Starting..."):
        """Start the live status display"""
        self.message = initial_message
        self.running = True
        self.live = Live(
            self._create_display(),
            console=console,
            refresh_per_second=10,
            transient=True,
        )
        self.live.start()

    def update(self, message: str, style: str = "cyan"):
        """Update the status message"""
        with self._lock:
            self.message = message
            self.style = style
            if self.live and self.running:
                self.live.update(self._create_display())

    def stop(self, final_message: str = None, show_success: bool = True):
        """Stop the live status and optionally print final message"""
        self.running = False
        if self.live:
            self.live.stop()
            self.live = None
        if final_message:
            if show_success:
                success(final_message)
            else:
                info(final_message)


class AnimatedSpinner:
    """
    Claude Code-style animated spinner for long operations.
    Uses a smooth braille dot animation.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str):
        self.message = message
        self.running = False
        self.thread = None
        self.frame_idx = 0

    def _animate(self):
        """Animation loop"""
        while self.running:
            frame = self.FRAMES[self.frame_idx % len(self.FRAMES)]
            console.print(f"\r   [cyan]{frame}[/] [dim]{self.message}[/]", end="")
            self.frame_idx += 1
            time.sleep(0.08)

    def start(self):
        """Start the spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self, success_message: str = None):
        """Stop the spinner"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)
        # Clear the line
        console.print("\r" + " " * 70 + "\r", end="")
        if success_message:
            success(success_message)


class StartupSequence:
    """
    Claude Code-style startup sequence with animated steps.
    """

    def __init__(self):
        self.steps = []

    def add_step(self, name: str, action: callable = None):
        """Add a step to the sequence"""
        self.steps.append((name, action))

    def run(self):
        """Run the startup sequence with animations"""
        for step_name, action in self.steps:
            with console.status(f"[cyan]{step_name}...[/]", spinner="dots"):
                if action:
                    try:
                        action()
                    except Exception as e:
                        error(f"{step_name}: {e}")
                        return False
                else:
                    time.sleep(0.3)
            success(step_name)
        return True


# Export
__all__ = [
    'console',
    'print_header',
    'print_minimal_header',
    'success',
    'error',
    'warning',
    'info',
    'muted',
    'speech_status',
    'card_detected',
    'speed_update',
    'status_update',
    'divider',
    'section',
    'spinner',
    'print_ready_banner',
    'print_quit_message',
    'print_inactivity_warning',
    'LiveStatus',
    'AnimatedSpinner',
    'StartupSequence',
]
