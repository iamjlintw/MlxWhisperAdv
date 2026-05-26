#!/usr/bin/env python3
"""MlxWhisperAdv CLI：影片/音檔 → 人聲分離 → Whisper → 字幕。

把要加字幕的檔案放進 import/，不帶參數執行即可在 TUI 選單中挑選；
字幕預設輸出到 output/。

範例：
    python main.py                       # 從 import/ 選檔，輸出到 output/
    python main.py input.mp4             # 指定檔案
    python main.py input.mp4 -o out/myvideo --model mlx-community/whisper-base-mlx --format both
    python main.py podcast.mp3 --no-separation --language zh
"""

import argparse
import sys
from pathlib import Path

import config
from whisperadv import picker, pipeline
from whisperadv.ui import make_reporter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="MlxWhisperAdv",
        description="macOS (Apple Silicon) 專用字幕產生器：Demucs 人聲分離 + mlx-whisper 辨識。",
    )
    p.add_argument("input", nargs="?", default=None,
                   help="輸入影片或音檔路徑；省略則從 import/ 選單挑選")
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


def _resolve_input(args) -> str:
    """取得輸入檔：有指定就用，否則從 import/ 列檔選擇。回傳路徑，取消回 None。"""
    if args.input:
        return args.input

    files = picker.list_media(config.IMPORT_DIR)
    if not files:
        print(f"錯誤：import 資料夾沒有可用的媒體檔：{config.IMPORT_DIR}", file=sys.stderr)
        print("請把影片/音檔放進 import/ 後再執行，或直接指定輸入檔。", file=sys.stderr)
        return None

    selected = picker.select_file(files)
    if selected is None:
        print("已取消。")
        return None
    return str(selected)


def _resolve_model(args):
    """取得模型：有指定 --model 就用；否則在終端機跳選單，非終端機用預設。"""
    if args.model:
        return args.model
    if sys.stdin.isatty():
        return picker.select_model()  # None 表示取消
    return config.WHISPER_MODEL


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    input_path = _resolve_input(args)
    if input_path is None:
        return 1

    model = _resolve_model(args)
    if model is None:
        print("已取消。")
        return 1

    # 未指定 -o 時，預設輸出到 output/<檔名>。
    if args.output:
        output = args.output
    else:
        Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        output = str(Path(config.OUTPUT_DIR) / Path(input_path).stem)

    # 非終端機（如導向檔案）或使用者指定時，退回純文字。
    use_tui = not args.no_tui and sys.stdout.isatty()
    reporter = make_reporter(use_tui)

    try:
        written = pipeline.run(
            input_path=input_path,
            output=output,
            model=model,
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
