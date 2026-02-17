from dataclasses import dataclass

@dataclass(frozen=True)
class CommandResult:
    handled: bool
    output: str = ""

def handle_command(cmd: str) -> CommandResult:
    cmd = cmd.strip()
    if cmd in ("/exit", "/mem", "/reset", "/stats"):
        return CommandResult(True)
    if cmd.startswith("/speak"):
        return CommandResult(True)
    return CommandResult(False)
    