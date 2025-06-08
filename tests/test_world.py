from civsim.world import World, Biome


def test_world_generation() -> None:
    world = World(width=20, height=20, seed=1)
    assert world.width == 20
    assert world.height == 20
    biomes = {tile.biome for row in world.tiles for tile in row}
    assert {Biome.PLAINS, Biome.FOREST, Biome.DESERT, Biome.WATER}.issubset(biomes)
