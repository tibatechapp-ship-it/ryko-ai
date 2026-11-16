"""خدمة الذاكرة السياقية باستخدام ChromaDB."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List

try:
    import chromadb
except Exception:  # pragma: no cover - handled gracefully when dependency missing
    chromadb = None  # type: ignore


class MemoryService:
    """حفظ واسترجاع سياق المحادثات من قاعدة بيانات متجهة."""

    def __init__(self, persist_path: str = "./data/chroma", collection_name: str = "chat_memory"):
        self.persist_path = persist_path
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._ready = False

    async def initialize(self) -> None:
        """تهيئة عميل ChromaDB بشكل غير حاجب للحلقة الحدثية."""
        if chromadb is None:
            self._ready = False
            return
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        Path(self.persist_path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.persist_path)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)
        self._ready = True

    @property
    def ready(self) -> bool:
        return self._ready and self._collection is not None

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        """حفظ رسالة في الذاكرة مع معرف فريد."""
        if not self.ready or not content.strip():
            return
        doc_id = f"{session_id}-{role}-{abs(hash((session_id, role, content)))}"
        metadata = {"session_id": session_id, "role": role}
        await asyncio.to_thread(
            self._collection.upsert,  # type: ignore[union-attr]
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id],
        )

    async def get_relevant_context(self, session_id: str, query: str, n_results: int = 3) -> List[str]:
        """استرجاع أقرب الرسائل/السياقات صلة بالاستعلام الحالي."""
        if not self.ready or not query.strip():
            return []
        try:
            result = await asyncio.to_thread(
                self._collection.query,  # type: ignore[union-attr]
                query_texts=[query],
                n_results=n_results,
                where={"session_id": session_id},
            )
        except Exception:
            return []
        docs = (result or {}).get("documents") or [[]]
        return [d for d in docs[0] if isinstance(d, str) and d.strip()]

    async def close(self) -> None:
        """إغلاق الموارد (Chroma PersistentClient لا يحتاج إغلاقاً صريحاً عادة)."""
        self._client = None
        self._collection = None
        self._ready = False
