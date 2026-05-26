"""集中設定。可由環境變數 / .env 覆寫，避免硬編碼。"""

import os

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str) -> str:
    return os.environ.get(key, default)


# Whisper 模型（mlx-community 上的 MLX 量化版）
# large-v3 最準但較慢；要快可改 mlx-community/whisper-base 或 whisper-small。
WHISPER_MODEL = _get("WHISPER_MODEL", "mlx-community/whisper-large-v3-mlx")

# 語言：None 代表自動偵測；可設 "zh"、"en" 等。
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE") or None

# 人聲分離計算裝置：mps（Apple GPU）/ cpu。
SEPARATION_DEVICE = _get("SEPARATION_DEVICE", "mps")

# Demucs 模型名稱。htdemucs 為預設 4-stem 模型，搭配 two-stems 取人聲。
DEMUCS_MODEL = _get("DEMUCS_MODEL", "htdemucs")

# 預設字幕輸出格式：vtt / srt / both。
DEFAULT_FORMAT = _get("DEFAULT_FORMAT", "vtt")

# ffmpeg 執行檔路徑（已裝在 PATH 即可）。
FFMPEG_BIN = _get("FFMPEG_BIN", "ffmpeg")
