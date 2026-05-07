from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class TerminalDisplay:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.console = Console()

    def show_response(self, text: str) -> None:
        panel = Panel(text, title=self.agent_name, border_style="cyan")
        self.console.print(panel)

    def show_tool_call(self, tool: str, args: dict) -> None:
        self.console.print(f"[bold yellow]Tool:[/bold yellow] {tool} {args}")

    def show_tool_result(self, result: str) -> None:
        self.console.print(f"[bold green]Result:[/bold green] {result}")

    def show_error(self, msg: str) -> None:
        self.console.print(f"[bold red]Error:[/bold red] {msg}")

    def show_startup_banner(self, info: dict) -> None:
        txt = Text()
        txt.append("S O V E R E I G N\n", style="bold white")
        txt.append("Local AI Agent - v1.0.0\n\n", style="dim")
        txt.append(f"Model: {info['model']}\n")
        txt.append(f"STT: {info['stt']}\n")
        txt.append(f"TTS: {info['tts']}\n")
        txt.append(f"Memory: {info['memory']}\n")
        txt.append(f"Skills: {info['skills']} loaded\n")
        txt.append(f"Wake word: {info['wake_word']}\n")
        txt.append(f"Mode: {info['mode']}\n")
        self.console.print(Panel(txt, border_style="magenta"))

    def show_listening(self) -> None:
        self.console.print("[cyan]Listening...[/cyan]")

    def show_thinking(self) -> None:
        self.console.print("[magenta]Thinking...[/magenta]")
