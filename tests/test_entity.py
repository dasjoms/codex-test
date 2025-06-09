from civsim.entity import Entity, ReproductionRules
from civsim.world import World, Resource
from civsim.simulation import Simulation


def test_entity_movement_and_gathering() -> None:
    world = World(width=3, height=3, seed=2)
    entity = Entity(id=1, x=1, y=1)
    tile = world.get_tile(1, 2)
    tile.resources.clear()
    tile.resources[Resource.WOOD] = 1
    tile.walkable = False

    entity.gather(world)
    assert entity.inventory.items[Resource.WOOD] == 1
    assert not tile.resources
    assert tile.walkable


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


def test_can_reproduce_rules() -> None:
    rules = ReproductionRules()
    entity = Entity(id=1, x=1, y=1)
    entity.age = rules.min_age
    entity.needs.energy = rules.energy_min
    entity.needs.hunger = rules.hunger_max
    entity.needs.thirst = rules.thirst_max
    entity.needs.health = rules.health_min
    assert entity.can_reproduce(rules, 0)

    entity.age = rules.min_age - 1
    assert not entity.can_reproduce(rules, 0)


def test_loneliness_updates_with_neighbors() -> None:
    world = World(width=3, height=3, seed=1)
    e1 = Entity(id=1, x=1, y=1)
    e2 = Entity(id=2, x=2, y=1)
    sim = Simulation(world=world, entities=[e1, e2])
    sim.step()  # both start adjacent, should decrease loneliness for e1
    assert e1.needs.loneliness == 0
    sim.entities.pop()  # remove e2
    sim.step()
    assert e1.needs.loneliness == 1


def test_entity_moves_to_remembered_resource() -> None:
    world = World(width=3, height=2, seed=1)
    tile = world.get_tile(2, 0)
    tile.resources.clear()
    tile.resources[Resource.FOOD] = 1
    tile.walkable = False

    e = Entity(id=1, x=0, y=0)
    e.memory.update({(0, 0), (1, 0), (2, 0)})
    e.needs.hunger = 15

    for _ in range(3):
        e.take_turn(world)

    assert (e.x, e.y) == (1, 0)
    assert Resource.FOOD in e.inventory.items
