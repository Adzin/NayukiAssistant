import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

def load_recent(chat_log: Path, n: int) -> List[Dict]:
    msgs = read_jsonl(chat_log)
    return msgs[-n:] if n > 0 else []

def clear_chat(chat_log: Path) -> None:
    if chat_log.exists():
        chat_log.unlink()

def load_long_memory(long_memory: Path) -> str:
    if not long_memory.exists():
        return ""
    return long_memory.read_text(encoding="utf-8").strip()

def write_long_memory(long_memory: Path, text: str) -> None:
    long_memory.parent.mkdir(exist_ok=True)
    long_memory.write_text(text.strip() + "\n", encoding="utf-8")

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")