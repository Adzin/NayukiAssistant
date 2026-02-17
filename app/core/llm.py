from typing import List, Dict
import ollama
import time

class LLMClient:
    def __init__(self, model: str, timeout: float = 60.0, retries: int = 1):
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def chat(self, messages: List[Dict]) -> Dict:
        attempt = 0

        while True:
            try:
                t0 = time.time()
                resp = ollama.chat(model=self.model, messages=messages)
                dt = time.time() - t0

                text = resp["message"]["content"]
                approx_tokens = max(len(text) // 4, 1)

                return {
                    "text": text,
                    "latency": dt,
                    "approx_tokens": approx_tokens,
                    "tps": approx_tokens / dt if dt > 0 else 0.0,
                }

            except Exception as e:
                attempt += 1
                if attempt > self.retries:
                    raise RuntimeError(f"LLM failed after {self.retries} retries: {e}")
                time.sleep(1)