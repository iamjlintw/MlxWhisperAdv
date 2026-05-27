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

## 資料夾

| 資料夾 | 用途 |
|---|---|
| `import/` | 放要加字幕的影片/音檔；不帶參數執行時 TUI 從這裡選 |
| `output/` | 字幕輸出位置（預設） |

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

### 兩條路線（TUI，推薦）

不帶任何參數執行，TUI 開頭會先讓你選路線：

```bash
./run.sh
```

```
選擇要做什麼
  ❯ 產生字幕    影片/音檔 → 辨識 → 字幕檔
    燒錄字幕    影片 + 字幕 → 內嵌字幕影片
```

- **產生字幕**：從 `import/` 選檔 → 選模型（base / small / large-v3）→ 字幕輸出到 `output/`
- **燒錄字幕**：從 `output/` 選一部影片 + 一份字幕 → 燒成 `output/<檔名>_內嵌字幕.mp4`
  （不跑辨識、不需模型等設定）

選單操作：`↑`/`↓`（或 `j`/`k`）移動、`Enter` 選擇、`q` 取消；
非終端機環境自動改為輸入編號。`run.sh` 會用 venv 執行並透傳參數。

### 直接指定檔案（產生字幕）

```bash
# 指定輸入（預設輸出到 output/）
./run.sh input.mp4

# 自訂輸出、模型、格式
./run.sh input.mp4 -o out/myvideo --model mlx-community/whisper-base-mlx --format both

# 純語音（背景乾淨）可略過人聲分離以加速
./run.sh podcast.mp3 --no-separation --language zh
```

> 燒錄字幕是 TUI 專屬路線；指定輸入檔時一律走「產生字幕」。

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
| `--no-tui` | 關閉 TUI 進度表，改純文字輸出 |
| `--no-zhtw` | 關閉中文轉繁體（預設會把中文字幕轉成繁體台灣用語） |

> 燒錄字幕（內嵌字幕，白字黑邊、PingFang TC）走 TUI 的「燒錄字幕」路線，不是參數。

### 進度顯示

在終端機執行時會顯示 **TUI 進度表**，逐階段呈現圖示 / 名稱 / 進度條 / 百分比 / 耗時：

```
✅ 抽取音軌  ━━━━━━━━━━━━━━━━ 100%  0:00:02
▶  人聲分離  ━━━━━━━━╶╶╶╶╶╶╶╶  52%  0:01:10
⏳ 語音辨識  ╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶    0%  -:--:--
⏳ 輸出字幕  ╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶    0%  -:--:--
```

人聲分離（Demucs）會顯示實際百分比；其餘階段以脈動進度條表示處理中。
輸出導向檔案（非終端機）或加 `--no-tui` 時，自動改為純文字。

### 繁體中文輸出

Whisper 對中文常輸出簡體，本工具預設用 **OpenCC（s2twp）** 把中文字幕轉成
**繁體（台灣用語）**，例如「信息→資訊、視頻→影片、軟件→軟體」。
只在偵測語言為中文時轉換，不影響其他語言；加 `--no-zhtw` 可關閉。

## 設定

可用環境變數或 `.env`（複製 `.env.example`）覆寫預設，詳見 `config.py`。

## 流程

```
input → ffmpeg 抽音軌(stereo/44.1k) → Demucs 取人聲 → mlx-whisper 辨識 → VTT/SRT
```
