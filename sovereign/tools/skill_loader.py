from __future__ import annotations

import importlib.util
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.registry = {}
        self.lock = threading.Lock()
        self._load_all()
        self._start_watcher()

    @property
    def count(self) -> int:
        return len(self.registry)

    def get_skill_names(self) -> list[str]:
        return list(self.registry.keys())

    def has_skill(self, name: str) -> bool:
        return name in self.registry

    def get_skill_list(self) -> str:
        if not self.registry:
            return "none"
        return "\n".join(
            f"- {name}: {module.SKILL_DESCRIPTION}" for name, module in self.registry.items()
        )

    def run_skill(self, name: str, args: dict) -> str:
        module = self.registry.get(name)
        if not module:
            return f"Skill not found: {name}"
        return str(module.execute(args))

    def _load_all(self) -> None:
        with self.lock:
            self.registry.clear()
            for file in self.skills_dir.glob("*.py"):
                self._load_one(file)

    def _load_one(self, file: Path) -> None:
        spec = importlib.util.spec_from_file_location(file.stem, file)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not all(hasattr(module, attr) for attr in ("SKILL_NAME", "SKILL_DESCRIPTION", "execute")):
            return
        self.registry[module.SKILL_NAME] = module

    def _start_watcher(self) -> None:
        handler = _SkillWatcher(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.skills_dir), recursive=False)
        self.observer.daemon = True
        self.observer.start()

    def reload(self) -> None:
        self._load_all()

    def stop(self) -> None:
        if hasattr(self, "observer"):
            self.observer.stop()
            self.observer.join(timeout=1)


class _SkillWatcher(FileSystemEventHandler):
    def __init__(self, loader: SkillLoader):
        self.loader = loader

    def on_any_event(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix == ".py":
            self.loader.reload()
