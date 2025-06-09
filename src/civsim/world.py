"""World generation and tile data structures for the civilization simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import List, Optional

from .community import Community


class Biome(Enum):
    """Different terrain types found on the map."""

    PLAINS = "plains"
    FOREST = "forest"
    DESERT = "desert"
    WATER = "water"
    MOUNTAIN = "mountain"


class Resource(Enum):
    """Types of resources that may appear on tiles or in inventories."""

    WOOD = "wood"
    STONE = "stone"
    CLAY = "clay"
    WATER = "water"
    BERRY_BUSH = "berry_bush"
    ANIMAL = "animal"
    BERRIES = "berries"
    MEAT = "meat"
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
    walkable: bool = True
    regrow: dict[Resource, int] = field(default_factory=dict)
    building_id: Optional[int] = None


@dataclass
class Blueprint:
    """Recipe for constructing a building."""

    name: str
    width: int
    height: int
    cost: dict[Resource, int]
    bonuses: dict[str, int] = field(default_factory=dict)
    occupant_limit: int = 0
    build_time: int = 5


@dataclass
class Building:
    """Structure occupying multiple tiles."""

    id: int
    x: int
    y: int
    width: int
    height: int
    name: str = "building"
    occupant_limit: int = 0
    occupant_ids: list[int] = field(default_factory=list)
    inventory: dict[Resource, int] = field(default_factory=dict)

    def deposit(self, resource: Resource, amount: int = 1) -> None:
        """Add items to the building's shared inventory."""

        self.inventory[resource] = self.inventory.get(resource, 0) + amount

    def withdraw(self, resource: Resource, amount: int = 1) -> int:
        """Remove up to the requested amount from the inventory."""

        available = self.inventory.get(resource, 0)
        taken = min(amount, available)
        if taken:
            self.inventory[resource] = available - taken
            if self.inventory[resource] <= 0:
                del self.inventory[resource]
        return taken

    def add_occupant(self, entity_id: int) -> bool:
        """Add an entity to the building if capacity allows."""

        if self.occupant_limit and len(self.occupant_ids) >= self.occupant_limit:
            return False
        if entity_id not in self.occupant_ids:
            self.occupant_ids.append(entity_id)
        return True

    def remove_occupant(self, entity_id: int) -> None:
        """Remove an entity from the building."""

        if entity_id in self.occupant_ids:
            self.occupant_ids.remove(entity_id)


@dataclass
class ConstructionSite:
    """A shared project tracking construction progress."""

    blueprint: Blueprint
    x: int
    y: int
    progress: int = 0
    required: int = 5
    participants: set[int] = field(default_factory=set)
    built: bool = False
    building: Building | None = None


class World:
    """Grid-based world made of tiles."""

    width: int
    height: int
    tiles: List[List[Tile]]
    buildings: List[Building]

    def __init__(
        self,
        width: int,
        height: int,
        seed: int | None = None,
        biome_scale: int = 5,
        resource_scale: int = 8,
        region_size: int = 32,
        climate_scale: int = 10,
        ensure_starting_resources: bool = True,
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
        self.buildings = []
        self.construction_sites: list[ConstructionSite] = []
        self.communities: list[Community] = []

        # generate temperature and moisture maps for realistic biomes
        coarse_w = max(1, width // climate_scale)
        coarse_h = max(1, height // climate_scale)
        temp_offset = [
            [rng.uniform(-0.2, 0.2) for _ in range(coarse_w)] for _ in range(coarse_h)
        ]
        moist_offset = [
            [rng.uniform(-0.3, 0.3) for _ in range(coarse_w)] for _ in range(coarse_h)
        ]
        temp_map = [
            [
                min(
                    1.0,
                    max(
                        0.0,
                        y / (height - 1)
                        + temp_offset[min(y // climate_scale, coarse_h - 1)][
                            min(x // climate_scale, coarse_w - 1)
                        ],
                    ),
                )
                for x in range(width)
            ]
            for y in range(height)
        ]
        moist_map = [
            [
                min(
                    1.0,
                    max(
                        0.0,
                        0.5
                        + moist_offset[min(y // climate_scale, coarse_h - 1)][
                            min(x // climate_scale, coarse_w - 1)
                        ],
                    ),
                )
                for x in range(width)
            ]
            for y in range(height)
        ]

        def _smooth(grid: list[list[float]]) -> list[list[float]]:
            out = [[0.0 for _ in range(width)] for _ in range(height)]
            for yy in range(height):
                for xx in range(width):
                    total = grid[yy][xx]
                    count = 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = xx + dx, yy + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            total += grid[ny][nx]
                            count += 1
                    out[yy][xx] = total / count
            return out

        for _ in range(2):
            temp_map = _smooth(temp_map)
            moist_map = _smooth(moist_map)

        for y in range(height):
            for x in range(width):
                temp = temp_map[y][x]
                moist = moist_map[y][x]
                biome = self._biome_from_climate(temp, moist, rng)
                tile = self.tiles[y][x]
                tile.biome = biome
                tile.walkable = biome not in (Biome.WATER, Biome.MOUNTAIN)

        # second pass to smooth biome edges
        for _ in range(2):
            new_biomes = [[tile.biome for tile in row] for row in self.tiles]
            for yy in range(height):
                for xx in range(width):
                    if self.tiles[yy][xx].biome in (Biome.WATER, Biome.DESERT):
                        new_biomes[yy][xx] = self.tiles[yy][xx].biome
                        continue
                    counts: dict[Biome, int] = {}
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx, ny = xx + dx, yy + dy
                            if 0 <= nx < width and 0 <= ny < height:
                                b = self.tiles[ny][nx].biome
                                counts[b] = counts.get(b, 0) + 1
                    new_biomes[yy][xx] = max(counts, key=counts.get)
            for yy in range(height):
                for xx in range(width):
                    self.tiles[yy][xx].biome = new_biomes[yy][xx]

        for ry in range(0, height, resource_scale):
            for rx in range(0, width, resource_scale):
                tx = rng.randrange(rx, min(rx + resource_scale, width))
                ty = rng.randrange(ry, min(ry + resource_scale, height))
                tile = self.tiles[ty][tx]
                res_type = self._choose_resource(tile.biome, rng)
                if res_type is None:
                    continue
                if res_type is Resource.ANIMAL:
                    herd = rng.randint(2, 5)
                    for _ in range(herd):
                        hx = max(0, min(width - 1, tx + rng.randint(-2, 2)))
                        hy = max(0, min(height - 1, ty + rng.randint(-2, 2)))
                        htile = self.tiles[hy][hx]
                        if Resource.ANIMAL in htile.resources:
                            continue
                        htile.resources[Resource.ANIMAL] = 1
                        htile.walkable = False
                else:
                    amount = self._resource_amount(res_type, rng)
                    tile.resources[res_type] = tile.resources.get(res_type, 0) + amount
                    tile.walkable = False

        if ensure_starting_resources:
            self._ensure_starting_resources(rng)

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

    def _biome_from_climate(
        self, temp: float, moist: float, rng: random.Random
    ) -> Biome:
        """Return a biome based on temperature and moisture values."""

        if moist > 0.8 or rng.random() < 0.03:
            return Biome.WATER
        if rng.random() < 0.05:
            return Biome.DESERT

        if temp < 0.3:
            return Biome.FOREST if moist > 0.4 else Biome.PLAINS
        if temp < 0.6:
            if moist < 0.3:
                return Biome.DESERT
            if moist > 0.6:
                return Biome.FOREST
            return Biome.PLAINS

        if moist < 0.4:
            return Biome.DESERT
        return Biome.PLAINS

    def _choose_resource(self, biome: Biome, rng: random.Random) -> Resource | None:
        """Return a resource type appropriate for the biome or None."""

        distribution = {
            Biome.FOREST: [
                (Resource.WOOD, 0.8),
                (Resource.ANIMAL, 0.6),
                (Resource.STONE, 0.1),
                (None, 0.2),
            ],
            Biome.PLAINS: [
                (Resource.BERRY_BUSH, 0.6),
                (Resource.WATER, 0.2),
                (Resource.ANIMAL, 0.5),
                (Resource.WOOD, 0.1),
                (Resource.STONE, 0.1),
                (Resource.IRON, 0.05),
                (None, 0.2),
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
            Resource.WOOD: (1, 1),
            Resource.ANIMAL: (1, 1),
            Resource.BERRY_BUSH: (1, 1),
            Resource.STONE: (2, 5),
            Resource.CLAY: (2, 5),
            Resource.WATER: (1, 3),
            Resource.IRON: (1, 3),
            Resource.COPPER: (1, 2),
            Resource.COAL: (1, 2),
            Resource.GOLD: (1, 1),
        }
        low, high = ranges.get(res, (1, 3))
        return rng.randint(low, high)

    def _ensure_starting_resources(self, rng: random.Random) -> None:
        """Place essential resources near the center if missing."""

        center_x = self.width // 2
        center_y = self.height // 2
        radius = 2

        def _place(res: Resource) -> None:
            for _ in range(100):
                x = max(0, min(self.width - 1, center_x + rng.randint(-radius, radius)))
                y = max(
                    0, min(self.height - 1, center_y + rng.randint(-radius, radius))
                )
                tile = self.tiles[y][x]
                if tile.walkable:
                    tile.resources[res] = tile.resources.get(res, 0) + 1
                    tile.walkable = False
                    break

        for _ in range(2):
            _place(Resource.WATER)
            _place(Resource.BERRY_BUSH)
            _place(Resource.ANIMAL)

    def tick_regrowth(self) -> None:
        """Advance resource regrowth timers and restore resources."""

        for row in self.tiles:
            for tile in row:
                for res, timer in list(tile.regrow.items()):
                    tile.regrow[res] -= 1
                    if tile.regrow[res] <= 0:
                        tile.resources[res] = 1
                        tile.walkable = False
                        del tile.regrow[res]

    # ------------------------------------------------------------------
    # Building management
    # ------------------------------------------------------------------
    def can_place_building(self, x: int, y: int, width: int, height: int) -> bool:
        """Return True if a building of the given size can be placed."""

        for dy in range(height):
            for dx in range(width):
                tx, ty = x + dx, y + dy
                if not self.in_bounds(tx, ty):
                    return False
                tile = self.tiles[ty][tx]
                if not tile.walkable or tile.building_id is not None:
                    return False
        return True

    def place_building(self, building: Building) -> bool:
        """Place a building on the map if possible."""

        if not self.can_place_building(
            building.x, building.y, building.width, building.height
        ):
            return False

        building.id = len(self.buildings)
        self.buildings.append(building)
        for dy in range(building.height):
            for dx in range(building.width):
                tile = self.tiles[building.y + dy][building.x + dx]
                tile.building_id = building.id
                tile.walkable = False
        return True

    def remove_building(self, building: Building) -> None:
        """Remove a building and free its tiles."""

        if building not in self.buildings:
            return
        self.buildings.remove(building)
        for dy in range(building.height):
            for dx in range(building.width):
                if not self.in_bounds(building.x + dx, building.y + dy):
                    continue
                tile = self.tiles[building.y + dy][building.x + dx]
                if tile.building_id == building.id:
                    tile.building_id = None
                    tile.walkable = True

    def closest_building(
        self, x: int, y: int, name: str, max_dist: int | None = None
    ) -> Building | None:
        """Return the nearest building with the given name."""

        best: Building | None = None
        best_dist = max_dist if max_dist is not None else 1_000_000
        for b in self.buildings:
            if b.name != name:
                continue
            dist = max(abs(b.x - x), abs(b.y - y))
            if dist < best_dist:
                best = b
                best_dist = dist
        return best

    # ------------------------------------------------------------------
    # Construction projects
    # ------------------------------------------------------------------
    def get_construction_site(self, x: int, y: int) -> ConstructionSite | None:
        """Return the construction site at the given location if present."""

        for site in self.construction_sites:
            if site.x == x and site.y == y:
                return site
        return None

    def start_construction(
        self, blueprint: Blueprint, x: int, y: int
    ) -> ConstructionSite | None:
        """Create a new construction site if the area is free."""

        if not self.can_place_building(x, y, blueprint.width, blueprint.height):
            return None
        site = ConstructionSite(
            blueprint=blueprint, x=x, y=y, required=blueprint.build_time
        )
        self.construction_sites.append(site)
        for dy in range(blueprint.height):
            for dx in range(blueprint.width):
                tile = self.tiles[y + dy][x + dx]
                tile.walkable = False
        return site

    def advance_construction(self, site: ConstructionSite, entity_id: int) -> bool:
        """Advance work on the site and return True when completed."""

        site.participants.add(entity_id)
        if site.built:
            return True
        site.progress += 1
        if site.progress >= site.required:
            building = Building(
                id=-1,
                x=site.x,
                y=site.y,
                width=site.blueprint.width,
                height=site.blueprint.height,
                name=site.blueprint.name,
                occupant_limit=site.blueprint.occupant_limit,
                inventory={},
            )
            building.id = len(self.buildings)
            self.buildings.append(building)
            for dy in range(building.height):
                for dx in range(building.width):
                    tile = self.tiles[building.y + dy][building.x + dx]
                    tile.building_id = building.id
                    tile.walkable = False
            site.built = True
            site.building = building
        return site.built
