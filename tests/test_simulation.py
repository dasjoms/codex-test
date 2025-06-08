from civsim.entity import Entity
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
    e1.needs.energy = 60
    e2.needs.energy = 60
    sim = Simulation(world=world, entities=[e1, e2])
    sim.step()
    assert len(sim.entities) == 3
