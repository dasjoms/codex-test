"""World generation and tile data structures for the civilization simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import List


class Biome(Enum):
    """Different terrain types found on the map."""

    PLAINS = "plains"
    FOREST = "forest"
    DESERT = "desert"
    WATER = "water"


class Resource(Enum):
    """Types of resources that may appear on tiles."""

    WOOD = "wood"
    STONE = "stone"
    CLAY = "clay"
    WATER = "water"
    FOOD = "food"
    ANIMAL = "animal"
    IRON = "iron"
    COPPER = "copper"
    GOLD = "gold"
    COAL = "coal"


@dataclass
class Tile:
    """A single map tile."""

    biome: Biome
    resources: dict[Resource, int] = field(default_factory=dict)


class World:
    """Grid-based world made of tiles."""

    width: int
    height: int
    tiles: List[List[Tile]]

    def __init__(
        self,
        width: int,
        height: int,
        seed: int | None = None,
        biome_scale: int = 5,
        resource_scale: int = 3,
    ) -> None:
        self.width = width
        self.height = height
        rng = random.Random(seed)

        self.tiles = [
            [Tile(biome=Biome.PLAINS) for _ in range(width)] for _ in range(height)
        ]

        # generate a temperature map to guide biome placement
        temps = [
            min(1.0, max(0.0, y / height + rng.uniform(-0.1, 0.1)))
            for y in range(height)
        ]

        for y in range(height):
            for x in range(width):
                neighbors = []
                if x > 0:
                    neighbors.append(self.tiles[y][x - 1].biome)
                if y > 0:
                    neighbors.append(self.tiles[y - 1][x].biome)

                if neighbors and rng.random() < 0.6:
                    biome = rng.choice(neighbors)
                else:
                    biome = self._biome_from_temperature(temps[y], rng)

                self.tiles[y][x].biome = biome

        # place resource nodes in a finer subgrid
        for ry in range(0, height, resource_scale):
            for rx in range(0, width, resource_scale):
                tx = rng.randrange(rx, min(rx + resource_scale, width))
                ty = rng.randrange(ry, min(ry + resource_scale, height))
                tile = self.tiles[ty][tx]
                res_type = self._choose_resource(tile.biome, rng)
                if res_type is None:
                    continue
                amount = self._resource_amount(res_type, rng)
                tile.resources[res_type] = tile.resources.get(res_type, 0) + amount

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if the coordinates are inside the map."""

        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> Tile:
        """Return the tile at the given coordinates."""

        if not self.in_bounds(x, y):
            raise IndexError("Coordinates out of bounds")
        return self.tiles[y][x]

    def _biome_from_temperature(self, temp: float, rng: random.Random) -> Biome:
        """Return a biome type influenced by temperature."""

        if temp < 0.3:
            choices = [Biome.FOREST, Biome.PLAINS]
        elif temp < 0.6:
            choices = [Biome.PLAINS, Biome.FOREST, Biome.DESERT]
        else:
            choices = [Biome.DESERT, Biome.PLAINS]

        if rng.random() < 0.05:
            choices.append(Biome.WATER)

        return rng.choice(choices)

    def _choose_resource(self, biome: Biome, rng: random.Random) -> Resource | None:
        """Return a resource type appropriate for the biome or None."""

        distribution = {
            Biome.FOREST: [
                (Resource.WOOD, 0.6),
                (Resource.ANIMAL, 0.2),
                (Resource.STONE, 0.1),
                (Resource.CLAY, 0.1),
            ],
            Biome.PLAINS: [
                (Resource.FOOD, 0.3),
                (Resource.WATER, 0.2),
                (Resource.ANIMAL, 0.2),
                (Resource.WOOD, 0.15),
                (Resource.STONE, 0.1),
                (Resource.IRON, 0.05),
            ],
            Biome.DESERT: [
                (Resource.STONE, 0.3),
                (Resource.CLAY, 0.3),
                (Resource.IRON, 0.15),
                (Resource.COPPER, 0.1),
                (Resource.COAL, 0.1),
                (Resource.GOLD, 0.05),
                (Resource.WATER, 0.05),
            ],
            Biome.WATER: [
                (Resource.WATER, 0.5),
                (Resource.ANIMAL, 0.5),
            ],
        }

        choices = distribution.get(biome)
        if not choices:
            return None
        total = sum(w for _, w in choices)
        r = rng.random() * total
        upto = 0.0
        for res, weight in choices:
            if upto + weight >= r:
                return res
            upto += weight
        return None

    def _resource_amount(self, res: Resource, rng: random.Random) -> int:
        """Return an amount for the given resource type."""

        ranges = {
            Resource.WOOD: (1, 1),
            Resource.ANIMAL: (1, 3),
            Resource.STONE: (2, 5),
            Resource.CLAY: (2, 5),
            Resource.FOOD: (2, 6),
            Resource.WATER: (1, 3),
            Resource.IRON: (1, 4),
            Resource.COPPER: (1, 3),
            Resource.COAL: (1, 3),
            Resource.GOLD: (1, 2),
        }
        low, high = ranges.get(res, (1, 3))
        return rng.randint(low, high)
