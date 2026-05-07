from __future__ import annotations

import logging
from pathlib import Path


class VectorMemory:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.backend_name = "SQLite only"
        self.enabled = False
        self.collection = None

        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(self.path))
            self.collection = client.get_or_create_collection("sovereign_memory")
            self.enabled = True
            self.backend_name = "SQLite + ChromaDB"
        except Exception as exc:
            logging.warning("ChromaDB unavailable, vector memory disabled: %s", exc)

    def add(self, text: str, metadata: dict) -> None:
        if not self.enabled or not self.collection:
            return
        try:
            doc_id = f"mem_{abs(hash(text))}_{metadata.get('role', 'unknown')}"
            self.collection.add(documents=[text], metadatas=[metadata], ids=[doc_id])
        except Exception as exc:
            logging.warning("Vector add failed: %s", exc)

    def search(self, query: str, n: int = 3) -> list[str]:
        if not self.enabled or not self.collection:
            return []
        try:
            result = self.collection.query(query_texts=[query], n_results=n)
            docs = result.get("documents", [[]])[0]
            return [str(d) for d in docs]
        except Exception as exc:
            logging.warning("Vector search failed: %s", exc)
            return []

    def delete_all(self) -> None:
        if not self.enabled or not self.collection:
            return
        self.collection.delete(where={})
