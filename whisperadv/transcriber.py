"""以 mlx-whisper 做語音辨識（Apple Silicon GPU 原生加速）。"""

from typing import Optional

import mlx_whisper

import config


def transcribe(audio_path: str, model: str = None, language: Optional[str] = None) -> dict:
    """辨識音檔，回傳 mlx_whisper 的結果 dict（含 segments）。

    model 預設取自 config.WHISPER_MODEL；language=None 代表自動偵測。
    """
    model = model or config.WHISPER_MODEL
    language = language if language is not None else config.WHISPER_LANGUAGE

    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=model,
        language=language,
        word_timestamps=False,
    )
    return result
