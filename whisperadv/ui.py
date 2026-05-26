"""TUI 進度表（以 rich 實作）與純文字備援 reporter。

pipeline 透過 reporter 回報各階段進度，與顯示細節解耦：
- RichReporter：終端機 TUI，逐階段顯示「圖示 / 名稱 / 進度條 / 百分比 / 耗時」。
- NullReporter：非 TTY（例如導向檔案）或 --no-tui 時的純文字輸出。
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

# 階段狀態圖示
_WAIT = "⏳"
_RUN = "▶ "
_DONE = "✅"
_ERR = "❌"


class NullReporter:
    """純文字備援：不做花俏顯示，只印關鍵訊息。"""

    live = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def header(self, info: dict):
        for k, v in info.items():
            print(f"{k}: {v}")

    def add_stages(self, names):
        self._names = list(names)

    def start_stage(self, name, total=None):
        print(f"▶ {name} ...")

    def update(self, completed):
        pass

    def finish_stage(self):
        pass

    def error_current(self):
        pass

    def note(self, msg: str):
        print(msg)


class RichReporter:
    """rich TUI 進度表。每個階段對應表格中的一列。"""

    live = True

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.progress = Progress(
            TextColumn("{task.fields[icon]}"),
            TextColumn("[bold]{task.description}"),
            BarColumn(bar_width=32),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )
        self._ids = {}        # 階段名 -> task id
        self._current = None  # 目前進行中的階段名

    def __enter__(self):
        self.progress.start()
        return self

    def __exit__(self, *exc):
        self.progress.stop()
        return False

    def header(self, info: dict):
        body = "\n".join(f"[cyan]{k}[/]：{v}" for k, v in info.items())
        self.console.print(Panel(body, title="MlxWhisperAdv", border_style="cyan"))

    def add_stages(self, names):
        for n in names:
            # 待處理：total=1、completed=0，顯示空進度條與待處理圖示。
            self._ids[n] = self.progress.add_task(n, start=False, total=1, icon=_WAIT)

    def start_stage(self, name, total=None):
        self._current = name
        tid = self._ids[name]
        # total=None → 不定量，進度條呈脈動動畫表示處理中。
        self.progress.reset(tid, total=total, start=True)
        self.progress.update(tid, icon=_RUN)

    def update(self, completed):
        if self._current is None:
            return
        self.progress.update(self._ids[self._current], completed=completed)

    def finish_stage(self):
        if self._current is None:
            return
        tid = self._ids[self._current]
        self.progress.update(tid, total=1, completed=1, icon=_DONE)
        self.progress.stop_task(tid)
        self._current = None

    def error_current(self):
        if self._current is None:
            return
        self.progress.update(self._ids[self._current], icon=_ERR)
        self.progress.stop_task(self._ids[self._current])

    def note(self, msg: str):
        self.console.print(msg)


def make_reporter(use_tui: bool):
    """依是否啟用 TUI 回傳對應 reporter。"""
    return RichReporter() if use_tui else NullReporter()
