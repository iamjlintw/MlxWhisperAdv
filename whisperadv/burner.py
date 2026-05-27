"""用 ffmpeg 把字幕燒錄（硬字幕）進影片，輸出新的 mp4。

進度透過 on_progress(0~100) 回呼回報（解析 ffmpeg -progress 的 out_time_us）。
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import config


def _ffprobe_value(path: str, entries: str) -> str:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", entries,
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return r.stdout.strip()


def has_video(path: str) -> bool:
    """輸入是否含影像串流（純音檔不能燒字幕）。"""
    out = _ffprobe_value(path, "stream=codec_type")
    return "video" in out.splitlines()


def _duration(path: str) -> float:
    try:
        return float(_ffprobe_value(path, "format=duration").splitlines()[0])
    except (ValueError, IndexError):
        return 0.0


def burn(video_path: str, subtitle_path: str, out_path: str, on_progress=None,
         font: str = None, font_size: int = None) -> str:
    """把 subtitle_path 燒進 video_path，輸出到 out_path。回傳 out_path。

    字幕先複製到 ascii 暫存路徑，避免 subtitles 濾鏡對含 CJK/特殊字元路徑的跳脫問題。
    音訊直接複製，僅重編碼影像（libx264）。
    """
    font = font or config.BURN_FONT
    font_size = font_size or config.BURN_FONT_SIZE
    duration = _duration(video_path)

    tmp_sub = Path(tempfile.mkdtemp(prefix="mlxburn_")) / ("sub" + Path(subtitle_path).suffix)
    shutil.copyfile(subtitle_path, tmp_sub)
    err_log = str(tmp_sub.parent / "ffmpeg.err")

    style = (
        f"FontName={font},FontSize={font_size},"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0"
    )
    vf = f"subtitles={tmp_sub}:force_style='{style}'"
    cmd = [
        config.FFMPEG_BIN, "-y",
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-progress", "pipe:1", "-nostats",
        str(out_path),
    ]

    try:
        with open(err_log, "w") as errf:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=errf, text=True, bufsize=1)
            for line in proc.stdout:
                if line.startswith("out_time_us=") and duration > 0 and on_progress:
                    try:
                        sec = int(line.strip().split("=", 1)[1]) / 1_000_000
                        on_progress(max(0, min(100, sec / duration * 100)))
                    except ValueError:
                        pass
            proc.wait()
        if proc.returncode != 0:
            msg = Path(err_log).read_text(errors="ignore")[-2000:]
            raise RuntimeError(f"ffmpeg 燒錄字幕失敗：\n{msg}")
        if on_progress:
            on_progress(100)
        return str(out_path)
    finally:
        shutil.rmtree(tmp_sub.parent, ignore_errors=True)
