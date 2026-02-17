from __future__ import annotations
from abc import ABC, abstractmethod

class TTS(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak the given text (blocking or non-blocking is implementation-defined)."""
        raise NotImplementedError

class STT(ABC):
    @abstractmethod
    def listen_once(self) -> str:
        """Capture audio and return transcribed text."""
        raise NotImplementedError