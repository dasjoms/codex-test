from civsim.world import World, Building
from civsim.entity import Entity
from civsim.simulation import Simulation


def test_house_capacity_and_memory_sharing() -> None:
    world = World(width=5, height=5, seed=1, ensure_starting_resources=False)
    for dy in range(2):
        for dx in range(2):
            tile = world.get_tile(dx, dy)
            tile.resources.clear()
            tile.walkable = True
    house = Building(id=0, x=0, y=0, width=2, height=2, name="house", occupant_limit=1)
    assert world.place_building(house)
    e1 = Entity(id=1, x=0, y=0)
    e2 = Entity(id=2, x=0, y=0)
    assert e1.bind_to_house(house)
    assert not e2.bind_to_house(house)

    house2 = Building(id=1, x=3, y=0, width=2, height=2, name="house", occupant_limit=2)
    for dy in range(2):
        for dx in range(2):
            tile = world.get_tile(3 + dx, dy)
            tile.resources.clear()
            tile.walkable = True
    assert world.place_building(house2)
    e3 = Entity(id=3, x=3, y=0)
    e4 = Entity(id=4, x=3, y=0)
    assert e3.bind_to_house(house2)
    assert e4.bind_to_house(house2)
    e3.memory[(4, 4)] = float("inf")
    sim = Simulation(world=world, entities=[e1, e2, e3, e4])
    sim._share_house_memory()
    assert (4, 4) in e4.memory
