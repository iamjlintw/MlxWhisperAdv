"""集中設定。可由環境變數 / .env 覆寫，避免硬編碼。"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 專案根目錄（本檔所在處），import/ 與 output/ 以此為基準。
BASE_DIR = Path(__file__).resolve().parent


def _get(key: str, default: str) -> str:
    return os.environ.get(key, default)


# 匯入資料夾：把要加字幕的影片/音檔放這裡；不指定輸入時 TUI 會從這裡選。
IMPORT_DIR = _get("IMPORT_DIR", str(BASE_DIR / "import"))

# 輸出資料夾：字幕檔預設輸出到這裡。
OUTPUT_DIR = _get("OUTPUT_DIR", str(BASE_DIR / "output"))


# Whisper 模型（mlx-community 上的 MLX 量化版）
# large-v3 最準但較慢；要快可改 mlx-community/whisper-base 或 whisper-small。
WHISPER_MODEL = _get("WHISPER_MODEL", "mlx-community/whisper-large-v3-mlx")

# TUI 模型選單可選項：(顯示名, repo id, 說明)。
WHISPER_MODELS = [
    ("base", "mlx-community/whisper-base-mlx", "最快，精度較低"),
    ("small", "mlx-community/whisper-small-mlx", "速度與精度平衡"),
    ("large-v3", "mlx-community/whisper-large-v3-mlx", "最準，較慢、較吃記憶體"),
]

# 語言：None 代表自動偵測；可設 "zh"、"en" 等。
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE") or None

# 人聲分離計算裝置：mps（Apple GPU）/ cpu。
SEPARATION_DEVICE = _get("SEPARATION_DEVICE", "mps")

# Demucs 模型名稱。htdemucs 為預設 4-stem 模型，搭配 two-stems 取人聲。
DEMUCS_MODEL = _get("DEMUCS_MODEL", "htdemucs")

# 預設字幕輸出格式：vtt / srt / both。
DEFAULT_FORMAT = _get("DEFAULT_FORMAT", "vtt")

# 是否把中文字幕轉成繁體（台灣用語）。
CONVERT_TO_TW = _get("CONVERT_TO_TW", "1").lower() not in ("0", "false", "no", "")

# OpenCC 轉換設定檔：s2twp = 簡轉繁 + 台灣慣用詞（信息→資訊、視頻→影片…）。
OPENCC_PROFILE = _get("OPENCC_PROFILE", "s2twp")

# ffmpeg 執行檔路徑（已裝在 PATH 即可）。
FFMPEG_BIN = _get("FFMPEG_BIN", "ffmpeg")

# 硬字幕燒錄字型與字級（macOS 預設繁中字型 PingFang TC）。
BURN_FONT = _get("BURN_FONT", "PingFang TC")
BURN_FONT_SIZE = int(_get("BURN_FONT_SIZE", "20"))
