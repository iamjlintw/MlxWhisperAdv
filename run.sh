#!/usr/bin/env bash
# MlxWhisperAdv 啟動腳本。
#   ./run.sh                 # 從 import/ 選檔、選模型，輸出到 output/
#   ./run.sh input.mp4       # 直接指定檔案
#   ./run.sh input.mp4 --burn  # 順便把字幕燒進影片（硬字幕）
#   ./run.sh input.mp4 --model mlx-community/whisper-base-mlx --format both
# 所有參數會原樣傳給 main.py。
set -euo pipefail

cd "$(dirname "$0")"

# 沒有 venv 就先提示建置
if [ ! -x ".venv/bin/python" ]; then
  echo "找不到虛擬環境，請先執行：./setup_mac.sh" >&2
  exit 1
fi

# ffmpeg 是必要外部相依
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "找不到 ffmpeg，請先安裝：brew install ffmpeg" >&2
  exit 1
fi

exec .venv/bin/python main.py "$@"
