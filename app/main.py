from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

from app.core.config import load_config
from app.core.logger import log_event
from app.core.memory import (
    append_jsonl,
    load_recent,
    clear_chat,
    load_long_memory,
    write_long_memory,
    now_iso,
)
from app.core.llm import LLMClient
from app.core.commands import handle_command

load_dotenv()
console = Console()

SYSTEM_PROMPT = """你叫 Nayuki，是Nick的本地端生活助理。
風格：簡潔、務實、像工程夥伴，不使用emoji。
原則：
- 優先給出可執行的下一步與指令
- 不確定就列出要確認的項目與最小測試方法
- 回答以繁體中文為主
"""

def build_messages(cfg, user_text: str):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]

    mem = load_long_memory(cfg.long_memory)
    if mem:
        msgs.append({"role": "system", "content": f"長期記憶（摘要）:\n{mem}"})

    for m in load_recent(cfg.chat_log, cfg.history_keep):
        if "role" in m and "content" in m:
            msgs.append({"role": m["role"], "content": m["content"]})

    msgs.append({"role": "user", "content": user_text})
    return msgs

def maybe_summarize(cfg, llm: LLMClient):
    if not cfg.chat_log.exists():
        return
    lines = cfg.chat_log.read_text(encoding="utf-8").splitlines()
    if len(lines) < cfg.summarize_every or (len(lines) % cfg.summarize_every != 0):
        return

    recent = "\n".join(lines[-cfg.summarize_every:])
    prompt = (
        "請把以下對話紀錄做成 5 行以內的長期記憶摘要，"
        "包含：Nick目前在做的事、偏好（例如不使用emoji）、"
        "以及近期決策。用繁體中文。\n\n"
        f"{recent}"
    )
    summary = llm.summarize(prompt)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    old = load_long_memory(cfg.long_memory)
    new_text = (old + "\n" + f"[{stamp}]\n{summary}\n").strip()
    write_long_memory(cfg.long_memory, new_text)

def main():
    cfg = load_config(Path(__file__).resolve().parents[1])
    cfg.mem_dir.mkdir(exist_ok=True)
    cfg.log_dir.mkdir(exist_ok=True)

    llm = LLMClient(cfg.model)

    console.print(f"[bold]NayukiAssistant[/bold] model={cfg.model}")
    console.print("指令：/exit 離開、/mem 查看長期記憶、/reset 清空對話、/stats 狀態\n")

    log_event(cfg.log_dir, f"App start model={cfg.model}")

    while True:
        user_text = Prompt.ask("[cyan]Nick[/cyan]").strip()

        cmd = handle_command(user_text)
        if cmd.handled:
            if user_text == "/exit":
                log_event(cfg.log_dir, "App exit")
                break
            if user_text == "/mem":
                mem = load_long_memory(cfg.long_memory)
                console.print(mem if mem else "(尚無長期記憶)")
                continue
            if user_text == "/reset":
                clear_chat(cfg.chat_log)
                console.print("已清空 chat_log.jsonl（長期記憶未清除）\n")
                log_event(cfg.log_dir, "Chat reset")
                continue
            if user_text == "/stats":
                console.print(f"model={cfg.model} history_keep={cfg.history_keep} summarize_every={cfg.summarize_every}")
                continue

        messages = build_messages(cfg, user_text)

        t0 = datetime.now()
        try:
            assistant_text = llm.chat(messages)
        except Exception as e:
            log_event(cfg.log_dir, f"LLM error: {e}")
            console.print(f"[red]LLM 呼叫失敗[/red]: {e}\n")
            continue

        dt = (datetime.now() - t0).total_seconds()
        console.print(f"[green]Nayuki[/green] ({dt:.2f}s)\n{assistant_text}\n")

        ts = now_iso()
        append_jsonl(cfg.chat_log, {"role": "user", "content": user_text, "ts": ts})
        append_jsonl(cfg.chat_log, {"role": "assistant", "content": assistant_text, "ts": ts})

        try:
            maybe_summarize(cfg, llm)
        except Exception as e:
            log_event(cfg.log_dir, f"Summarize error: {e}")

if __name__ == "__main__":
    main()