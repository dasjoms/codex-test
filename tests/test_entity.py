from civsim.entity import Entity
from civsim.world import World, Resource


def test_entity_movement_and_gathering() -> None:
    world = World(width=3, height=3, seed=2)
    entity = Entity(id=1, x=1, y=1)
    tile = world.get_tile(1, 1)
    tile.resources[Resource.WOOD] = 1

    entity.move(1, 0, world)
    assert (entity.x, entity.y) in [(2, 1), (1, 1)]  # move stays in bounds

    entity.x, entity.y = 1, 1
    entity.gather(world)
    assert entity.inventory == 1
    assert not tile.resources


def test_entity_needs_update_and_rest() -> None:
    world = World(width=3, height=3, seed=1)
    entity = Entity(id=1, x=1, y=1)
    entity.needs.energy = 1

    entity.take_turn(world)
    assert entity.needs.hunger == 2
    assert entity.needs.thirst == 2
    assert entity.needs.energy == 20  # rested when energy depleted


def test_entity_age_causes_death() -> None:
    world = World(width=3, height=3, seed=1)
    entity = Entity(id=1, x=1, y=1, max_age=2)

    entity.take_turn(world)
    entity.take_turn(world)
    entity.take_turn(world)
    assert entity.needs.health == 0


def test_entity_memory_and_relationships() -> None:
    world = World(width=3, height=3, seed=1)
    e1 = Entity(id=1, x=1, y=1)
    e2 = Entity(id=2, x=1, y=1)

    e1.add_relationship(e2, "friend")
    assert e1.relationships[2] == "friend"

    e1.take_turn(world)
    assert (1, 1) in e1.memory
