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

7. **安裝依賴完成**：`./setup_mac.sh` 跑完，所有套件裝好，
   `mlx_whisper / demucs / torch` import OK，**torch MPS 可用 = True**。
   （實際版本：torch 2.12.0 / demucs 4.0.1 / mlx-whisper 0.4.3 / numpy 2.4.6）
8. **推 GitHub 完成**：已推到 **public** repo
   <https://github.com/iamjlintw/MlxWhisperAdv>（branch main，origin 走 SSH）。
   `.claude/` 已加入 .gitignore 不入庫。

9. **真實素材端對端測試通過** ✅：用 `廠商端使用手冊影片V2.mp4`（約 7 分鐘）
   跑完整 pipeline（ffmpeg → Demucs/MPS 分離 → whisper-base 辨識 → VTT+SRT），
   產出 93 段字幕，格式 / 時間碼 / 繁中皆正確。
   過程中修掉兩個 bug：
   - **torchcodec 缺失**：torch 2.12/torchaudio 2.11 把音訊存檔委派給 torchcodec，
     Demucs 存 vocals.wav 會失敗 → 已加入 requirements.txt 並安裝（與 ffmpeg 8.0 相容）。
   - **模型 repo 名稱**：mlx-community 的 repo 都帶 `-mlx` 後綴
     （正解 `whisper-base-mlx` / `whisper-large-v3-mlx`，不帶後綴會 401）。
     config 預設值本來就正確；測試指令補上後綴後即通過。
   - 備註：base 小模型辨識精度偏低（有錯字），預設 large-v3 會準很多。

## 全部完成 🎉
專案已可用。後續若要更準，直接用預設 large-v3 跑即可（較慢、較吃記憶體）。

## 已確認的決定
- repo 名稱 `MlxWhisperAdv`，**public**。
- Whisper 預設模型 **large-v3**（config.WHISPER_MODEL = mlx-community/whisper-large-v3-mlx）。
