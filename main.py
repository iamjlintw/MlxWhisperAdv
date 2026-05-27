#!/usr/bin/env python3
"""MlxWhisperAdv：兩條獨立路線。

- 產生字幕：影片/音檔 → 人聲分離 → Whisper → 字幕檔。
- 燒錄字幕：現有影片 + 現有字幕 → 內嵌字幕影片（不跑辨識）。

不帶參數執行會進 TUI，先選路線；指定輸入檔則直接走產生字幕。
素材放 import/，成果出 output/。

範例：
    python main.py                       # TUI：先選產生字幕 / 燒錄字幕
    python main.py input.mp4             # 直接產生字幕
    python main.py input.mp4 --model mlx-community/whisper-base-mlx --format both
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
        description="macOS (Apple Silicon) 專用字幕工具：產生字幕 / 燒錄字幕兩條路線。",
    )
    p.add_argument("input", nargs="?", default=None,
                   help="輸入影片或音檔；省略則進 TUI 選路線")
    p.add_argument("-o", "--output", help="輸出字幕前綴（不含副檔名）；預設 output/<檔名>")
    p.add_argument("--model", default=None, help=f"Whisper 模型（預設 {config.WHISPER_MODEL}）")
    p.add_argument("--language", default=None, help="語言碼如 zh / en；預設自動偵測")
    p.add_argument("--device", default=None, choices=["mps", "cpu"], help="人聲分離裝置（預設 mps）")
    p.add_argument("--no-separation", action="store_true", help="略過人聲分離（背景乾淨時加速）")
    p.add_argument("--format", default=None, choices=["vtt", "srt", "both"],
                   help=f"字幕格式（預設 {config.DEFAULT_FORMAT}）")
    p.add_argument("--keep-temp", action="store_true", help="保留暫存目錄（除錯用）")
    p.add_argument("--no-tui", action="store_true", help="關閉 TUI 進度表，改純文字輸出")
    p.add_argument("--no-zhtw", action="store_true", help="關閉中文字幕轉繁體（台灣用語）")
    return p


def _make_reporter(args):
    # 非終端機（如導向檔案）或使用者指定時，退回純文字。
    return make_reporter(not args.no_tui and sys.stdout.isatty())


def _report_done(paths) -> int:
    print("完成，已輸出：")
    for path in paths:
        print(f"  - {path}")
    return 0


def run_subtitle(args, input_path: str) -> int:
    """產生字幕路線。"""
    if args.model:
        model = args.model
    elif sys.stdin.isatty():
        model = picker.select_model()
        if model is None:
            print("已取消。")
            return 1
    else:
        model = config.WHISPER_MODEL

    if args.output:
        output = args.output
    else:
        Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        output = str(Path(config.OUTPUT_DIR) / Path(input_path).stem)

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
            to_tw=not args.no_zhtw and config.CONVERT_TO_TW,
            reporter=_make_reporter(args),
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    return _report_done(written)


def run_burn(args) -> int:
    """燒錄字幕路線：影片與字幕都從 output/ 選。"""
    videos = picker.list_videos(config.OUTPUT_DIR)
    if not videos:
        print(f"錯誤：output 資料夾沒有影片可燒錄：{config.OUTPUT_DIR}", file=sys.stderr)
        return 1
    video = picker.select_file(videos, title="選擇要燒錄字幕的影片")
    if video is None:
        print("已取消。")
        return 1

    subs = picker.list_subtitles(config.OUTPUT_DIR)
    if not subs:
        print(f"錯誤：output 資料夾沒有字幕（.vtt/.srt）：{config.OUTPUT_DIR}", file=sys.stderr)
        return 1
    sub = picker.select_file(subs, title="選擇要燒進影片的字幕")
    if sub is None:
        print("已取消。")
        return 1

    out_path = args.output or str(Path(config.OUTPUT_DIR) / f"{video.stem}_內嵌字幕.mp4")
    try:
        burned = pipeline.burn_only(str(video), str(sub), out_path, reporter=_make_reporter(args))
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    return _report_done([burned])


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    # 有指定輸入檔 → 直接產生字幕。
    if args.input:
        return run_subtitle(args, args.input)

    # 無輸入檔 → TUI 選路線。
    if not sys.stdin.isatty():
        print("錯誤：未指定輸入檔。請指定輸入檔，或在終端機執行以使用選單。", file=sys.stderr)
        return 1

    mode = picker.select_mode()
    if mode is None:
        print("已取消。")
        return 1

    if mode == "burn":
        return run_burn(args)

    # 產生字幕：從 import/ 選檔。
    files = picker.list_media(config.IMPORT_DIR)
    if not files:
        print(f"錯誤：import 資料夾沒有可用的媒體檔：{config.IMPORT_DIR}", file=sys.stderr)
        print("請把影片/音檔放進 import/ 後再執行。", file=sys.stderr)
        return 1
    selected = picker.select_file(files)
    if selected is None:
        print("已取消。")
        return 1
    return run_subtitle(args, str(selected))


if __name__ == "__main__":
    raise SystemExit(main())
