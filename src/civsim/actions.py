"""Action system for entity decisions and multi-tick tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, TYPE_CHECKING
import heapq

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .entity import Entity

from .world import World, Resource, Blueprint, ConstructionSite


class Action:
    """Base class for an action executed over one or more ticks."""

    finished: bool = False

    def start(self, entity: "Entity", world: World) -> None:
        """Prepare the action."""

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        """Perform one tick of the action."""
        self.finished = True


@dataclass
class MoveAction(Action):
    """Move one step if possible."""

    dx: int
    dy: int

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        if entity.move(self.dx, self.dy, world, occupied):
            self.finished = True
        else:
            self.finished = True


@dataclass
class MoveToAction(Action):
    """Pathfind to a specific tile over multiple ticks."""

    target: Tuple[int, int]
    path: List[Tuple[int, int]] = field(default_factory=list)

    def start(self, entity: "Entity", world: World) -> None:
        self._rebuild_path(entity, world)

    def _rebuild_path(self, entity: "Entity", world: World) -> None:
        self.path = self._astar(entity, world)

    def _astar(self, entity: "Entity", world: World) -> List[Tuple[int, int]]:
        start = (entity.x, entity.y)
        goal = self.target
        if start == goal:
            return []

        open_set: list[tuple[int, tuple[int, int]]] = []
        heapq.heappush(open_set, (0, start))
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        g_score: dict[tuple[int, int], int] = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = current[0] + dx, current[1] + dy
                if not world.in_bounds(nx, ny):
                    continue
                if not world.get_tile(nx, ny).walkable and (nx, ny) != goal:
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get((nx, ny), float("inf")):
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative_g
                    priority = tentative_g + abs(goal[0] - nx) + abs(goal[1] - ny)
                    heapq.heappush(open_set, (priority, (nx, ny)))
        else:
            return []

        cur = goal
        path_rev = []
        while cur != start:
            path_rev.append(cur)
            cur = came_from.get(cur)
            if cur is None:
                break
        path_rev.reverse()
        return path_rev

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        if not self.path:
            self.finished = True
            return
        next_pos = self.path[0]
        dx = next_pos[0] - entity.x
        dy = next_pos[1] - entity.y
        if entity.move(dx, dy, world, occupied):
            self.path.pop(0)
            if not self.path:
                self.finished = True
        else:
            self._rebuild_path(entity, world)
            self.finished = True


class GatherAction(Action):
    """Gather a resource from the current tile."""

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        entity.gather(world)
        self.finished = True


class RestAction(Action):
    """Rest until energy is above a threshold."""

    threshold: int = 50

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        if entity.needs.energy >= self.threshold:
            self.finished = True
            return
        entity.rest()
        if entity.needs.energy >= self.threshold:
            self.finished = True


class ConsumeAction(Action):
    """Consume a resource from the entity's inventory."""

    def __init__(self, resource: Resource) -> None:
        self.resource = resource

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        entity.consume(self.resource)
        self.finished = True


@dataclass
class BuildAction(Action):
    """Construct a building using a blueprint."""

    blueprint: Blueprint
    x: int
    y: int
    site: ConstructionSite | None = None

    def start(self, entity: "Entity", world: World) -> None:
        site = world.get_construction_site(self.x, self.y)
        if site is None:
            if not world.can_place_building(
                self.x, self.y, self.blueprint.width, self.blueprint.height
            ):
                self.finished = True
                return
            for res, amount in self.blueprint.cost.items():
                if entity.inventory.items.get(res, 0) < amount:
                    self.finished = True
                    return
            for res, amount in self.blueprint.cost.items():
                entity.inventory.items[res] -= amount
                if entity.inventory.items[res] <= 0:
                    del entity.inventory.items[res]
            site = world.start_construction(self.blueprint, self.x, self.y)
            if site is None:
                self.finished = True
                return
        self.site = site
        self.site.participants.add(entity.id)

    def step(
        self, entity: "Entity", world: World, occupied: set[Tuple[int, int]]
    ) -> None:
        if self.site is None:
            self.finished = True
            return
        built = world.advance_construction(self.site, entity.id)
        self.finished = built
