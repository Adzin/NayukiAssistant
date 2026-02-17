from pathlib import Path
from datetime import datetime

def log_event(log_dir: Path, msg: str) -> None:
    log_dir.mkdir(exist_ok=True)
    p = log_dir / "app.log"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {msg}\n")