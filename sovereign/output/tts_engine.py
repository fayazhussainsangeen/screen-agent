from __future__ import annotations

import threading
from importlib import import_module


class TTSEngine:
    def __init__(self, engine: str = "pyttsx3", rate: int = 175):
        self.engine_name = engine
        self.rate = rate
        self._thread = None

        self.engine = None
        self.coqui = None

        if self.engine_name == "pyttsx3":
            import pyttsx3

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
        elif self.engine_name == "coqui":
            tts_module = import_module("TTS.api")
            self.coqui = tts_module.TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

    def speak(self, text: str) -> None:
        if not text:
            return

        def _worker():
            if self.engine_name == "pyttsx3" and self.engine is not None:
                self.engine.say(text)
                self.engine.runAndWait()
            elif self.engine_name == "coqui" and self.coqui is not None:
                self.coqui.tts_to_file(text=text, file_path="/tmp/sovereign_tts.wav")

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self.engine_name == "pyttsx3" and self.engine is not None:
            self.engine.stop()

    def set_voice(self, voice_id: str) -> None:
        if self.engine_name == "pyttsx3" and self.engine is not None:
            self.engine.setProperty("voice", voice_id)
