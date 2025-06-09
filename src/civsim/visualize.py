"""Rendering utilities for ASCII and SVG output."""

from __future__ import annotations

from typing import List

from .entity import Entity
from .world import World, Biome
from .colors import BIOME_COLORS, RESOURCE_COLORS


def render_ascii(world: World, entities: List[Entity]) -> str:
    """Return an ASCII representation of the world with entities."""

    def tile_char(biome: Biome) -> str:
        return {
            Biome.PLAINS: ".",
            Biome.FOREST: "F",
            Biome.DESERT: "D",
            Biome.WATER: "~",
            Biome.MOUNTAIN: "^",
        }[biome]

    grid = [
        [
            (
                "B"
                if world.tiles[y][x].building_id is not None
                else tile_char(world.tiles[y][x].biome)
            )
            for x in range(world.width)
        ]
        for y in range(world.height)
    ]

    for entity in entities:
        if world.in_bounds(entity.x, entity.y):
            grid[entity.y][entity.x] = str(entity.id % 10)

    return "\n".join("".join(row) for row in grid)


def render_svg(world: World, entities: List[Entity], tile_size: int = 20) -> str:
    """Return an SVG representation of the world with entities and resources."""

    colors = BIOME_COLORS
    res_colors = RESOURCE_COLORS
    width_px = world.width * tile_size
    height_px = world.height * tile_size
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" height="{height_px}">'
    ]

    for y in range(world.height):
        for x in range(world.width):
            tile = world.tiles[y][x]
            color = colors[tile.biome]
            parts.append(
                f'<rect x="{x*tile_size}" y="{y*tile_size}" width="{tile_size}" height="{tile_size}" fill="{color}" />'
            )
            if tile.building_id is not None:
                parts.append(
                    f'<rect x="{x*tile_size}" y="{y*tile_size}" width="{tile_size}" height="{tile_size}" fill="#666666" opacity="0.6" />'
                )
            if tile.resources:
                r = tile_size // 6
                cx = x * tile_size + tile_size // 2
                cy = y * tile_size + tile_size // 2
                res = next(iter(tile.resources))
                rc = res_colors.get(res, "#ffd700")
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{rc}" />')

    for e in entities:
        if world.in_bounds(e.x, e.y):
            cx = e.x * tile_size + tile_size // 2
            cy = e.y * tile_size + tile_size // 2
            parts.append(
                f'<text x="{cx}" y="{cy}" font-size="{tile_size//2}" '
                'text-anchor="middle" dominant-baseline="central">'
                f"{e.id}</text>"
            )

    parts.append("</svg>")
    return "".join(parts)


def render_vision_ascii(world: World, entity: Entity) -> str:
    """Return an ASCII map showing the entity's vision area."""

    def tile_char(biome: Biome) -> str:
        return {
            Biome.PLAINS: ".",
            Biome.FOREST: "F",
            Biome.DESERT: "D",
            Biome.WATER: "~",
            Biome.MOUNTAIN: "^",
        }[biome]

    grid = [
        [tile_char(world.tiles[y][x].biome) for x in range(world.width)]
        for y in range(world.height)
    ]

    r = entity.traits.perception
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            x, y = entity.x + dx, entity.y + dy
            if world.in_bounds(x, y):
                grid[y][x] = "*"

    if world.in_bounds(entity.x, entity.y):
        grid[entity.y][entity.x] = str(entity.id % 10)

    return "\n".join("".join(row) for row in grid)


def render_memory_ascii(world: World, entity: Entity) -> str:
    """Return an ASCII map showing tiles stored in the entity's memory."""

    def tile_char(biome: Biome) -> str:
        return {
            Biome.PLAINS: ".",
            Biome.FOREST: "F",
            Biome.DESERT: "D",
            Biome.WATER: "~",
            Biome.MOUNTAIN: "^",
        }[biome]

    grid = [
        [tile_char(world.tiles[y][x].biome) for x in range(world.width)]
        for y in range(world.height)
    ]

    for x, y in entity.memory.keys():
        if world.in_bounds(x, y):
            grid[y][x] = "#"

    if world.in_bounds(entity.x, entity.y):
        grid[entity.y][entity.x] = str(entity.id % 10)

    return "\n".join("".join(row) for row in grid)
