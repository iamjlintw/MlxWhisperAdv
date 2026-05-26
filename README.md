# MlxWhisperAdv

macOS（Apple Silicon）專用的字幕產生工具：**影片 → 人聲分離 → 語音辨識 → WebVTT / SRT**。

由 [`iamjlintw/WhisperAdv`](https://github.com/iamjlintw/WhisperAdv) 改寫而來，捨棄無法在 arm64 安裝的 conda / Spleeter / TensorFlow 架構，改用 Apple 原生加速的技術棧。

## 技術棧

| 功能 | 原專案 | 本專案 |
|---|---|---|
| 人聲分離 | Spleeter (TensorFlow) | **Demucs** (PyTorch / MPS) |
| 語音辨識 | openai-whisper (CUDA/CPU) | **mlx-whisper** (Apple GPU) |
| 抽音軌 | moviepy | **ffmpeg** 直呼 |
| 字幕輸出 | webvtt-py | WebVTT + SRT |
| 環境 | conda × 3 | 單一 venv |

## 環境需求

- Apple Silicon（M 系列）+ macOS
- Python 3.12
- ffmpeg（`brew install ffmpeg`）

## 安裝

```bash
git clone <this-repo>
cd MlxWhisperAdv
chmod +x setup_mac.sh && ./setup_mac.sh
```

或手動：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 使用

```bash
# 最簡單：輸出與輸入同名的 .vtt
.venv/bin/python main.py input.mp4

# 指定輸出、模型、格式
.venv/bin/python main.py input.mp4 -o out/myvideo --model mlx-community/whisper-base --format both

# 純語音（背景乾淨）可略過人聲分離以加速
.venv/bin/python main.py podcast.mp3 --no-separation --language zh
```

### 參數

| 參數 | 說明 |
|---|---|
| `input` | 輸入影片或音檔 |
| `-o, --output` | 輸出字幕前綴（不含副檔名） |
| `--model` | Whisper 模型，預設 `mlx-community/whisper-large-v3-mlx` |
| `--language` | 語言碼（`zh` / `en`…），預設自動偵測 |
| `--device` | 人聲分離裝置 `mps` / `cpu`，預設 `mps` |
| `--no-separation` | 略過人聲分離 |
| `--format` | `vtt` / `srt` / `both`，預設 `vtt` |
| `--keep-temp` | 保留暫存目錄（除錯） |

## 設定

可用環境變數或 `.env`（複製 `.env.example`）覆寫預設，詳見 `config.py`。

## 流程

```
input → ffmpeg 抽音軌(stereo/44.1k) → Demucs 取人聲 → mlx-whisper 辨識 → VTT/SRT
```
