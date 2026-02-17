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

from app.core.stats import format_stats

from app.audio.tts_sapi import SapiTTS
from app.audio.stt_stub import StubSTT

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
    tts = SapiTTS()
    stt = StubSTT()
    speak_enabled = False

    llm = LLMClient(cfg.model, timeout=60.0, retries=1)

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
                console.print(format_stats(cfg))
                continue
            if user_text == "/ptt":
                # 1) 取得語音辨識結果（目前是 stub）
                spoken_text = stt.listen_once()
                if not spoken_text:
                    console.print("(空輸入，已取消)")
                    continue
                # 2) 用辨識文字當作 user_text 進同一套流程
                user_text = spoken_text
                console.print(f"[cyan]Nick(STT)[/cyan] {user_text}")
                # 注意：不要 continue，讓它落到下面 messages = build_messages(...) 的流程
            if user_text.startswith("/speak"):
                parts = user_text.split()
                if len(parts) == 2 and parts[1].lower() in ("on", "off"):
                    speak_enabled = (parts[1].lower() == "on")
                    console.print(f"speak_enabled={speak_enabled}")
                    log_event(cfg.log_dir, f"speak_enabled={speak_enabled}")
                else:
                    console.print("用法：/speak on 或 /speak off")
                continue

        messages = build_messages(cfg, user_text)

        t0 = datetime.now()
        try:
            result = llm.chat(messages)
            assistant_text = result["text"]
            latency = result["latency"]
            tps = result["tps"]
        except Exception as e:
            log_event(cfg.log_dir, f"LLM error: {e}")
            console.print(f"[red]LLM 呼叫失敗[/red]: {e}\n")
            continue

        console.print(f"[green]Nayuki[/green] ({latency:.2f}s | ~{tps:.1f} tok/s)\n{assistant_text}\n")
        if speak_enabled:
            tts.speak(assistant_text)

        ts = now_iso()
        append_jsonl(cfg.chat_log, {"role": "user", "content": user_text, "ts": ts})
        append_jsonl(cfg.chat_log, {"role": "assistant", "content": assistant_text, "ts": ts})

        try:
            maybe_summarize(cfg, llm)
        except Exception as e:
            log_event(cfg.log_dir, f"Summarize error: {e}")

if __name__ == "__main__":
    main()