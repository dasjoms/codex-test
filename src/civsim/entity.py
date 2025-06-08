"""Entity definitions with needs, traits, and basic behaviours."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple

from .world import World, Resource


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
class ReproductionRules:
    """Thresholds controlling when entities may reproduce."""

    min_age: int = 18
    energy_min: int = 70
    hunger_max: int = 5
    thirst_max: int = 5
    health_min: int = 80
    injury_max: int = 0
    cooldown: int = 10


@dataclass
class Inventory:
    """Mapping of resources held by an entity."""

    items: Dict[Resource, int] = field(default_factory=dict)

    def add(self, resource: Resource, amount: int = 1) -> None:
        """Add the given resource amount to the inventory."""

        self.items[resource] = self.items.get(resource, 0) + amount

    def __str__(self) -> str:  # pragma: no cover - string format
        return (
            ", ".join(f"{res.name}: {qty}" for res, qty in self.items.items())
            or "empty"
        )


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
    inventory: Inventory = field(default_factory=Inventory)
    memory: Set[Tuple[int, int]] = field(default_factory=set)
    relationships: Dict[int, str] = field(default_factory=dict)
    last_reproduced: int = -9999

    def perceive(self, world: World) -> None:
        """Add visible tiles to memory based on perception range."""

        r = self.traits.perception
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = self.x + dx, self.y + dy
                if world.in_bounds(x, y):
                    self.memory.add((x, y))

    def move(
        self,
        dx: int,
        dy: int,
        world: World,
        occupied: Set[Tuple[int, int]] | None = None,
    ) -> bool:
        """Move the entity by the given delta if the target is free."""

        if occupied is None:
            occupied = set()

        nx, ny = self.x + dx, self.y + dy
        if world.in_bounds(nx, ny) and (nx, ny) not in occupied:
            self.x, self.y = nx, ny
            return True
        return False

    def gather(self, world: World) -> None:
        """Gather one resource from the current tile if available."""

        tile = world.get_tile(self.x, self.y)
        if not tile.resources:
            return

        res = random.choice(list(tile.resources.keys()))
        tile.resources[res] -= 1
        if tile.resources[res] <= 0:
            del tile.resources[res]
        self.inventory.add(res)
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

    def can_reproduce(
        self,
        rules: ReproductionRules | None = None,
        current_tick: int = 0,
    ) -> bool:
        """Return True if the entity satisfies the given reproduction rules."""

        if rules is None:
            rules = ReproductionRules()

        if current_tick - self.last_reproduced < rules.cooldown:
            return False

        return (
            self.age >= rules.min_age
            and self.needs.energy >= rules.energy_min
            and self.needs.hunger <= rules.hunger_max
            and self.needs.thirst <= rules.thirst_max
            and self.needs.health >= rules.health_min
            and self.needs.injuries <= rules.injury_max
        )

    def reproduce_with(
        self, partner: "Entity", child_id: int, current_tick: int
    ) -> "Entity":
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
        self.last_reproduced = current_tick
        partner.last_reproduced = current_tick
        self.relationships[child_id] = "family"
        partner.relationships[child_id] = "family"
        child.relationships[self.id] = "parent"
        child.relationships[partner.id] = "parent"
        return child

    def take_turn(
        self, world: World, occupied: Set[Tuple[int, int]] | None = None
    ) -> None:
        """Perform a simple turn: update needs then act."""

        if occupied is None:
            occupied = set()

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

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            if self.move(dx, dy, world, occupied):
                break
        self.memory.add((self.x, self.y))
        self.perceive(world)
        self.gather(world)
