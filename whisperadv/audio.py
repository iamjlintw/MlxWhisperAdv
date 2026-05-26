"""以 ffmpeg 直接抽出音軌。保留 stereo / 44.1kHz 給 Demucs 使用。"""

import subprocess
from pathlib import Path

import config


def extract_audio(input_path: str, out_wav: str) -> str:
    """從影片（或音檔）抽出 PCM WAV：stereo、44.1kHz、16-bit。

    Demucs 需要立體聲與較高取樣率才能良好分離人聲，故不在此降規。
    回傳輸出的 wav 路徑。
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"找不到輸入檔：{input_path}")

    cmd = [
        config.FFMPEG_BIN,
        "-y",                 # 覆寫既有輸出
        "-i", str(src),
        "-vn",                # 去除影像
        "-ac", "2",           # 立體聲
        "-ar", "44100",       # 44.1kHz
        "-acodec", "pcm_s16le",
        str(out_wav),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 抽音軌失敗：\n{proc.stderr}")
    return out_wav
