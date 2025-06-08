# TODO

This file tracks upcoming tasks for the civilization simulator. Items are ordered so that each phase builds on the previous one.

## 1. Core Framework
- [x] Set up project structure with `civsim` package and tests
- [x] Implement `World` class with grid of tiles and basic biomes
- [x] Add resource node placement on a finer subgrid
- [x] Create `Entity` class with health, hunger, thirst, energy, and inventory count
- [x] Build `Simulation` loop to update entities each tick
- [x] Provide ASCII renderer and example `run.py`

## 2. Extended World Generation
- [x] Introduce additional biomes (desert, water, etc.)
- [x] Support specialized resource nodes by biome

## 3. Advanced Entity Needs
- [x] Expand health system with `max_health` and injuries
- [x] Add fatigue requiring rest and recovery
- [x] Implement morale/happiness tracking
- [x] Include base attributes or skills (strength, agility, intelligence)
- [x] Add age and lifespan stages

## 4. Social Behaviour
- [x] Implement perception range and memory of explored tiles
- [x] Track relationships (friendships, rivalries, families)
- [x] Add personality traits influencing decisions
- [x] Enable reproduction and family groups

## 5. Decision Making Improvements
- [ ] Prioritize needs (hunger, thirst, energy, morale)
- [ ] Use perception and memory when selecting actions

## 6. Inventory and Equipment
- [ ] Replace simple resource counter with inventory of items
- [ ] Add equipment slots that grant bonuses

## 7. Visualization Enhancements
- [ ] Render entities with health bars and inventory icons
- [ ] Optionally move from ASCII to SVG or GUI output

Each phase builds toward a more realistic and feature-rich simulation. Completing items in order should keep the codebase testable and manageable.
