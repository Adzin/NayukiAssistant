from __future__ import annotations

class StubSTT:
    """
    MVP 用的 STT 替身：
    - listen_once() 先用鍵盤輸入文字，模擬語音辨識結果
    - 下一步會換成 WhisperSTT（真錄音 + 辨識）
    """
    def listen_once(self) -> str:
        return input("STT(Stub) 請輸入你要當作語音辨識的文字： ").strip()