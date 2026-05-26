"""以 Demucs 做人聲分離（取代原專案的 Spleeter）。

預設裝置 mps（Apple Silicon GPU），失敗時可 fallback 至 cpu。
使用 --two-stems=vocals 只切出「人聲 / 其餘」兩軌，較省時。
透過 on_progress 回呼把 Demucs 進度（0~100）回報給上層 UI。
"""

import re
import subprocess
import sys
from pathlib import Path

import config

# Demucs 進度條形如 " 45%|███| 193.0/427.0 [..]"，抓百分比。
_PCT_RE = re.compile(r"(\d+)%\|")


def _stream(cmd, on_progress):
    """執行 cmd，邊讀邊解析進度。回傳 (returncode, 完整輸出文字)。

    Demucs 的進度條用 '\\r' 重畫同一行，故逐字元讀取並以 '\\r'/'\\n' 斷句。
    """
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    captured = []
    buf = ""
    while True:
        ch = proc.stdout.read(1)
        if ch == "":
            break
        if ch in "\r\n":
            if buf:
                captured.append(buf)
                m = _PCT_RE.search(buf)
                if m and on_progress:
                    on_progress(min(100, int(m.group(1))))
                buf = ""
        else:
            buf += ch
    if buf:
        captured.append(buf)
    proc.wait()
    return proc.returncode, "\n".join(captured)


def separate_vocals(wav_path: str, out_dir: str, device: str = None, on_progress=None) -> str:
    """對 wav 做人聲分離，回傳 vocals.wav 路徑。

    Demucs 會輸出到 out_dir/<model>/<track_name>/vocals.wav。
    若指定裝置失敗（常見為 mps 不支援某些 op），自動退回 cpu 重試一次。
    """
    device = device or config.SEPARATION_DEVICE
    src = Path(wav_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def _build(dev):
        return [
            sys.executable, "-m", "demucs",
            "-n", config.DEMUCS_MODEL,
            "--two-stems=vocals",
            "-d", dev,
            "-o", str(out),
            str(src),
        ]

    rc, output = _stream(_build(device), on_progress)
    if rc != 0:
        if device != "cpu":
            # MPS 偶有不支援的算子，退回 CPU 再試一次。
            if on_progress:
                on_progress(0)
            rc, output = _stream(_build("cpu"), on_progress)
        if rc != 0:
            raise RuntimeError(f"Demucs 人聲分離失敗：\n{output}")

    vocals = out / config.DEMUCS_MODEL / src.stem / "vocals.wav"
    if not vocals.exists():
        raise RuntimeError(f"找不到 Demucs 輸出的人聲檔：{vocals}")
    return str(vocals)
