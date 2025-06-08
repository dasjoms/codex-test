# Agent Instructions

This repository is meant to grow into a life/civilization simulator in Python. The goal is to support many entities on a procedurally generated map with multiple biomes and resources. This file provides guidelines and a to-do list for anyone developing in this project.

## Project Overview
- The simulation should model a world map made of tiles. Tiles belong to biomes (e.g., forest, desert, water) and may hold resources.
- Entities inhabit the map. Each entity has parameters such as health, hunger, energy, and other stats that influence their decisions.
- The world should be expandable to handle large numbers of entities efficiently.
- Procedural generation is used to create diverse maps with varying biomes and resources.
- Decision making for entities is handled via basic AI/state machines, steering behaviours, or similar approaches.


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

