"""把 Whisper segments 轉成 WebVTT / SRT 字幕檔。"""

from pathlib import Path
from typing import List


def _fmt_ts(seconds: float, sep: str) -> str:
    """秒數 → HH:MM:SS<sep>mmm。VTT 用 '.'，SRT 用 ','。"""
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def write_vtt(segments: List[dict], out_path: str) -> str:
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = _fmt_ts(seg["start"], ".")
        end = _fmt_ts(seg["end"], ".")
        text = seg["text"].strip()
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path


def write_srt(segments: List[dict], out_path: str) -> str:
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = _fmt_ts(seg["start"], ",")
        end = _fmt_ts(seg["end"], ",")
        text = seg["text"].strip()
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path


def write_subtitles(segments: List[dict], out_base: str, fmt: str) -> List[str]:
    """依 fmt（vtt / srt / both）輸出，回傳實際產生的檔案路徑清單。

    out_base 為不含副檔名的輸出路徑前綴。
    """
    written = []
    if fmt in ("vtt", "both"):
        written.append(write_vtt(segments, f"{out_base}.vtt"))
    if fmt in ("srt", "both"):
        written.append(write_srt(segments, f"{out_base}.srt"))
    if not written:
        raise ValueError(f"未知的字幕格式：{fmt}")
    return written
