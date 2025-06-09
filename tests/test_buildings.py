from civsim.world import World, Building, Blueprint, Resource
from civsim.entity import Entity
from civsim.actions import BuildAction
from civsim.simulation import Simulation


def test_place_building_blocks_tiles() -> None:
    world = World(width=5, height=5, seed=1, ensure_starting_resources=False)
    for dy in range(3):
        for dx in range(2):
            tile = world.get_tile(1 + dx, 1 + dy)
            tile.resources.clear()
            tile.walkable = True
    b = Building(id=0, x=1, y=1, width=2, height=3, name="hut")
    assert world.place_building(b)
    for dy in range(3):
        for dx in range(2):
            tile = world.get_tile(1 + dx, 1 + dy)
            assert not tile.walkable
            assert tile.building_id == b.id


def test_cannot_overlap_building() -> None:
    world = World(width=5, height=5, seed=2, ensure_starting_resources=False)
    b1 = Building(id=0, x=0, y=0, width=2, height=2)
    assert world.place_building(b1)
    b2 = Building(id=1, x=1, y=1, width=2, height=2)
    assert not world.place_building(b2)


def test_build_action_places_building() -> None:
    world = World(width=4, height=4, seed=3, ensure_starting_resources=False)
    for dy in range(2):
        for dx in range(2):
            tile = world.get_tile(1 + dx, 1 + dy)
            tile.resources.clear()
            tile.walkable = True
    e = Entity(id=1, x=1, y=1)
    e.inventory.add(Resource.WOOD, 4)
    bp = Blueprint(
        name="house",
        width=2,
        height=2,
        cost={Resource.WOOD: 4},
        bonuses={"morale": 5},
        occupant_limit=2,
        build_time=3,
    )
    action = BuildAction(bp, 1, 1)
    e.current_action = action
    action.start(e, world)
    sim = Simulation(world=world, entities=[e])
    for _ in range(bp.build_time):
        sim.step()
    assert any(b.name == "house" for b in world.buildings)
    assert e.skills.construction == 1
    assert e.home_id is not None


def test_group_building_speeds_up() -> None:
    world = World(width=4, height=4, seed=4, ensure_starting_resources=False)
    for dy in range(2):
        for dx in range(2):
            tile = world.get_tile(1 + dx, 1 + dy)
            tile.resources.clear()
            tile.walkable = True
    e1 = Entity(id=1, x=1, y=1)
    e1.inventory.add(Resource.WOOD, 4)
    e2 = Entity(id=2, x=1, y=1)
    bp = Blueprint(
        name="house",
        width=2,
        height=2,
        cost={Resource.WOOD: 4},
        bonuses={"morale": 5},
        occupant_limit=2,
        build_time=4,
    )
    act = BuildAction(bp, 1, 1)
    e1.current_action = act
    act.start(e1, world)
    sim = Simulation(world=world, entities=[e1, e2])
    for _ in range(bp.build_time):
        sim.step()
    house = next((b for b in world.buildings if b.name == "house"), None)
    assert house is not None
    assert len(house.occupant_ids) == 2
