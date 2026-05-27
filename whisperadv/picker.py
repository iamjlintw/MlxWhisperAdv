"""TUI 選單：列出選項用方向鍵選擇（檔案、模型皆可）。

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

import config

# 視為影片的副檔名
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv", ".ts", ".mpg", ".mpeg"}
# 視為音檔的副檔名
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
# 視為媒體（影片＋音檔）
MEDIA_EXTS = VIDEO_EXTS | AUDIO_EXTS
# 字幕副檔名
SUB_EXTS = {".vtt", ".srt"}


def _list_by_ext(folder: str, exts) -> List[Path]:
    d = Path(folder)
    if not d.exists():
        return []
    files = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return sorted(files, key=lambda p: p.name.lower())


def list_media(import_dir: str) -> List[Path]:
    """列出資料夾內的媒體檔（影片＋音檔，依檔名排序）。"""
    return _list_by_ext(import_dir, MEDIA_EXTS)


def list_videos(folder: str) -> List[Path]:
    """列出資料夾內的影片檔。"""
    return _list_by_ext(folder, VIDEO_EXTS)


def list_subtitles(folder: str) -> List[Path]:
    """列出資料夾內的字幕檔（.vtt / .srt）。"""
    return _list_by_ext(folder, SUB_EXTS)


def _human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f}{unit}" if unit == "B" else f"{num:.1f}{unit}"
        num /= 1024


def _render(title: str, subtitle: str, labels: List[str], idx: int) -> Panel:
    body = Text()
    for i, label in enumerate(labels):
        selected = i == idx
        prefix = "❯ " if selected else "  "
        body.append(prefix + label + "\n", style="reverse bold cyan" if selected else "")
    return Panel(body, title=title, subtitle=subtitle, border_style="cyan")


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


def _menu_cbreak(labels: List[str], title: str, subtitle: str, console: Console) -> Optional[int]:
    """方向鍵互動選單。回傳選中的索引，取消則 None。"""
    import termios
    import tty
    from rich.live import Live

    idx = 0
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        with Live(_render(title, subtitle, labels, idx), console=console,
                  auto_refresh=False, screen=False) as live:
            while True:
                live.update(_render(title, subtitle, labels, idx))
                live.refresh()
                key = _read_key()
                if key == "up":
                    idx = (idx - 1) % len(labels)
                elif key == "down":
                    idx = (idx + 1) % len(labels)
                elif key == "enter":
                    return idx
                elif key in ("quit", "esc", "ctrl-c", "eof"):
                    return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _menu_numbered(labels: List[str], title: str, console: Console) -> Optional[int]:
    """備援：列編號讓使用者輸入選擇。回傳索引，取消則 None。"""
    from rich.prompt import IntPrompt

    console.print(f"[bold cyan]{title}：[/]")
    for i, label in enumerate(labels, start=1):
        console.print(f"  [bold]{i}[/]. {label}")
    try:
        n = IntPrompt.ask("輸入編號（0 取消）", default=1)
    except (EOFError, KeyboardInterrupt):
        return None
    if n < 1 or n > len(labels):
        return None
    return n - 1


def _menu(labels: List[str], title: str, subtitle: str, console: Console) -> Optional[int]:
    """通用選單：終端機用方向鍵，否則退回編號輸入。回傳選中索引或 None。"""
    if not labels:
        return None
    if sys.stdin.isatty():
        try:
            return _menu_cbreak(labels, title, subtitle, console)
        except Exception:
            # 某些終端無法進入 cbreak，退回編號模式。
            return _menu_numbered(labels, title, console)
    return _menu_numbered(labels, title, console)


_NAV = "↑/↓ 或 j/k 移動，Enter 選擇，q 取消"


def select_file(files: List[Path], title: str = "選擇要加字幕的檔案",
                console: Console = None) -> Optional[Path]:
    """從檔案清單選一個。回傳 Path，取消則 None。"""
    console = console or Console()
    if not files:
        return None
    labels = [f"{f.name}  ({_human_size(f.stat().st_size)})" for f in files]
    idx = _menu(labels, title, _NAV, console)
    return None if idx is None else files[idx]


def select_mode(console: Console = None) -> Optional[str]:
    """選擇路線：'sub'（產生字幕）或 'burn'（燒錄字幕）。取消則 None。"""
    console = console or Console()
    modes = [
        ("sub", "產生字幕    影片/音檔 → 辨識 → 字幕檔"),
        ("burn", "燒錄字幕    影片 + 字幕 → 內嵌字幕影片"),
    ]
    idx = _menu([label for _k, label in modes], "選擇要做什麼", _NAV, console)
    return None if idx is None else modes[idx][0]


def select_model(console: Console = None) -> Optional[str]:
    """選擇 Whisper 模型。回傳 repo id，取消則 None。"""
    console = console or Console()
    models = config.WHISPER_MODELS
    labels = [f"{name:<9} {desc}" for name, _repo, desc in models]
    idx = _menu(labels, "選擇辨識模型", _NAV, console)
    return None if idx is None else models[idx][1]
