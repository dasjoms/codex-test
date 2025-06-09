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

            entity.take_turn(self.world, set(occupied.keys()), tick=self.tick)
            if entity.home_id is not None:
                entity.needs.morale = min(100, entity.needs.morale + 1)

            if entity.needs.health > 0:
                pos = (entity.x, entity.y)
                occupied[pos] = occupied.get(pos, 0) + 1
                alive_entities.append(entity)

        self.entities = alive_entities
        self.entities.extend(new_entities)
        self._complete_construction()
        self._share_house_memory()
        self.tick += 1

    def _share_house_memory(self) -> None:
        """Share map knowledge between housemates and nearby houses."""

        ent_map = {e.id: e for e in self.entities}
        houses = [b for b in self.world.buildings if b.occupant_limit > 0]

        for house in houses:
            mem_union: set[tuple[int, int]] = set()
            for eid in house.occupant_ids:
                if eid in ent_map:
                    mem_union |= set(ent_map[eid].memory.keys())
            for eid in house.occupant_ids:
                if eid in ent_map:
                    for pos in mem_union:
                        ent_map[eid].remember(*pos, persistent=True)

        for i, h1 in enumerate(houses):
            for h2 in houses[i + 1 :]:
                if max(abs(h1.x - h2.x), abs(h1.y - h2.y)) <= 5:
                    mem_union = set()
                    for eid in h1.occupant_ids + h2.occupant_ids:
                        if eid in ent_map:
                            mem_union |= set(ent_map[eid].memory.keys())
                    for eid in h1.occupant_ids + h2.occupant_ids:
                        if eid in ent_map:
                            for pos in mem_union:
                                ent_map[eid].remember(*pos, persistent=True)

    def _complete_construction(self) -> None:
        """Finalize finished construction sites and reward builders."""

        ent_map = {e.id: e for e in self.entities}
        for site in list(self.world.construction_sites):
            if not site.built or site.building is None:
                continue
            building = site.building
            for eid in site.participants:
                ent = ent_map.get(eid)
                if ent is None:
                    continue
                ent.skills.construction += 1
                for attr, bonus in site.blueprint.bonuses.items():
                    if hasattr(ent.needs, attr):
                        setattr(ent.needs, attr, getattr(ent.needs, attr) + bonus)
                    elif hasattr(ent.traits, attr):
                        setattr(ent.traits, attr, getattr(ent.traits, attr) + bonus)
                if building.occupant_limit:
                    if building.add_occupant(ent.id):
                        ent.home_id = building.id
            self.world.construction_sites.remove(site)
