from civsim.world import World, Biome


def test_world_generation() -> None:
    world = World(width=20, height=20, seed=1)
    assert world.width == 20
    assert world.height == 20
    biomes = {tile.biome for row in world.tiles for tile in row}
    assert {Biome.PLAINS, Biome.FOREST, Biome.DESERT, Biome.WATER}.issubset(biomes)


def test_resource_tiles_not_walkable() -> None:
    world = World(width=10, height=10, seed=2)
    has_resource = False
    for row in world.tiles:
        for tile in row:
            if tile.resources:
                has_resource = True
                assert not tile.walkable
    assert has_resource
