"""把辨識文字轉成繁體中文（台灣用語），使用 OpenCC。

轉換器延遲初始化；若 opencc 未安裝則優雅略過（原文回傳），不讓整條流程失敗。
"""

import config

_cc = None
_failed = False


def _converter():
    global _cc, _failed
    if _cc is None and not _failed:
        try:
            from opencc import OpenCC
            _cc = OpenCC(config.OPENCC_PROFILE)
        except Exception:
            # 未安裝 opencc 或設定檔有誤：標記失敗，後續直接回傳原文。
            _failed = True
    return _cc


def to_traditional(text: str) -> str:
    cc = _converter()
    return cc.convert(text) if cc else text


def convert_segments(segments):
    """就地把每段 text 轉繁體。轉換器不可用時原樣回傳。"""
    cc = _converter()
    if not cc:
        return segments
    for seg in segments:
        if seg.get("text"):
            seg["text"] = cc.convert(seg["text"])
    return segments


def available() -> bool:
    """opencc 是否可用。"""
    return _converter() is not None
