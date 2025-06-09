from civsim.world import World, Resource
from civsim.entity import Entity


def test_world_generation() -> None:
    world = World(width=20, height=20, seed=1)
    assert world.width == 20
    assert world.height == 20
    biomes = {tile.biome for row in world.tiles for tile in row}
    assert len(biomes) >= 3


def test_resource_tiles_not_walkable() -> None:
    world = World(width=10, height=10, seed=2)
    has_resource = False
    for row in world.tiles:
        for tile in row:
            if tile.resources:
                has_resource = True
                assert not tile.walkable
    assert has_resource


def test_berry_bush_regrows() -> None:
    world = World(width=3, height=3, seed=1)
    tile = world.get_tile(1, 1)
    tile.resources.clear()
    tile.resources[Resource.BERRY_BUSH] = 1
    tile.walkable = False

    e = Entity(id=1, x=0, y=0)
    e.memory[(1, 1)] = float("inf")
    e.move(1, 1, world)
    e.gather(world)

    for _ in range(100):
        world.tick_regrowth()

    assert Resource.BERRY_BUSH in tile.resources
    assert not tile.walkable
