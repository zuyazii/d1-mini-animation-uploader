"""State management for uploaded frames."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence


@dataclass
class FrameRecord:
    id: str
    name: str
    delay_ms: int
    order: int
    source_path: str
    bitmap: List[int]
    ascii_preview: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class FrameStore:
    """Thread-safe persistence layer for frame metadata."""

    def __init__(self, state_file: Path) -> None:
        self.state_file = state_file
        self._lock = threading.RLock()
        self._frames: Dict[str, FrameRecord] = {}
        self._load()

    def list_frames(self) -> List[FrameRecord]:
        with self._lock:
            return sorted(self._frames.values(), key=lambda frame: frame.order)

    def add_frame(
        self,
        *,
        frame_id: str | None = None,
        name: str,
        delay_ms: int,
        source_path: Path,
        bitmap: List[int],
        ascii_preview: List[str],
    ) -> FrameRecord:
        with self._lock:
            frame_id = frame_id or str(uuid.uuid4())
            order = self._next_order_locked()
            record = FrameRecord(
                id=frame_id,
                name=name,
                delay_ms=delay_ms,
                order=order,
                source_path=str(source_path),
                bitmap=list(bitmap),
                ascii_preview=list(ascii_preview),
            )
            self._frames[frame_id] = record
            self._persist_locked()
            return record

    def update_delay(self, frame_id: str, delay_ms: int) -> FrameRecord:
        with self._lock:
            record = self._require(frame_id)
            record.delay_ms = delay_ms
            self._persist_locked()
            return record

    def update_all_delays(self, delay_ms: int) -> List[FrameRecord]:
        with self._lock:
            for frame in self._frames.values():
                frame.delay_ms = delay_ms
            self._persist_locked()
            return self.list_frames()

    def reorder(self, ordered_ids: Sequence[str]) -> List[FrameRecord]:
        with self._lock:
            if len(ordered_ids) != len(self._frames):
                raise ValueError("Order list length mismatch.")
            if set(ordered_ids) != set(self._frames.keys()):
                raise ValueError("Ordered IDs must match existing frame IDs exactly.")
            for index, frame_id in enumerate(ordered_ids):
                self._frames[frame_id].order = index
            self._persist_locked()
            return self.list_frames()

    def delete(self, frame_id: str) -> None:
        with self._lock:
            record = self._require(frame_id)
            path = Path(record.source_path)
            if path.exists():
                path.unlink()
            del self._frames[frame_id]
            self._renumber_locked()
            self._persist_locked()

    def clear_all(self) -> None:
        with self._lock:
            for record in self._frames.values():
                path = Path(record.source_path)
                if path.exists():
                    path.unlink()
            self._frames.clear()
            self._persist_locked()

    # Internal helpers -------------------------------------------------
    def _require(self, frame_id: str) -> FrameRecord:
        try:
            return self._frames[frame_id]
        except KeyError as exc:
            raise KeyError(f"Unknown frame id: {frame_id}") from exc

    def _next_order_locked(self) -> int:
        if not self._frames:
            return 0
        return max(frame.order for frame in self._frames.values()) + 1

    def _renumber_locked(self) -> None:
        for new_order, frame in enumerate(self.list_frames()):
            frame.order = new_order

    def _persist_locked(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {frame_id: frame.to_dict() for frame_id, frame in self._frames.items()}
        self.state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self.state_file.exists():
            return
        raw = json.loads(self.state_file.read_text(encoding="utf-8"))
        for frame_id, payload in raw.items():
            self._frames[frame_id] = FrameRecord(
                id=payload["id"],
                name=payload["name"],
                delay_ms=payload["delay_ms"],
                order=payload["order"],
                source_path=payload["source_path"],
                bitmap=payload["bitmap"],
                ascii_preview=payload["ascii_preview"],
            )
