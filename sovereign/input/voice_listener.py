from __future__ import annotations

import time
from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class VoiceListener:
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        sample_rate: int = 16000,
        block_duration: float = 0.25,
        vad_threshold: float = 0.01,
        silence_seconds: float = 1.5,
        wake_word: str = "",
    ):
        self.model = WhisperModel(model_size, device=device)
        self.sample_rate = sample_rate
        self.block_duration = block_duration
        self.vad_threshold = vad_threshold
        self.silence_seconds = silence_seconds
        self.wake_word = (wake_word or "").strip().lower()

    def get_input(self) -> str:
        frames = []
        ring = deque(maxlen=int(self.silence_seconds / self.block_duration))
        in_speech = False

        while True:
            chunk = sd.rec(
                int(self.sample_rate * self.block_duration),
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            audio = chunk.flatten()
            rms = float(np.sqrt(np.mean(audio ** 2)))

            if rms > self.vad_threshold:
                in_speech = True
                frames.append(audio)
                ring.clear()
                continue

            if in_speech:
                ring.append(audio)
                if len(ring) < ring.maxlen:
                    continue

                full = np.concatenate(frames + list(ring)) if frames else np.array([], dtype=np.float32)
                if full.size == 0:
                    in_speech = False
                    frames = []
                    ring.clear()
                    continue

                segments, _ = self.model.transcribe(full, language="en")
                text = " ".join(seg.text.strip() for seg in segments).strip()
                in_speech = False
                frames = []
                ring.clear()

                if not text:
                    continue

                if self.wake_word:
                    lowered = text.lower()
                    if self.wake_word not in lowered:
                        continue
                    text = lowered.replace(self.wake_word, "", 1).strip()
                    if not text:
                        continue

                return text

            time.sleep(0.01)
