# Agent Instructions

This repository is meant to grow into a life/civilization simulator in Python. The goal is to support many entities on a procedurally generated map with multiple biomes and resources. This file provides guidelines and a to-do list for anyone developing in this project.

## Project Overview
- The simulation should model a world map made of tiles. Tiles belong to biomes (e.g., forest, desert, water) and may hold resources.
- Entities inhabit the map. Each entity has parameters such as health, hunger, energy, and other stats that influence their decisions.
- The world should be expandable to handle large numbers of entities efficiently.
- Procedural generation is used to create diverse maps with varying biomes and resources.
- Decision making for entities is handled via basic AI/state machines, steering behaviours, or similar approaches.

## Initial Design Ideas
1. **Map Representation**
   - Start with a grid (2D list) of tiles; each tile stores biome type and resources.
   - Provide hooks for procedural generation functions to create varied landscapes.
2. **Entity Model**
   - Minimal required attributes: `id`, `position`, `health`, `hunger`, `energy`.
   - Entities can perceive nearby tiles, move, gather resources, and interact with other entities.
3. **Simulation Loop**
   - Each tick updates the state of the world and all entities.
   - Handle resource regeneration, entity movements, and decisions per tick.
4. **Scalability**
   - Keep data structures lightweight and consider spatial partitioning (e.g., chunks) if the entity count becomes large.
5. **Testing and Visualization**
   - Include unit tests for key components (map generation, entity behaviour). Later, add basic visualization or logging to track the simulation over time.

## To‑Do List
- [ ] Set up a `src` package for Python modules.
- [ ] Implement world/map generation with at least two biomes.
- [ ] Create an `Entity` class with parameters for health and decision-making.
- [ ] Build the main simulation loop.
- [ ] Develop simple decision logic for entities to move and gather resources.
- [ ] Add unit tests using `pytest`.
- [ ] Provide example scripts to run a basic simulation.
- [ ] Optionally integrate visualization (ASCII or graphical) to observe simulation progress.

## Development Environment
- Python 3.10 or higher is recommended.
- Dependencies should be listed in `requirements.txt`.
- Install them using `pip install -r requirements.txt`.

## Code Style
- Format code with **Black** (line length 88).
- Lint with **Ruff** for Python code quality checks.
- Keep functions small and focused.
- Write docstrings for public modules, classes, and functions.

## Programmatic Checks
When making changes, run the following commands before committing:
```bash
black --check .
ruff check .
pytest -q
```
If any of these commands fail, fix the issues before submitting a pull request.

