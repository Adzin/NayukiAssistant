from __future__ import annotations
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel
import tempfile
import os

class WhisperSTT:
    def __init__(self, model_size: str = "base"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def listen_once(self, duration: int = 5, samplerate: int = 16000) -> str:
        print(f"開始錄音 {duration} 秒...")
        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        print("錄音完成，辨識中...")
    
        tmp_path = None
        try:
            # 先產生檔名，但不要保持開啟狀態
            fd, tmp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
    
            wav.write(
                tmp_path,
                samplerate,
                (recording * 32767).astype(np.int16),
            )
    
            segments, _ = self.model.transcribe(
                tmp_path,
                language="zh",
            )
    
            text = "".join([seg.text for seg in segments])
            return text.strip()
    
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)