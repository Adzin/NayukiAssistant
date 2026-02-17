from typing import List, Dict, Optional
import ollama

class LLMClient:
    def __init__(self, model: str):
        self.model = model

    def chat(self, messages: List[Dict], timeout_s: Optional[float] = None) -> str:
        # ollama python client目前不一定支援 timeout 參數，
        # timeout 我們先留介面，之後改用 requests 直打 localhost API 時再實作。
        resp = ollama.chat(model=self.model, messages=messages)
        return resp["message"]["content"]

    def summarize(self, text: str) -> str:
        resp = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是負責整理長期記憶的助手，務必精簡、可用。"},
                {"role": "user", "content": text},
            ],
        )
        return resp["message"]["content"].strip()