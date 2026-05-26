# MlxWhisperAdv 進度筆記

> 目標：把 GitHub 上的 `iamjlintw/WhisperAdv`（影片→人聲分離→Whisper→WebVTT）
> **改寫成 macOS (Apple Silicon) 專用版本**，完成後推到一個**新的 GitHub repo**。
> 不沿用原專案的 conda / Spleeter 架構。

## 決定的技術棧（macOS 原生）
| 功能 | 原專案 | 本專案改用 | 原因 |
|---|---|---|---|
| 人聲分離 | Spleeter (TensorFlow) | **Demucs** (PyTorch/MPS) | arm64 裝不了 tensorflow、numpy 衝突 |
| 語音辨識 | openai-whisper (CUDA/CPU) | **mlx-whisper** | Apple Silicon GPU 原生加速，最快 |
| 抽音軌 | moviepy | **ffmpeg 直呼**（已裝 8.0） | 更穩更輕 |
| 字幕輸出 | webvtt-py | webvtt-py（VTT + 計畫加 SRT） | 不變 |
| 環境隔離 | conda × 3 | **單一 venv（無 conda）** | Demucs+Whisper 同為 torch 可共存 |
| GPU | CUDA | MPS / MLX | Mac 無 NVIDIA |

## 本機環境（已確認）
- Apple M2 Pro (arm64) / macOS 15.6.1
- Python 3.12.3（pyenv，唯一可用版本，無 3.10/3.11）
- ffmpeg 8.0 ✅ / Homebrew 5.1.3 ✅
- conda ❌ 未裝（本專案不需要）/ CUDA ❌ 無

## ✅ 已完成
1. 分析原專案需求與本機可行性（結論：Spleeter 不可行，其餘可行）。
2. 資料夾已從 `WhisperAdv` 改名為 `MlxWhisperAdv`。
3. 建立 `requirements.txt`（demucs / mlx-whisper / webvtt-py / python-dotenv / torch / torchaudio / numpy）。
4. 建立 `.venv`（Python 3.12.3，已 upgrade pip，乾淨狀態）。
5. **路徑檢查**：venv（pyvenv.cfg / pip shebang / activate）全部正確指向新資料夾 `MlxWhisperAdv`，無殘留舊路徑。
6. **撰寫程式碼完成**（已過 py_compile 語法檢查）：
   - `config.py` + `.env.example` — 集中設定，可由環境變數覆寫
   - `whisperadv/audio.py` — ffmpeg 抽音軌（stereo / 44.1k）
   - `whisperadv/separator.py` — Demucs `--two-stems=vocals`，mps 失敗自動 fallback cpu
   - `whisperadv/transcriber.py` — `mlx_whisper.transcribe()`
   - `whisperadv/subtitles.py` — segments → VTT / SRT（自寫時間碼格式器）
   - `whisperadv/pipeline.py` — 串接 + tempfile 暫存 + 清理
   - `main.py` — argparse CLI（input / -o / --model / --language / --device / --no-separation / --format / --keep-temp）
   - `setup_mac.sh`、`README.md`（繁中）、`.gitignore`

## ⬜ 尚未完成（下次接續）
1. **安裝依賴**（pip install 這步使用者尚未批准執行）：
   ```bash
   cd /Users/jlin/codes/tool/MlxWhisperAdv
   ./setup_mac.sh   # 或 .venv/bin/python -m pip install -r requirements.txt
   ```
   注意：demucs 在 Python 3.12 可能有依賴小摩擦，裝完 setup 會自動驗證 import + MPS 可用性。
2. **測試**：找一段短影片跑完整 pipeline，驗證輸出 .vtt。
3. **推 GitHub**：建立新 repo（建議 `MlxWhisperAdv`），git init → push。

## 待使用者確認的點
- 新 repo 名稱與是否 public/private。
- Whisper 模型大小預設（large-v3 準但慢，base/small 快）。
