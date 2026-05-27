"""串接整條流程：抽音軌 → (人聲分離) → 辨識 → 輸出字幕。

各階段進度透過 reporter 回報；reporter 可為 TUI（RichReporter）或純文字（NullReporter）。
"""

import contextlib
import io
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

import config
from whisperadv import audio, burner, separator, subtitles, transcriber, zhconv
from whisperadv.ui import NullReporter


def _pick_subtitle(written):
    """燒錄優先用 .vtt，否則用第一個輸出的字幕檔。"""
    for path in written:
        if path.endswith(".vtt"):
            return path
    return written[0]


def _quiet_if(active: bool):
    """active 時把 stderr 吞掉，避免 mlx_whisper 的進度條破壞 TUI 畫面。"""
    if active:
        return contextlib.redirect_stderr(io.StringIO())
    return contextlib.nullcontext()


def run(
    input_path: str,
    output: Optional[str] = None,
    model: Optional[str] = None,
    language: Optional[str] = None,
    device: Optional[str] = None,
    separate: bool = True,
    fmt: Optional[str] = None,
    keep_temp: bool = False,
    to_tw: bool = True,
    burn: bool = False,
    reporter=None,
) -> List[str]:
    """執行完整 pipeline，回傳產生的字幕檔路徑清單。

    output：字幕輸出前綴（不含副檔名）；預設與輸入同目錄同檔名。
    separate：是否做人聲分離（背景音很乾淨的檔可關閉以加速）。
    reporter：進度回報器；None 時不輸出進度。
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"找不到輸入檔：{input_path}")

    reporter = reporter or NullReporter()
    fmt = fmt or config.DEFAULT_FORMAT
    out_base = output or str(src.with_suffix(""))

    # 純音檔不能燒字幕；要求 burn 但無影像串流時，跳過並提示。
    do_burn = burn and burner.has_video(str(src))

    stages = ["抽取音軌"]
    if separate:
        stages.append("人聲分離")
    stages += ["語音辨識", "輸出字幕"]
    if do_burn:
        stages.append("燒錄字幕")

    tmp_dir = tempfile.mkdtemp(prefix="mlxwhisperadv_")
    try:
        with reporter:
            reporter.header({
                "輸入": src.name,
                "模型": model or config.WHISPER_MODEL,
                "人聲分離": ("是（%s）" % (device or config.SEPARATION_DEVICE)) if separate else "否",
                "格式": fmt,
            })
            reporter.add_stages(stages)
            if burn and not do_burn:
                reporter.note("輸入無影像串流（純音檔），略過燒錄字幕。")
            try:
                # 1) 抽音軌
                reporter.start_stage("抽取音軌")
                wav = audio.extract_audio(str(src), str(Path(tmp_dir) / f"{src.stem}.wav"))
                reporter.finish_stage()

                # 2) 人聲分離（可選）
                if separate:
                    reporter.start_stage("人聲分離", total=100)
                    speech = separator.separate_vocals(
                        wav, str(Path(tmp_dir) / "demucs"),
                        device=device, on_progress=reporter.update,
                    )
                    reporter.finish_stage()
                else:
                    speech = wav

                # 3) 語音辨識
                reporter.start_stage("語音辨識")
                with _quiet_if(reporter.live):
                    result = transcriber.transcribe(speech, model=model, language=language)
                segments = result.get("segments", [])
                # 中文才做簡→繁（台灣用語）轉換，避免動到其他語言。
                if to_tw and result.get("language") == "zh":
                    zhconv.convert_segments(segments)
                reporter.finish_stage()

                # 4) 輸出字幕
                reporter.start_stage("輸出字幕")
                Path(out_base).parent.mkdir(parents=True, exist_ok=True)
                written = subtitles.write_subtitles(segments, out_base, fmt)
                reporter.finish_stage()

                # 5) 燒錄硬字幕（可選）
                if do_burn:
                    reporter.start_stage("燒錄字幕", total=100)
                    burned = burner.burn(
                        str(src), _pick_subtitle(written), f"{out_base}_硬字幕.mp4",
                        on_progress=reporter.update,
                    )
                    reporter.finish_stage()
                    written.append(burned)
            except Exception:
                reporter.error_current()
                raise
        return written
    finally:
        if keep_temp:
            reporter.note(f"暫存目錄保留於：{tmp_dir}")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)
