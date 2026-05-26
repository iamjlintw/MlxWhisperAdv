"""串接整條流程：抽音軌 → (人聲分離) → 辨識 → 輸出字幕。"""

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

import config
from whisperadv import audio, separator, subtitles, transcriber


def run(
    input_path: str,
    output: Optional[str] = None,
    model: Optional[str] = None,
    language: Optional[str] = None,
    device: Optional[str] = None,
    separate: bool = True,
    fmt: Optional[str] = None,
    keep_temp: bool = False,
) -> List[str]:
    """執行完整 pipeline，回傳產生的字幕檔路徑清單。

    output：字幕輸出前綴（不含副檔名）；預設與輸入同目錄同檔名。
    separate：是否做人聲分離（背景音很乾淨的檔可關閉以加速）。
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"找不到輸入檔：{input_path}")

    fmt = fmt or config.DEFAULT_FORMAT
    out_base = output or str(src.with_suffix(""))

    tmp_dir = tempfile.mkdtemp(prefix="mlxwhisperadv_")
    try:
        # 1) 抽音軌
        wav = audio.extract_audio(str(src), str(Path(tmp_dir) / f"{src.stem}.wav"))

        # 2) 人聲分離（可選）
        if separate:
            speech = separator.separate_vocals(wav, str(Path(tmp_dir) / "demucs"), device=device)
        else:
            speech = wav

        # 3) 語音辨識
        result = transcriber.transcribe(speech, model=model, language=language)
        segments = result.get("segments", [])

        # 4) 輸出字幕
        written = subtitles.write_subtitles(segments, out_base, fmt)
        return written
    finally:
        if keep_temp:
            print(f"暫存目錄保留於：{tmp_dir}")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)
