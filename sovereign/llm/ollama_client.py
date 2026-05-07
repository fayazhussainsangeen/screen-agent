import json
from typing import Generator

import requests


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _payload(self, prompt: str) -> dict:
        return {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": 0.2},
        }

    def stream(self, prompt: str) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/generate"
        try:
            resp = requests.post(url, json=self._payload(prompt), stream=True, timeout=self.timeout)
        except requests.RequestException as exc:
            raise RuntimeError("Ollama is not running. Start it with: ollama serve") from exc

        if resp.status_code == 404:
            raise RuntimeError(f"Model not found. Run: ollama pull {self.model}")

        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            data = json.loads(line)
            token = data.get("response", "")
            if token:
                yield token

    def complete(self, prompt: str) -> str:
        return "".join(self.stream(prompt)).strip()
