"""Interactive demo script for the civilization simulator."""

from civsim import Entity, Simulation, World, SimulationUI


def main() -> None:
    world = World(width=60, height=40, seed=42)
    entities = [Entity(id=i, x=world.width // 2, y=world.height // 2) for i in range(5)]
    sim = Simulation(world=world, entities=entities)
    ui = SimulationUI(sim, ticks_per_second=2)
    ui.run()


if __name__ == "__main__":
    main()
