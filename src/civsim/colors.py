"""Shared color mappings for biomes and resources."""

from __future__ import annotations

from .world import Biome, Resource

BIOME_COLORS: dict[Biome, str] = {
    Biome.PLAINS: "#a4c689",
    Biome.FOREST: "#228b22",
    Biome.DESERT: "#e0c469",
    Biome.WATER: "#1e90ff",
    Biome.MOUNTAIN: "#888888",
}

RESOURCE_COLORS: dict[Resource, str] = {
    Resource.WOOD: "#8b4513",
    Resource.STONE: "#808080",
    Resource.CLAY: "#b5651d",
    Resource.WATER: "#00bfff",
    Resource.BERRY_BUSH: "#ff6347",
    Resource.ANIMAL: "#fafad2",
    Resource.BERRIES: "#ff9999",
    Resource.MEAT: "#cd5c5c",
    Resource.IRON: "#b0b0b0",
    Resource.COPPER: "#b87333",
    Resource.GOLD: "#ffd700",
    Resource.COAL: "#2f4f4f",
}
