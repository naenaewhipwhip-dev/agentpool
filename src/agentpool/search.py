from __future__ import annotations
from pathlib import Path
from agentpool.models import Solution, Tip

import chromadb


def _entry_to_text(entry: Solution | Tip) -> str:
    if isinstance(entry, Solution):
        return f"{entry.title}\n{entry.problem}\n{entry.solution}"
    return f"{entry.title}\n{entry.content}"


class SearchIndex:
    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path.home() / ".agentpool" / "chroma"
        db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._collection = self._client.get_or_create_collection(
            name="agentpool",
            metadata={"hnsw:space": "cosine"},
        )

    def index_entries(self, entries: list[Solution | Tip]) -> None:
        # Clear and reindex
        self._client.delete_collection("agentpool")
        self._collection = self._client.create_collection(
            name="agentpool",
            metadata={"hnsw:space": "cosine"},
        )
        if not entries:
            return
        self._collection.add(
            ids=[e.id for e in entries],
            documents=[_entry_to_text(e) for e in entries],
            metadatas=[{"type": e.type, "title": e.title, "tags": ",".join(e.tags)} for e in entries],
        )

    def search(self, query: str, top_k: int = 5) -> list[Solution | Tip]:
        if self.count() == 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self.count()),
        )
        entries = []
        for i, entry_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            doc = results["documents"][0][i]
            if meta["type"] == "solution":
                parts = doc.split("\n", 2)
                entries.append(Solution(
                    id=entry_id,
                    title=meta["title"],
                    problem=parts[1] if len(parts) > 1 else "",
                    solution=parts[2] if len(parts) > 2 else "",
                    tags=meta["tags"].split(",") if meta["tags"] else [],
                ))
            else:
                parts = doc.split("\n", 1)
                entries.append(Tip(
                    id=entry_id,
                    title=meta["title"],
                    content=parts[1] if len(parts) > 1 else "",
                    tags=meta["tags"].split(",") if meta["tags"] else [],
                ))
        return entries

    def count(self) -> int:
        return self._collection.count()
