from civsim.entity import Entity
from civsim.actions import MoveToAction
from civsim.simulation import Simulation
from civsim.world import World


def test_simulation_step() -> None:
    world = World(width=5, height=5, seed=3)
    entities = [Entity(id=0, x=2, y=2)]
    sim = Simulation(world=world, entities=entities)
    sim.step()
    assert sim.tick == 1


def test_reproduction_creates_new_entity() -> None:
    world = World(width=3, height=3, seed=2)
    e1 = Entity(id=0, x=1, y=1)
    e2 = Entity(id=1, x=1, y=1)
    e1.age = 20
    e2.age = 20
    e1.needs.energy = 80
    e2.needs.energy = 80
    sim = Simulation(world=world, entities=[e1, e2])
    sim.step()
    assert len(sim.entities) == 3


def test_entities_do_not_overlap_after_step() -> None:
    world = World(width=3, height=3, seed=1)
    for y in range(3):
        for x in range(3):
            tile = world.get_tile(x, y)
            tile.resources.clear()
            tile.walkable = True
    e1 = Entity(id=0, x=1, y=1)
    e2 = Entity(id=1, x=1, y=1)
    sim = Simulation(world=world, entities=[e1, e2])
    sim.step()
    positions = {(e.x, e.y) for e in sim.entities}
    assert len(positions) == len(sim.entities)


def test_reproduction_requires_conditions() -> None:
    world = World(width=3, height=3, seed=3)
    e1 = Entity(id=0, x=1, y=1)
    e2 = Entity(id=1, x=1, y=1)
    e1.age = 5  # below threshold
    e2.age = 5
    sim = Simulation(world=world, entities=[e1, e2])
    sim.step()
    assert len(sim.entities) == 2


def test_entities_die_and_are_removed() -> None:
    world = World(width=3, height=3, seed=1)
    e = Entity(id=0, x=1, y=1)
    e.needs.health = 5
    e.needs.hunger = 20
    e.needs.thirst = 20
    sim = Simulation(world=world, entities=[e])
    sim.step()
    assert len(sim.entities) == 1
    assert sim.entities[0].needs.health == 4.75


def test_seek_unexplored_when_no_known_resources() -> None:
    world = World(width=5, height=5, seed=1)
    for y in range(5):
        for x in range(5):
            t = world.get_tile(x, y)
            t.resources.clear()
            t.walkable = True
    e = Entity(id=0, x=2, y=2)
    e.needs.hunger = 15
    action = e.plan_action(world)
    assert isinstance(action, MoveToAction)
    assert action.target not in e.memory
