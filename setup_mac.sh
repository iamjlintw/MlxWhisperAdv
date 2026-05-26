#!/usr/bin/env bash
# macOS (Apple Silicon) 一鍵環境建置：建立 venv 並安裝依賴。
set -euo pipefail

cd "$(dirname "$0")"

# 檢查 ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "找不到 ffmpeg，請先安裝：brew install ffmpeg" >&2
  exit 1
fi

# 建立 venv（若不存在）
if [ ! -d ".venv" ]; then
  echo "建立虛擬環境 .venv ..."
  python3 -m venv .venv
fi

echo "升級 pip ..."
.venv/bin/python -m pip install --upgrade pip

echo "安裝依賴 ..."
.venv/bin/python -m pip install -r requirements.txt

echo "驗證 import ..."
.venv/bin/python - <<'PY'
import mlx_whisper, demucs, torch
print("mlx_whisper / demucs / torch import OK")
print("torch MPS 可用：", torch.backends.mps.is_available())
PY

echo "完成。用法：.venv/bin/python main.py <影片或音檔>"
