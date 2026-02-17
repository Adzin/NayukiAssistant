from __future__ import annotations
import subprocess
import shlex

class SapiTTS:
    """
    Windows built-in TTS via PowerShell + SAPI.SpVoice.
    Pros: no extra install, stable.
    Cons: voice quality is system dependent.
    """

    def speak(self, text: str) -> None:
        # Escape double quotes for PowerShell string
        safe = text.replace('"', '\\"')
        ps = (
            'Add-Type -AssemblyName System.Speech;'
            '$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;'
            f'$speak.Speak("{safe}");'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
        )