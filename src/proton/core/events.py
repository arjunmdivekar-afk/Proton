"""Structured Event Bus for Proton streaming and observability."""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Agent lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_THINKING = "agent.thinking"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"

    # Streaming
    MESSAGE_DELTA = "message.delta"
    MESSAGE_COMPLETED = "message.completed"

    # Plan
    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"

    # Tool execution
    TOOL_STARTED = "tool.started"
    TOOL_OUTPUT = "tool.output"
    TOOL_COMPLETED = "tool.completed"

    # Approvals
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_RESOLVED = "approval.resolved"

    # File & Validation
    FILE_CHANGED = "file.changed"
    TEST_STARTED = "test.started"
    TEST_COMPLETED = "test.completed"


class Event(BaseModel):
    type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None


EventHandler = Callable[[Event], Any]


class EventBus:
    """Asynchronous and synchronous event distributor."""

    def __init__(self) -> None:
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def emit(self, event: Event) -> None:
        # Call specific handlers
        handlers = self._handlers.get(event.type, []) + self._global_handlers
        for handler in handlers:
            try:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                # Observers must not crash the main execution loop
                pass

    def emit_sync(self, event: Event) -> None:
        handlers = self._handlers.get(event.type, []) + self._global_handlers
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass


# Global singleton instance
event_bus = EventBus()
