"""Entity definitions with needs, traits, and basic behaviours."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

from .world import World, Resource, Tile
from .actions import (
    Action,
    GatherAction,
    MoveAction,
    MoveToAction,
    RestAction,
    ConsumeAction,
)


@dataclass
class Needs:
    """Container for mutable entity needs."""

    max_health: int = 100
    health: int = 100
    hunger: int = 0
    thirst: int = 0
    energy: int = 100
    morale: int = 50
    loneliness: int = 0
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
    current_action: Optional[Action] = None

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
        if (
            world.in_bounds(nx, ny)
            and (nx, ny) not in occupied
            and world.get_tile(nx, ny).walkable
        ):
            self.x, self.y = nx, ny
            return True
        return False

    def remembered_tile_with_resource(
        self, world: World, resource: Resource
    ) -> Tuple[int, int] | None:
        """Return coordinates of a remembered tile containing the resource."""

        for x, y in sorted(self.memory):
            if not world.in_bounds(x, y):
                continue
            tile = world.get_tile(x, y)
            if resource in tile.resources:
                return x, y
        return None

    def remembered_adjacent_tile_for_resource(
        self, world: World, resource: Resource
    ) -> Tuple[int, int] | None:
        """Return a walkable tile adjacent to a remembered resource."""

        for x, y in self.memory:
            if not world.in_bounds(x, y):
                continue
            tile = world.get_tile(x, y)
            if resource not in tile.resources:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if world.in_bounds(nx, ny) and world.get_tile(nx, ny).walkable:
                    return nx, ny
        return None

    def gather(self, world: World) -> None:
        """Gather a resource from an adjacent non-walkable tile."""

        sources: list[Tuple[Tile, Tuple[int, int]]] = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = self.x + dx, self.y + dy
            if not world.in_bounds(nx, ny):
                continue
            t = world.get_tile(nx, ny)
            if t.resources:
                sources.append((t, (nx, ny)))
        if not sources:
            return

        tile, _ = random.choice(sources)
        res = random.choice(list(tile.resources.keys()))
        tile.resources[res] -= 1
        if tile.resources[res] <= 0:
            del tile.resources[res]
            tile.walkable = True
            if res is Resource.BERRY_BUSH:
                tile.regrow[Resource.BERRY_BUSH] = 100
        if res is Resource.BERRY_BUSH:
            self.inventory.add(Resource.BERRIES)
        elif res is Resource.ANIMAL:
            self.inventory.add(Resource.MEAT)
        else:
            self.inventory.add(res)
        if self.needs.hunger > 0:
            self.needs.hunger = max(0, self.needs.hunger - 1)
        if self.needs.thirst > 0:
            self.needs.thirst = max(0, self.needs.thirst - 1)

    def consume(self, resource: Resource) -> None:
        """Consume a resource from the inventory."""

        if self.inventory.items.get(resource, 0) <= 0:
            return
        self.inventory.items[resource] -= 1
        if self.inventory.items[resource] <= 0:
            del self.inventory.items[resource]

        if resource is Resource.WATER:
            self.needs.thirst = max(0, self.needs.thirst - 5)
        elif resource is Resource.BERRIES:
            self.needs.hunger = max(0, self.needs.hunger - 3)
        elif resource is Resource.MEAT:
            self.needs.hunger = max(0, self.needs.hunger - 7)

    def rest(self) -> None:
        """Recover energy while increasing hunger and thirst."""

        self.needs.energy = min(100, self.needs.energy + 20)
        self.needs.hunger += 0.5
        self.needs.thirst += 0.5
        self.needs.morale = min(100, self.needs.morale + 1)

    def add_relationship(self, other: "Entity", kind: str) -> None:
        """Record a relationship with another entity."""

        self.relationships[other.id] = kind

    def plan_action(self, world: World) -> Action:
        """Select the next action based on needs and memory."""

        if self.needs.energy <= 20:
            return RestAction()

        if self.needs.health < 30:
            if (
                self.needs.thirst > 5
                and self.inventory.items.get(Resource.WATER, 0) > 0
            ):
                return ConsumeAction(Resource.WATER)
            for food in (Resource.MEAT, Resource.BERRIES):
                if self.needs.hunger > 5 and self.inventory.items.get(food, 0) > 0:
                    return ConsumeAction(food)

        if self.needs.thirst >= 12 and self.inventory.items.get(Resource.WATER, 0) > 0:
            return ConsumeAction(Resource.WATER)
        if self.needs.hunger >= 12:
            for food in (Resource.MEAT, Resource.BERRIES):
                if self.inventory.items.get(food, 0) > 0:
                    return ConsumeAction(food)

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            nx, ny = self.x + dx, self.y + dy
            if world.in_bounds(nx, ny) and world.get_tile(nx, ny).resources:
                return GatherAction()

        if self.needs.thirst >= 50 and self.inventory.items.get(Resource.WATER, 0) == 0:
            loc = self.remembered_adjacent_tile_for_resource(world, Resource.WATER)
            if loc:
                return MoveToAction(target=loc)

        if self.needs.hunger >= 50 and not any(
            self.inventory.items.get(res, 0) > 0
            for res in (Resource.MEAT, Resource.BERRIES)
        ):
            for res in (Resource.ANIMAL, Resource.BERRY_BUSH):
                loc = self.remembered_adjacent_tile_for_resource(world, res)
                if loc:
                    return MoveToAction(target=loc)

        if self.needs.loneliness >= 8:
            dx, dy = random.choice(directions)
            return MoveAction(dx, dy)

        dx, dy = random.choice(directions)
        return MoveAction(dx, dy)

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
        """Update needs, decide on an action, and perform it."""

        if occupied is None:
            occupied = set()

        self.age += 1
        self.needs.hunger += 0.5
        self.needs.thirst += 0.5
        self.needs.energy -= 1
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if any((self.x + dx, self.y + dy) in occupied for dx, dy in directions):
            self.needs.loneliness = max(0, self.needs.loneliness - 2)
        else:
            self.needs.loneliness += 1

        regen = 0
        if self.needs.hunger <= 5 or self.needs.thirst <= 5:
            regen += 1
        if self.needs.hunger <= 5 and self.needs.thirst <= 5:
            regen += 1
        if regen:
            self.needs.health = min(self.needs.max_health, self.needs.health + regen)
        self.memory.add((self.x, self.y))
        self.perceive(world)

        if self.needs.hunger >= 20 or self.needs.thirst >= 20:
            self.needs.health = max(0, self.needs.health - 5)
            self.needs.injuries += 1

        if (
            self.needs.hunger > 10
            or self.needs.thirst > 10
            or self.needs.loneliness > 5
        ):
            self.needs.morale = max(0, self.needs.morale - 1)
        else:
            self.needs.morale = min(100, self.needs.morale + 1)

        if self.age >= self.max_age:
            self.needs.health = 0

        if self.current_action is None or self.current_action.finished:
            self.current_action = self.plan_action(world)
            self.current_action.start(self, world)

        self.current_action.step(self, world, occupied)
        self.memory.add((self.x, self.y))
        self.perceive(world)
