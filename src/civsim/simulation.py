"""Main simulation loop and entity interactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .entity import Entity
from .world import World


@dataclass
class Simulation:
    """Main simulation loop management."""

    world: World
    entities: List[Entity]
    tick: int = 0

    def step(self) -> None:
        """Advance the simulation by one tick."""

        new_entities: List[Entity] = []
        for i, entity in enumerate(self.entities):
            for other in self.entities[i + 1 :]:
                if (
                    entity.x == other.x
                    and entity.y == other.y
                    and entity.can_reproduce()
                    and other.can_reproduce()
                ):
                    child_id = len(self.entities) + len(new_entities)
                    child = entity.reproduce_with(other, child_id)
                    new_entities.append(child)
                    break
            entity.take_turn(self.world)
        self.entities.extend(new_entities)
        self.tick += 1
