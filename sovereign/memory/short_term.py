from collections import deque


class ShortTermMemory:
    def __init__(self, limit: int):
        self.buffer = deque(maxlen=limit)

    def add(self, role: str, content: str) -> None:
        self.buffer.append({"role": role, "content": content})

    def get_history(self) -> str:
        if not self.buffer:
            return "none"
        return "\n".join(f"{item['role']}: {item['content']}" for item in self.buffer)

    def clear(self) -> None:
        self.buffer.clear()

    def to_list(self) -> list[dict]:
        return list(self.buffer)
