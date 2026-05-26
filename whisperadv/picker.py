"""TUI 檔案選單：列出 import/ 內的媒體檔，用方向鍵選擇要加字幕的檔案。

互動採 stdlib termios/tty（cbreak 模式），不需額外依賴；
非終端機環境或無法進入 cbreak 時，退回輸入編號的純文字選單。
"""

import os
import select
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# 視為媒體的副檔名
MEDIA_EXTS = {
    ".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv", ".ts", ".mpg", ".mpeg",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma",
}


def list_media(import_dir: str) -> List[Path]:
    """列出 import_dir 內的媒體檔（依檔名排序）。"""
    d = Path(import_dir)
    if not d.exists():
        return []
    files = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTS]
    return sorted(files, key=lambda p: p.name.lower())


def _human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f}{unit}" if unit == "B" else f"{num:.1f}{unit}"
        num /= 1024


def _render(files: List[Path], idx: int) -> Panel:
    body = Text()
    for i, f in enumerate(files):
        selected = i == idx
        prefix = "❯ " if selected else "  "
        line = f"{prefix}{f.name}  ({_human_size(f.stat().st_size)})"
        body.append(line + "\n", style="reverse bold cyan" if selected else "")
    return Panel(
        body,
        title="選擇要加字幕的檔案",
        subtitle="↑/↓ 或 j/k 移動，Enter 選擇，q 取消",
        border_style="cyan",
    )


def _read_key() -> str:
    """cbreak 模式下讀一個按鍵，回傳語意化字串。"""
    fd = sys.stdin.fileno()
    ch = os.read(fd, 1)
    if not ch:
        return "eof"
    if ch == b"\x1b":  # ESC，可能是方向鍵序列
        r, _, _ = select.select([sys.stdin], [], [], 0.05)
        if r:
            seq = os.read(fd, 2)
            return {b"[A": "up", b"[B": "down", b"[C": "right", b"[D": "left"}.get(seq, "esc")
        return "esc"
    if ch in (b"\r", b"\n"):
        return "enter"
    if ch == b"\x03":
        return "ctrl-c"
    if ch in (b"k", b"K"):
        return "up"
    if ch in (b"j", b"J"):
        return "down"
    if ch in (b"q", b"Q"):
        return "quit"
    return ch.decode(errors="ignore")


def _select_cbreak(files: List[Path], console: Console) -> Optional[Path]:
    """方向鍵互動選單。回傳選中的檔案，取消則 None。"""
    import termios
    import tty
    from rich.live import Live

    idx = 0
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        with Live(_render(files, idx), console=console, auto_refresh=False, screen=False) as live:
            while True:
                live.update(_render(files, idx))
                live.refresh()
                key = _read_key()
                if key == "up":
                    idx = (idx - 1) % len(files)
                elif key == "down":
                    idx = (idx + 1) % len(files)
                elif key == "enter":
                    return files[idx]
                elif key in ("quit", "esc", "ctrl-c", "eof"):
                    return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _select_numbered(files: List[Path], console: Console) -> Optional[Path]:
    """備援：列編號讓使用者輸入選擇。"""
    from rich.prompt import IntPrompt

    console.print("[bold cyan]選擇要加字幕的檔案：[/]")
    for i, f in enumerate(files, start=1):
        console.print(f"  [bold]{i}[/]. {f.name}  ([dim]{_human_size(f.stat().st_size)}[/])")
    try:
        n = IntPrompt.ask("輸入編號（0 取消）", default=1)
    except (EOFError, KeyboardInterrupt):
        return None
    if n < 1 or n > len(files):
        return None
    return files[n - 1]


def select_file(files: List[Path], console: Console = None) -> Optional[Path]:
    """從清單選一個檔案。終端機用方向鍵選單，否則退回編號輸入。"""
    console = console or Console()
    if not files:
        return None
    if sys.stdin.isatty():
        try:
            return _select_cbreak(files, console)
        except Exception:
            # 某些終端無法進入 cbreak，退回編號模式。
            return _select_numbered(files, console)
    return _select_numbered(files, console)
