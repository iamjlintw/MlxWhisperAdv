"""以 Demucs 做人聲分離（取代原專案的 Spleeter）。

預設裝置 mps（Apple Silicon GPU），失敗時可 fallback 至 cpu。
使用 --two-stems=vocals 只切出「人聲 / 其餘」兩軌，較省時。
"""

import subprocess
import sys
from pathlib import Path

import config


def separate_vocals(wav_path: str, out_dir: str, device: str = None) -> str:
    """對 wav 做人聲分離，回傳 vocals.wav 路徑。

    Demucs 會輸出到 out_dir/<model>/<track_name>/vocals.wav。
    若指定裝置失敗（常見為 mps 不支援某些 op），自動退回 cpu 重試一次。
    """
    device = device or config.SEPARATION_DEVICE
    src = Path(wav_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def _run(dev: str):
        cmd = [
            sys.executable, "-m", "demucs",
            "-n", config.DEMUCS_MODEL,
            "--two-stems=vocals",
            "-d", dev,
            "-o", str(out),
            str(src),
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    proc = _run(device)
    if proc.returncode != 0:
        if device != "cpu":
            # MPS 偶有不支援的算子，退回 CPU 再試一次。
            proc = _run("cpu")
        if proc.returncode != 0:
            raise RuntimeError(f"Demucs 人聲分離失敗：\n{proc.stderr}")

    vocals = out / config.DEMUCS_MODEL / src.stem / "vocals.wav"
    if not vocals.exists():
        raise RuntimeError(f"找不到 Demucs 輸出的人聲檔：{vocals}")
    return str(vocals)
