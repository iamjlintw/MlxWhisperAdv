#!/usr/bin/env python3
"""MlxWhisperAdv CLI：影片/音檔 → 人聲分離 → Whisper → 字幕。

範例：
    python main.py input.mp4
    python main.py input.mp4 -o out/myvideo --model mlx-community/whisper-base-mlx --format both
    python main.py podcast.mp3 --no-separation --language zh
"""

import argparse
import sys

import config
from whisperadv import pipeline
from whisperadv.ui import make_reporter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="MlxWhisperAdv",
        description="macOS (Apple Silicon) 專用字幕產生器：Demucs 人聲分離 + mlx-whisper 辨識。",
    )
    p.add_argument("input", help="輸入影片或音檔路徑")
    p.add_argument("-o", "--output", help="輸出字幕前綴（不含副檔名）；預設與輸入同名")
    p.add_argument("--model", default=None, help=f"Whisper 模型（預設 {config.WHISPER_MODEL}）")
    p.add_argument("--language", default=None, help="語言碼如 zh / en；預設自動偵測")
    p.add_argument("--device", default=None, choices=["mps", "cpu"], help="人聲分離裝置（預設 mps）")
    p.add_argument("--no-separation", action="store_true", help="略過人聲分離（背景乾淨時加速）")
    p.add_argument("--format", default=None, choices=["vtt", "srt", "both"],
                   help=f"字幕格式（預設 {config.DEFAULT_FORMAT}）")
    p.add_argument("--keep-temp", action="store_true", help="保留暫存目錄（除錯用）")
    p.add_argument("--no-tui", action="store_true", help="關閉 TUI 進度表，改純文字輸出")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    # 非終端機（如導向檔案）或使用者指定時，退回純文字。
    use_tui = not args.no_tui and sys.stdout.isatty()
    reporter = make_reporter(use_tui)

    try:
        written = pipeline.run(
            input_path=args.input,
            output=args.output,
            model=args.model,
            language=args.language,
            device=args.device,
            separate=not args.no_separation,
            fmt=args.format,
            keep_temp=args.keep_temp,
            reporter=reporter,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1

    print("完成，已輸出：")
    for path in written:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
