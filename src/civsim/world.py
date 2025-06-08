"""World generation and tile data structures for the civilization simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
import random
from typing import List


class Biome(Enum):
    """Different terrain types found on the map."""

    PLAINS = "plains"
    FOREST = "forest"
    DESERT = "desert"
    WATER = "water"
    MOUNTAIN = "mountain"


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
    elevation: float = 0.0
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
        resource_scale: int = 8,
        region_size: int = 32,
    ) -> None:
        self.width = width
        self.height = height
        self.region_size = max(
            1,
            min(
                region_size, max(1, width // biome_scale), max(1, height // biome_scale)
            ),
        )
        rng = random.Random(seed)

        self.tiles = [
            [Tile(biome=Biome.PLAINS) for _ in range(width)] for _ in range(height)
        ]

        reg_w = math.ceil(width / self.region_size)
        reg_h = math.ceil(height / self.region_size)

        temps = [
            min(1.0, max(0.0, ry / reg_h + rng.uniform(-0.1, 0.1)))
            for ry in range(reg_h)
        ]

        region_biomes: List[List[Biome]] = [
            [Biome.PLAINS for _ in range(reg_w)] for _ in range(reg_h)
        ]
        region_elev: List[List[float]] = [
            [rng.random() for _ in range(reg_w)] for _ in range(reg_h)
        ]

        for ry in range(reg_h):
            for rx in range(reg_w):
                neighbors = []
                if rx > 0:
                    neighbors.append(region_biomes[ry][rx - 1])
                if ry > 0:
                    neighbors.append(region_biomes[ry - 1][rx])

                base_elev = region_elev[ry][rx]
                if neighbors and rng.random() < 0.6:
                    biome = rng.choice(neighbors)
                else:
                    biome = self._biome_from_climate(temps[ry], base_elev, rng)

                region_biomes[ry][rx] = biome

                for y in range(
                    ry * self.region_size, min((ry + 1) * self.region_size, height)
                ):
                    for x in range(
                        rx * self.region_size, min((rx + 1) * self.region_size, width)
                    ):
                        elev = min(1.0, max(0.0, base_elev + rng.uniform(-0.05, 0.05)))
                        self.tiles[y][x].elevation = elev
                        self.tiles[y][x].biome = (
                            Biome.MOUNTAIN if elev > 0.85 else biome
                        )

        needed = {Biome.PLAINS, Biome.FOREST, Biome.DESERT, Biome.WATER}
        present = {tile.biome for row in self.tiles for tile in row}
        for missing in needed - present:
            x = rng.randrange(width)
            y = rng.randrange(height)
            self.tiles[y][x].biome = missing

        for y in range(height):
            for x in range(width):
                tile = self.tiles[y][x]
                if tile.biome == Biome.FOREST and rng.random() < 0.7:
                    amt = rng.randint(3, 7)
                    tile.resources[Resource.WOOD] = (
                        tile.resources.get(Resource.WOOD, 0) + amt
                    )

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
        """Return a biome type influenced by temperature (legacy)."""

        if temp < 0.3:
            choices = [Biome.FOREST, Biome.PLAINS]
        elif temp < 0.6:
            choices = [Biome.PLAINS, Biome.FOREST, Biome.DESERT]
        else:
            choices = [Biome.DESERT, Biome.PLAINS]

        if rng.random() < 0.05:
            choices.append(Biome.WATER)

        return rng.choice(choices)

    def _biome_from_climate(
        self, temp: float, elevation: float, rng: random.Random
    ) -> Biome:
        """Return a biome given temperature and elevation."""

        if elevation > 0.8:
            return Biome.MOUNTAIN

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
                (Resource.WOOD, 0.9),
                (Resource.ANIMAL, 0.3),
                (Resource.STONE, 0.1),
                (None, 0.2),
            ],
            Biome.PLAINS: [
                (Resource.FOOD, 0.3),
                (Resource.WATER, 0.2),
                (Resource.ANIMAL, 0.2),
                (Resource.WOOD, 0.1),
                (Resource.STONE, 0.1),
                (Resource.IRON, 0.05),
                (None, 0.3),
            ],
            Biome.DESERT: [
                (Resource.STONE, 0.4),
                (Resource.CLAY, 0.3),
                (Resource.IRON, 0.1),
                (Resource.COPPER, 0.05),
                (Resource.COAL, 0.05),
                (Resource.GOLD, 0.05),
                (Resource.WATER, 0.05),
                (None, 0.4),
            ],
            Biome.MOUNTAIN: [
                (Resource.STONE, 0.5),
                (Resource.IRON, 0.15),
                (Resource.COPPER, 0.1),
                (Resource.COAL, 0.1),
                (Resource.GOLD, 0.05),
                (None, 0.5),
            ],
            Biome.WATER: [
                (Resource.WATER, 0.6),
                (Resource.ANIMAL, 0.4),
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
                return res  # type: ignore[return-value]
            upto += weight
        return None

    def _resource_amount(self, res: Resource, rng: random.Random) -> int:
        """Return an amount for the given resource type."""

        ranges = {
            Resource.WOOD: (3, 7),
            Resource.ANIMAL: (1, 3),
            Resource.STONE: (2, 5),
            Resource.CLAY: (2, 5),
            Resource.FOOD: (2, 6),
            Resource.WATER: (1, 3),
            Resource.IRON: (1, 3),
            Resource.COPPER: (1, 2),
            Resource.COAL: (1, 2),
            Resource.GOLD: (1, 1),
        }
        low, high = ranges.get(res, (1, 3))
        return rng.randint(low, high)
