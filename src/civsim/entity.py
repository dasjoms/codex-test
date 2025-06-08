"""Entity definitions with needs, traits, and basic behaviours."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple

from .world import World


@dataclass
class Needs:
    """Container for mutable entity needs."""

    max_health: int = 100
    health: int = 100
    hunger: int = 0
    thirst: int = 0
    energy: int = 100
    morale: int = 50
    injuries: int = 0


@dataclass
class Traits:
    """Base attributes that influence entity behaviour."""

    strength: int = 5
    agility: int = 5
    intelligence: int = 5
    perception: int = 2
    curiosity: float = 0.5
    sociability: float = 0.5


@dataclass
class Entity:
    """A basic entity living in the world with simple needs."""

    id: int
    x: int
    y: int
    needs: Needs = field(default_factory=Needs)
    traits: Traits = field(default_factory=Traits)
    age: int = 0
    max_age: int = 100
    inventory: int = 0
    memory: Set[Tuple[int, int]] = field(default_factory=set)
    relationships: Dict[int, str] = field(default_factory=dict)

    def perceive(self, world: World) -> None:
        """Add visible tiles to memory based on perception range."""

        r = self.traits.perception
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = self.x + dx, self.y + dy
                if world.in_bounds(x, y):
                    self.memory.add((x, y))

    def move(self, dx: int, dy: int, world: World) -> None:
        """Move the entity by the given delta if inside world bounds."""

        nx, ny = self.x + dx, self.y + dy
        if world.in_bounds(nx, ny):
            self.x, self.y = nx, ny

    def gather(self, world: World) -> None:
        """Gather one resource from the current tile if available."""

        tile = world.get_tile(self.x, self.y)
        if not tile.resources:
            return

        res = random.choice(list(tile.resources.keys()))
        tile.resources[res] -= 1
        if tile.resources[res] <= 0:
            del tile.resources[res]
        self.inventory += 1
        if self.needs.hunger > 0:
            self.needs.hunger = max(0, self.needs.hunger - 1)
        if self.needs.thirst > 0:
            self.needs.thirst = max(0, self.needs.thirst - 1)

    def rest(self) -> None:
        """Recover energy while increasing hunger and thirst."""

        self.needs.energy = min(100, self.needs.energy + 20)
        self.needs.hunger += 1
        self.needs.thirst += 1

    def add_relationship(self, other: "Entity", kind: str) -> None:
        """Record a relationship with another entity."""

        self.relationships[other.id] = kind

    def can_reproduce(self) -> bool:
        """Return True if the entity has enough reserves to create offspring."""

        return (
            self.needs.energy > 50
            and self.needs.hunger < 10
            and self.needs.thirst < 10
            and self.needs.health > 0
        )

    def reproduce_with(self, partner: "Entity", child_id: int) -> "Entity":
        """Return a new entity representing offspring with the partner."""

        child_traits = Traits(
            strength=(self.traits.strength + partner.traits.strength) // 2,
            agility=(self.traits.agility + partner.traits.agility) // 2,
            intelligence=(self.traits.intelligence + partner.traits.intelligence) // 2,
            perception=(self.traits.perception + partner.traits.perception) // 2,
            curiosity=(self.traits.curiosity + partner.traits.curiosity) / 2,
            sociability=(self.traits.sociability + partner.traits.sociability) / 2,
        )
        self.needs.energy -= 20
        partner.needs.energy -= 20
        child = Entity(id=child_id, x=self.x, y=self.y, traits=child_traits)
        self.relationships[child_id] = "family"
        partner.relationships[child_id] = "family"
        child.relationships[self.id] = "parent"
        child.relationships[partner.id] = "parent"
        return child

    def take_turn(self, world: World) -> None:
        """Perform a simple turn: update needs then act."""

        self.age += 1
        self.needs.hunger += 1
        self.needs.thirst += 1
        self.needs.energy -= 1

        self.memory.add((self.x, self.y))
        self.perceive(world)

        if self.needs.hunger >= 20 or self.needs.thirst >= 20:
            self.needs.health = max(0, self.needs.health - 5)
            self.needs.injuries += 1

        if self.age >= self.max_age:
            self.needs.health = 0

        if self.needs.energy <= 0:
            self.rest()
            return

        dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)])
        self.move(dx, dy, world)
        self.memory.add((self.x, self.y))
        self.perceive(world)
        self.gather(world)
