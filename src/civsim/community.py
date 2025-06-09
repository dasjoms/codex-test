"""Basic community and task structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class CommunityTask:
    """A placeholder community task."""

    description: str
    assigned: Set[int] = field(default_factory=set)
    completed: bool = False


@dataclass
class Community:
    """Group of entities sharing tasks and storage."""

    id: int
    member_ids: Set[int] = field(default_factory=set)
    tasks: List[CommunityTask] = field(default_factory=list)
    storage_id: int | None = None

    def add_member(self, entity_id: int) -> None:
        self.member_ids.add(entity_id)

    def remove_member(self, entity_id: int) -> None:
        self.member_ids.discard(entity_id)

    def add_task(self, task: CommunityTask) -> None:
        self.tasks.append(task)
