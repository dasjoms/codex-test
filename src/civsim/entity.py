"""Entity definitions with needs, traits, and basic behaviours."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

from .world import World, Resource, Tile, Building, Blueprint, Biome
from .community import Community
from .actions import (
    Action,
    GatherAction,
    MoveAction,
    MoveToAction,
    RestAction,
    ConsumeAction,
    BuildAction,
)

BASE_MEMORY_TTL = 40.0
VISIT_MEMORY_BOOST = 40.0
MAX_MEMORY_TTL = 100.0


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
class Skills:
    """Skill levels improved through actions."""

    construction: int = 0


@dataclass
class Entity:
    """A basic entity living in the world with simple needs."""

    id: int
    x: int
    y: int
    needs: Needs = field(default_factory=Needs)
    traits: Traits = field(default_factory=Traits)
    age: int = 0
    max_age: int = 100000
    inventory: Inventory = field(default_factory=Inventory)
    skills: Skills = field(default_factory=Skills)
    memory: Dict[Tuple[int, int], float] = field(default_factory=dict)
    relationships: Dict[int, str] = field(default_factory=dict)
    last_reproduced: int = -9999
    current_action: Optional[Action] = None
    home_id: Optional[int] = None
    community_id: Optional[int] = None
    last_plan_reason: str = ""
    action_log: list[str] = field(default_factory=list)

    def remember(
        self,
        x: int,
        y: int,
        *,
        visited: bool = False,
        persistent: bool = False,
    ) -> None:
        """Store a tile in memory with a decay timer."""

        if persistent:
            self.memory[(x, y)] = float("inf")
            return
        ttl = BASE_MEMORY_TTL + (VISIT_MEMORY_BOOST if visited else 0)
        ttl = min(ttl, MAX_MEMORY_TTL)
        current = self.memory.get((x, y))
        if current is None or current < ttl:
            self.memory[(x, y)] = ttl

    def decay_memory(self) -> None:
        """Reduce memory timers and drop expired entries."""

        to_delete = [pos for pos, ttl in self.memory.items() if ttl != float("inf")]
        for pos in to_delete:
            ttl = self.memory[pos]
            ttl -= 1
            if ttl <= 0:
                del self.memory[pos]
            else:
                self.memory[pos] = ttl

    def perceive(self, world: World) -> None:
        """Add visible tiles to memory based on perception range."""

        r = self.traits.perception
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = self.x + dx, self.y + dy
                if world.in_bounds(x, y):
                    self.remember(x, y)

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
            if (nx, ny) not in self.memory:
                self.needs.morale = min(100, self.needs.morale + 2)
            self.x, self.y = nx, ny
            return True
        return False

    def remembered_tile_with_resource(
        self, world: World, resource: Resource
    ) -> Tuple[int, int] | None:
        """Return coordinates of a remembered tile containing the resource."""

        for x, y in sorted(self.memory.keys()):
            if not world.in_bounds(x, y):
                continue
            tile = world.get_tile(x, y)
            if resource is Resource.WATER:
                if tile.biome is Biome.WATER or resource in tile.resources:
                    return x, y
            elif resource in tile.resources:
                return x, y
        return None

    def remembered_adjacent_tile_for_resource(
        self, world: World, resource: Resource
    ) -> Tuple[int, int] | None:
        """Return a walkable tile adjacent to a remembered resource."""

        for x, y in self.memory.keys():
            if not world.in_bounds(x, y):
                continue
            tile = world.get_tile(x, y)
            has_resource = resource in tile.resources
            if resource is Resource.WATER:
                has_resource = has_resource or tile.biome is Biome.WATER
            if not has_resource:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if world.in_bounds(nx, ny) and world.get_tile(nx, ny).walkable:
                    return nx, ny
        return None

    def nearest_unexplored_tile(self, world: World) -> Tuple[int, int] | None:
        """Return the closest walkable tile that is not in memory."""

        from collections import deque

        start = (self.x, self.y)
        if start not in self.memory:
            return start
        queue: deque[tuple[int, int]] = deque([start])
        visited: set[tuple[int, int]] = {start}
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not world.in_bounds(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                if not world.get_tile(nx, ny).walkable:
                    continue
                if (nx, ny) not in self.memory:
                    return nx, ny
                queue.append((nx, ny))
        return None

    def adjacent_tile_for_building(
        self, world: World, building: Building
    ) -> Tuple[int, int] | None:
        """Return a walkable tile adjacent to the given building."""

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = building.x + dx, building.y + dy
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
            if t.resources or t.biome is Biome.WATER:
                sources.append((t, (nx, ny)))
        if not sources:
            return

        tile, _ = random.choice(sources)
        res_choices = list(tile.resources.keys())
        if tile.biome is Biome.WATER:
            res_choices.append(Resource.WATER)
        res = random.choice(res_choices)
        if res is not Resource.WATER:
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

    def step_toward_unexplored(self, world: World) -> MoveAction | None:
        """Return a move action biased toward unexplored territory."""

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        best: tuple[int, int] | None = None
        best_distance = -1
        for dx, dy in directions:
            if not world.in_bounds(self.x + dx, self.y + dy):
                continue
            if not world.get_tile(self.x + dx, self.y + dy).walkable:
                continue
            dist = 1
            nx, ny = self.x + dx, self.y + dy
            while world.in_bounds(nx, ny) and (nx, ny) in self.memory:
                nx += dx
                ny += dy
                dist += 1
            if not world.in_bounds(nx, ny):
                continue
            if dist > best_distance:
                best_distance = dist
                best = (dx, dy)
        if best is not None:
            return MoveAction(*best)
        return None

    def rest(self) -> None:
        """Recover energy while increasing hunger and thirst."""

        self.needs.energy = min(100, self.needs.energy + 20)
        self.needs.hunger += 0.5
        self.needs.thirst += 0.5
        self.needs.morale = min(100, self.needs.morale + 1)

    def add_relationship(self, other: "Entity", kind: str) -> None:
        """Record a relationship with another entity."""

        self.relationships[other.id] = kind

    def bind_to_house(self, building: Building) -> bool:
        """Attempt to join the given house."""

        if not building.add_occupant(self.id):
            return False
        self.home_id = building.id
        return True

    def join_community(self, community: "Community") -> None:
        """Associate this entity with a community."""

        self.community_id = community.id
        community.add_member(self.id)

    def leave_community(self, community: "Community") -> None:
        """Remove this entity from the community."""

        if self.community_id == community.id:
            self.community_id = None
        community.remove_member(self.id)

    def plan_action(self, world: World) -> Action:
        """Select the next action based on needs and memory."""

        storage = world.closest_building(self.x, self.y, "storage", 5)
        if storage:
            dist = max(abs(storage.x - self.x), abs(storage.y - self.y))
            if dist <= 1:
                for res in (Resource.WOOD, Resource.STONE, Resource.CLAY):
                    amt = self.inventory.items.pop(res, 0)
                    if amt:
                        storage.deposit(res, amt)
                if (
                    self.needs.thirst >= 8
                    and storage.inventory.get(Resource.WATER, 0) > 0
                ):
                    if storage.withdraw(Resource.WATER, 1):
                        self.inventory.add(Resource.WATER)
                        self.last_plan_reason = "drinking from storage"
                        return ConsumeAction(Resource.WATER)
                if self.needs.hunger >= 8:
                    for r in (Resource.MEAT, Resource.BERRIES):
                        if storage.inventory.get(r, 0) > 0:
                            if storage.withdraw(r, 1):
                                self.inventory.add(r)
                                self.last_plan_reason = "eating from storage"
                                return ConsumeAction(r)
            else:
                if (
                    self.needs.thirst >= 8
                    and storage.inventory.get(Resource.WATER, 0) > 0
                    and self.inventory.items.get(Resource.WATER, 0) == 0
                ):
                    loc = self.adjacent_tile_for_building(world, storage)
                    if loc:
                        self.last_plan_reason = "moving to storage for water"
                        return MoveToAction(target=loc)
                if (
                    self.needs.hunger >= 8
                    and not any(
                        self.inventory.items.get(r, 0) > 0
                        for r in (Resource.MEAT, Resource.BERRIES)
                    )
                    and any(
                        storage.inventory.get(r, 0) > 0
                        for r in (Resource.BERRIES, Resource.MEAT)
                    )
                ):
                    loc = self.adjacent_tile_for_building(world, storage)
                    if loc:
                        self.last_plan_reason = "moving to storage for food"
                        return MoveToAction(target=loc)

        if self.needs.energy <= 20:
            self.last_plan_reason = "resting due to low energy"
            return RestAction()

        if self.needs.health < 30:
            if (
                self.needs.thirst > 5
                and self.inventory.items.get(Resource.WATER, 0) > 0
            ):
                self.last_plan_reason = "healing by drinking"
                return ConsumeAction(Resource.WATER)
            for food in (Resource.MEAT, Resource.BERRIES):
                if self.needs.hunger > 5 and self.inventory.items.get(food, 0) > 0:
                    self.last_plan_reason = "healing by eating"
                    return ConsumeAction(food)

        if self.needs.thirst >= 8 and self.inventory.items.get(Resource.WATER, 0) > 0:
            self.last_plan_reason = "drinking from inventory"
            return ConsumeAction(Resource.WATER)
        if self.needs.hunger >= 8:
            for food in (Resource.MEAT, Resource.BERRIES):
                if self.inventory.items.get(food, 0) > 0:
                    self.last_plan_reason = "eating from inventory"
                    return ConsumeAction(food)

        house_bp = Blueprint(
            name="house",
            width=2,
            height=2,
            cost={Resource.WOOD: 4},
            bonuses={"morale": 5},
            occupant_limit=2,
            build_time=5,
        )
        if (
            self.inventory.items.get(Resource.WOOD, 0) >= 4
            and self.needs.energy > 60
            and world.can_place_building(
                self.x, self.y, house_bp.width, house_bp.height
            )
        ):
            self.last_plan_reason = "building a house"
            return BuildAction(house_bp, self.x, self.y)

        for site in world.construction_sites:
            if not site.built and max(abs(site.x - self.x), abs(site.y - self.y)) <= 1:
                return BuildAction(site.blueprint, site.x, site.y)

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            nx, ny = self.x + dx, self.y + dy
            if not world.in_bounds(nx, ny):
                continue
            tile = world.get_tile(nx, ny)
            if tile.resources or tile.biome is Biome.WATER:
                resources = dict(tile.resources)
                if tile.biome is Biome.WATER:
                    resources[Resource.WATER] = resources.get(Resource.WATER, 1)
                if list(resources.keys()) == [Resource.WATER] and self.needs.thirst < 8:
                    continue
                if Resource.WOOD in resources:
                    if self.inventory.items.get(
                        Resource.WOOD, 0
                    ) >= 8 and world.can_place_building(self.x, self.y, 2, 2):
                        continue
                return GatherAction()

        if self.inventory.items.get(Resource.WOOD, 0) < 4:
            loc = self.remembered_adjacent_tile_for_resource(world, Resource.WOOD)
            if loc:
                self.last_plan_reason = "seeking wood"
                return MoveToAction(target=loc)
            target = self.nearest_unexplored_tile(world)
            if target:
                self.last_plan_reason = "exploring for wood"
                return MoveToAction(target=target)
            explore = self.step_toward_unexplored(world)
            if explore:
                self.last_plan_reason = "moving toward unexplored for wood"
                return explore

        if self.needs.thirst >= 8 and self.inventory.items.get(Resource.WATER, 0) == 0:
            loc = self.remembered_adjacent_tile_for_resource(world, Resource.WATER)
            if loc:
                self.last_plan_reason = "seeking water source"
                return MoveToAction(target=loc)
            target = self.nearest_unexplored_tile(world)
            if target:
                self.last_plan_reason = "exploring for water"
                return MoveToAction(target=target)
            explore = self.step_toward_unexplored(world)
            if explore:
                self.last_plan_reason = "moving toward unexplored for water"
                return explore

        if self.needs.hunger >= 8 and not any(
            self.inventory.items.get(res, 0) > 0
            for res in (Resource.MEAT, Resource.BERRIES)
        ):
            for res in (Resource.ANIMAL, Resource.BERRY_BUSH):
                loc = self.remembered_adjacent_tile_for_resource(world, res)
                if loc:
                    self.last_plan_reason = "hunting/gathering food"
                    return MoveToAction(target=loc)
            target = self.nearest_unexplored_tile(world)
            if target:
                self.last_plan_reason = "exploring for food"
                return MoveToAction(target=target)
            explore = self.step_toward_unexplored(world)
            if explore:
                self.last_plan_reason = "moving toward unexplored for food"
                return explore

        if self.needs.loneliness >= 8:
            dx, dy = random.choice(directions)
            self.last_plan_reason = "wandering due to loneliness"
            return MoveAction(dx, dy)

        dx, dy = random.choice(directions)
        self.last_plan_reason = "wandering randomly"
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
        self,
        world: World,
        occupied: Set[Tuple[int, int]] | None = None,
        *,
        tick: int = 0,
    ) -> None:
        """Update needs, decide on an action, and perform it."""

        if occupied is None:
            occupied = set()

        self.age += 1
        self.decay_memory()
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
        self.remember(self.x, self.y, visited=True)
        self.perceive(world)

        if self.needs.hunger >= 20 or self.needs.thirst >= 20:
            self.needs.health = max(0, self.needs.health - 0.25)
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
            entry = f"t{tick}: {self.current_action.__class__.__name__} - {self.last_plan_reason}"
            self.action_log.append(entry)
            if len(self.action_log) > 20:
                self.action_log.pop(0)

        self.current_action.step(self, world, occupied)
        self.remember(self.x, self.y, visited=True)
        self.perceive(world)
