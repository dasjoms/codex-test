"""Main simulation loop and entity interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .entity import Entity, ReproductionRules
from .world import World


@dataclass
class Simulation:
    """Main simulation loop management."""

    world: World
    entities: List[Entity]
    tick: int = 0
    reproduction_rules: ReproductionRules = field(default_factory=ReproductionRules)

    def step(self) -> None:
        """Advance the simulation by one tick."""

        self.world.tick_regrowth()

        new_entities: List[Entity] = []
        alive_entities: List[Entity] = []

        occupied: dict[tuple[int, int], int] = {}
        for ent in self.entities:
            pos = (ent.x, ent.y)
            occupied[pos] = occupied.get(pos, 0) + 1

        for i, entity in enumerate(self.entities):
            for other in self.entities[i + 1 :]:
                if (
                    entity.x == other.x
                    and entity.y == other.y
                    and entity.can_reproduce(self.reproduction_rules, self.tick)
                    and other.can_reproduce(self.reproduction_rules, self.tick)
                ):
                    child_id = len(self.entities) + len(new_entities)
                    child = entity.reproduce_with(other, child_id, self.tick)
                    new_entities.append(child)
                    break

            pos = (entity.x, entity.y)
            occupied[pos] -= 1
            if occupied[pos] == 0:
                del occupied[pos]

            entity.take_turn(self.world, set(occupied.keys()))

            if entity.needs.health > 0:
                pos = (entity.x, entity.y)
                occupied[pos] = occupied.get(pos, 0) + 1
                alive_entities.append(entity)

        self.entities = alive_entities
        self.entities.extend(new_entities)
        self.tick += 1
