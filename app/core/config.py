from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class AppConfig:
    root: Path
    model: str
    history_keep: int = 14
    summarize_every: int = 20

    @property
    def mem_dir(self) -> Path:
        return self.root / "memory"

    @property
    def log_dir(self) -> Path:
        return self.root / "logs"

    @property
    def chat_log(self) -> Path:
        return self.mem_dir / "chat_log.jsonl"

    @property
    def long_memory(self) -> Path:
        return self.mem_dir / "long_memory.txt"

def load_config(project_root: Path) -> AppConfig:
    model = os.getenv("MODEL", "qwen2.5:7b")
    return AppConfig(root=project_root, model=model)