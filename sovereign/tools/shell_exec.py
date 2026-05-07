from __future__ import annotations

import re
import subprocess


class ShellExecutor:
    BLOCKLIST = [
        r"rm\s+-rf\s+/",
        r"mkfs",
        r"dd\s+if=",
        r":\(\)\s*\{\s*:\|:&\s*\};:",
        r"chmod\s+777\s+/",
        r">\s*/dev/sda",
        r"/etc",
        r"/sys",
        r"/boot",
    ]

    def __init__(self, long_term, safe_shell: bool = True):
        self.long_term = long_term
        self.safe_shell = safe_shell

    def execute(self, args: dict) -> str:
        command = args.get("command", "")
        if not command:
            return "No command provided."

        if self.safe_shell and self._blocked(command):
            return "Blocked by SAFE_SHELL policy."

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}".strip()
            self.long_term.log_command(command, output)
            return output
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds."
        except Exception as exc:
            return f"Shell execution failed: {exc}"

    def _blocked(self, command: str) -> bool:
        for pattern in self.BLOCKLIST:
            if re.search(pattern, command):
                return True
        return False
