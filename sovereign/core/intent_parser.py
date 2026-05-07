import json
import logging
import re
from typing import Any, Dict


class IntentParser:
    def parse(self, raw_output: str) -> Dict[str, Any]:
        payload = self._parse_json(raw_output)
        if payload is None:
            logging.debug("Intent parse failed, using fallback. raw=%s", raw_output)
            return {"tool": "none", "args": {}, "reply": raw_output.strip()}

        if not all(k in payload for k in ("tool", "args", "reply")):
            logging.debug("Intent keys missing, using fallback. payload=%s", payload)
            return {"tool": "none", "args": {}, "reply": raw_output.strip()}

        if not isinstance(payload.get("args"), dict):
            payload["args"] = {}

        return {
            "tool": str(payload.get("tool", "none")),
            "args": payload.get("args", {}),
            "reply": str(payload.get("reply", "")),
        }

    def _parse_json(self, raw_output: str) -> Dict[str, Any] | None:
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            pass

        # Try fenced JSON first because many models wrap structured output in markdown.
        fenced_matches = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, flags=re.DOTALL)
        for snippet in reversed(fenced_matches):
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                continue

        # Fall back to scanning all object-like snippets and use the last valid JSON object.
        candidates = re.findall(r"\{.*?\}", raw_output, flags=re.DOTALL)
        for snippet in reversed(candidates):
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                continue

        return None
