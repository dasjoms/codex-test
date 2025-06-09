"""Interactive demo script for the civilization simulator."""

from civsim import Entity, Simulation, World, SimulationUI, Building


def main() -> None:
    world = World(width=120, height=80, seed=42)
    world.place_building(Building(id=0, x=10, y=10, width=4, height=3, name="house"))
    entities = [Entity(id=i, x=world.width // 2, y=world.height // 2) for i in range(5)]
    sim = Simulation(world=world, entities=entities)
    ui = SimulationUI(sim, ticks_per_second=2)
    ui.run()


if __name__ == "__main__":
    main()
