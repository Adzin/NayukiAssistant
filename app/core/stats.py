from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import os
import subprocess

def get_ollama_models() -> str:
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "ollama list failed"
        return result.stdout.strip()
    except Exception as e:
        return f"ollama list error: {e}"

def file_line_count(p: Path) -> int:
    if not p.exists():
        return 0
    # jsonl 用行數當作訊息數（user+assistant 都算）
    return sum(1 for _ in p.open("r", encoding="utf-8"))

def file_size_mb(p: Path) -> float:
    if not p.exists():
        return 0.0
    return p.stat().st_size / (1024 * 1024)

def env_or_unknown(name: str) -> str:
    v = os.getenv(name)
    return v if v else "(unknown)"

def format_stats(cfg) -> str:
    # cfg 是 AppConfig
    chat_lines = file_line_count(cfg.chat_log)
    long_mem_exists = cfg.long_memory.exists()
    long_mem_mb = file_size_mb(cfg.long_memory)

    # Ollama 模型路徑：你已經在 GUI 指到 G:\AI_Project\.ollama\models
    # 這裡顯示 OLLAMA_MODELS（如果有設）與預設提示
    ollama_models = env_or_unknown("OLLAMA_MODELS")

    parts = []
    parts.append(f"model={cfg.model}")
    parts.append(f"history_keep={cfg.history_keep}")
    parts.append(f"summarize_every={cfg.summarize_every}")

    parts.append(f"project_root={cfg.root}")
    parts.append(f"chat_log={cfg.chat_log} (lines={chat_lines})")
    parts.append(f"long_memory={cfg.long_memory} (exists={long_mem_exists}, size={long_mem_mb:.2f}MB)")
    parts.append(f"ollama_models_env={ollama_models}")

    parts.append("\nInstalled models:")
    parts.append(get_ollama_models())

    return "\n".join(parts)