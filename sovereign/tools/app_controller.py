from __future__ import annotations

import os
import subprocess
import sys

import psutil


class AppController:
    def execute(self, args: dict) -> str:
        action = args.get("action")
        if not action or not hasattr(self, action):
            return f"Unsupported app action: {action}"
        call_args = {k: v for k, v in args.items() if k != "action"}
        return str(getattr(self, action)(**call_args))

    def open_app(self, app_name: str) -> str:
        if sys.platform.startswith("win"):
            os.startfile(app_name)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name])
        return f"Opened app: {app_name}"

    def close_app(self, app_name: str) -> str:
        terminated = 0
        for proc in psutil.process_iter(attrs=["name"]):
            name = (proc.info.get("name") or "").lower()
            if app_name.lower() in name:
                proc.terminate()
                terminated += 1
        return f"Terminated {terminated} process(es) for {app_name}"

    def list_running(self) -> str:
        names = sorted({(p.info.get("name") or "") for p in psutil.process_iter(attrs=["name"]) if p.info.get("name")})
        return "\n".join(names)

    def focus_app(self, app_name: str) -> str:
        if sys.platform.startswith("linux"):
            subprocess.run(["wmctrl", "-a", app_name], check=False)
            return f"Focused app (Linux/wmctrl): {app_name}"
        return f"Focus operation not supported on {sys.platform}."
