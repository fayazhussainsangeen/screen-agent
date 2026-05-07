from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class FileAgent:
    PROTECTED_PREFIXES = [Path("/etc"), Path("/sys"), Path("/boot")]

    EXT_GROUPS = {
        "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
        "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".csv"},
        "Videos": {".mp4", ".mov", ".avi", ".mkv"},
        "Audio": {".mp3", ".wav", ".flac", ".m4a"},
        "Code": {".py", ".js", ".ts", ".html", ".css", ".sh", ".json"},
        "Archives": {".zip", ".tar", ".gz", ".rar"},
    }

    def __init__(self, trash_dir: Path):
        self.trash_dir = Path(trash_dir)
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, args: dict) -> str:
        action = args.get("action")
        if not action or not hasattr(self, action):
            return f"Unsupported file action: {action}"
        call_args = {k: v for k, v in args.items() if k != "action"}
        return str(getattr(self, action)(**call_args))

    def _safe_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser().resolve()
        for protected in self.PROTECTED_PREFIXES:
            try:
                path.relative_to(protected)
            except ValueError:
                pass
            else:
                raise ValueError(f"Operation rejected on protected path: {path}")
        return path

    def list_directory(self, path: str) -> str:
        target = self._safe_path(path)
        if not target.exists() or not target.is_dir():
            return f"Directory not found: {target}"

        lines = [f"{target}"]
        for p in sorted(target.iterdir()):
            marker = "/" if p.is_dir() else ""
            lines.append(f"- {p.name}{marker}")
        return "\n".join(lines)

    def move_file(self, src: str, dst: str) -> str:
        s = self._safe_path(src)
        d = self._safe_path(dst)
        shutil.move(str(s), str(d))
        return f"Moved: {s} -> {d}"

    def copy_file(self, src: str, dst: str) -> str:
        s = self._safe_path(src)
        d = self._safe_path(dst)
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
        return f"Copied: {s} -> {d}"

    def delete_file(self, path: str) -> str:
        src = self._safe_path(path)
        if not src.exists():
            return f"Path not found: {src}"
        target = self.trash_dir / f"{src.name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        shutil.move(str(src), str(target))
        return f"Moved to trash: {target}"

    def rename_file(self, path: str, new_name: str) -> str:
        src = self._safe_path(path)
        dst = src.with_name(new_name)
        src.rename(dst)
        return f"Renamed: {src.name} -> {dst.name}"

    def search_files(self, directory: str, pattern: str) -> str:
        root = self._safe_path(directory)
        matches = sorted(root.rglob(pattern))
        if not matches:
            return "No matches found."
        return "\n".join(str(m) for m in matches)

    def organize_by_type(self, directory: str) -> str:
        root = self._safe_path(directory)
        moved = 0
        for item in root.iterdir():
            if item.is_dir():
                continue
            dest_group = "Other"
            for group, exts in self.EXT_GROUPS.items():
                if item.suffix.lower() in exts:
                    dest_group = group
                    break
            dest_dir = root / dest_group
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(item), str(dest_dir / item.name))
            moved += 1
        return f"Organized {moved} file(s) by type in {root}"

    def organize_by_date(self, directory: str) -> str:
        root = self._safe_path(directory)
        moved = 0
        for item in root.iterdir():
            if item.is_dir():
                continue
            dt = datetime.fromtimestamp(item.stat().st_mtime)
            dest_dir = root / f"{dt.year:04d}" / f"{dt.month:02d}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(dest_dir / item.name))
            moved += 1
        return f"Organized {moved} file(s) by date in {root}"
