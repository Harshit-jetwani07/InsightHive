"""Structured trace logging for ADK agent runs."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any


@dataclass
class TraceEvent:
    trace_id: str
    step: int
    event_type: str
    agent: str = ""
    tool: str = ""
    detail: str = ""
    status: str = "success"
    latency_ms: int = 0
    timestamp: float = field(default_factory=time.time)


class TraceLogger:
    def __init__(self) -> None:
        self._lock = Lock()
        self._events: list[TraceEvent] = []
        self._current_trace_id = str(uuid.uuid4())

    def new_trace(self) -> str:
        with self._lock:
            self._current_trace_id = str(uuid.uuid4())
            self._events = []
            return self._current_trace_id

    def log(
        self,
        event_type: str,
        *,
        agent: str = "",
        tool: str = "",
        detail: str = "",
        status: str = "success",
        latency_ms: int = 0,
    ) -> None:
        with self._lock:
            step = len(self._events) + 1
            self._events.append(
                TraceEvent(
                    trace_id=self._current_trace_id,
                    step=step,
                    event_type=event_type,
                    agent=agent,
                    tool=tool,
                    detail=detail,
                    status=status,
                    latency_ms=latency_ms,
                )
            )

    def get_events(self) -> list[dict[str, Any]]:
        with self._lock:
            return [asdict(event) for event in self._events]

    @property
    def trace_id(self) -> str:
        return self._current_trace_id
