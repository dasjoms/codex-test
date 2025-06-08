"""Tkinter-based interactive visualization for the simulation."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from .simulation import Simulation
from .entity import Entity
from .world import Biome, Resource


class SimulationUI:
    """Display and control a running :class:`~civsim.simulation.Simulation`."""

    def __init__(
        self,
        sim: Simulation,
        tile_size: int = 20,
        ticks_per_second: int = 2,
    ) -> None:
        self.sim = sim
        self.tile_size = tile_size
        self.root = tk.Tk()
        self.root.title("CivSim")
        self.running = True
        self.speed_var = tk.IntVar(value=max(1, ticks_per_second))
        canvas_width = sim.world.width * tile_size
        canvas_height = sim.world.height * tile_size
        self.canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height)
        self.canvas.pack(side="left")

        control = tk.Frame(self.root)
        control.pack(side="right", fill="both", expand=True)
        self.info_var = tk.StringVar(value="Select an entity")
        tk.Label(control, textvariable=self.info_var, justify="left").pack(anchor="nw")
        self.show_memory = tk.BooleanVar(value=False)
        tk.Checkbutton(
            control, text="Show Memory", variable=self.show_memory, command=self.redraw
        ).pack(anchor="nw")

        tk.Label(control, text="Ticks per second:").pack(anchor="nw")
        tk.Scale(
            control,
            from_=1,
            to=20,
            orient="horizontal",
            variable=self.speed_var,
        ).pack(anchor="nw")

        self.pause_button = tk.Button(
            control, text="Pause", command=self.toggle_running
        )
        self.pause_button.pack(anchor="nw", pady=4)

        self.selected: Optional[Entity] = None
        self.selected_tile: Optional[tuple[int, int]] = None
        self.canvas.bind("<Button-1>", self.on_click)

    def run(self) -> None:
        """Begin the UI loop."""

        self.redraw()
        self.root.after(self._interval_ms(), self.update)
        self.root.mainloop()

    def toggle_running(self) -> None:
        """Pause or resume the simulation."""

        self.running = not self.running
        self.pause_button.config(text="Resume" if not self.running else "Pause")

    def _interval_ms(self) -> int:
        speed = max(1, self.speed_var.get())
        return int(1000 / speed)

    def on_click(self, event: tk.Event) -> None:  # type: ignore[override]
        """Select an entity when clicking its tile."""

        x = event.x // self.tile_size
        y = event.y // self.tile_size
        for ent in self.sim.entities:
            if ent.x == x and ent.y == y:
                self.selected = ent
                self.selected_tile = None
                break
        else:
            self.selected = None
            self.selected_tile = (x, y)
        self.redraw()

    def update(self) -> None:
        """Advance the simulation and refresh the display."""

        if self.running:
            self.sim.step()
        self.redraw()
        self.root.after(self._interval_ms(), self.update)

    def redraw(self) -> None:
        """Draw the world, entities, and overlays."""

        self.canvas.delete("all")
        world = self.sim.world
        ts = self.tile_size
        colors = {
            Biome.PLAINS: "#a4c689",
            Biome.FOREST: "#228b22",
            Biome.DESERT: "#e0c469",
            Biome.WATER: "#1e90ff",
            Biome.MOUNTAIN: "#888888",
        }
        res_colors = {
            Resource.WOOD: "#8b4513",
            Resource.STONE: "#808080",
            Resource.CLAY: "#b5651d",
            Resource.WATER: "#00bfff",
            Resource.FOOD: "#ff6347",
            Resource.ANIMAL: "#fafad2",
            Resource.IRON: "#b0b0b0",
            Resource.COPPER: "#b87333",
            Resource.GOLD: "#ffd700",
            Resource.COAL: "#2f4f4f",
        }
        for y in range(world.height):
            for x in range(world.width):
                tile = world.tiles[y][x]
                color = colors[tile.biome]
                self.canvas.create_rectangle(
                    x * ts,
                    y * ts,
                    (x + 1) * ts,
                    (y + 1) * ts,
                    fill=color,
                    outline="black",
                )
                if tile.resources:
                    cx = x * ts + ts // 2
                    cy = y * ts + ts // 2
                    r = ts // 6
                    res = next(iter(tile.resources))
                    rc = res_colors.get(res, "yellow")
                    self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=rc)

        if self.selected:
            self.draw_overlays(self.selected)

        for ent in self.sim.entities:
            cx = ent.x * ts + ts // 2
            cy = ent.y * ts + ts // 2
            color = "red" if ent is self.selected else "black"
            self.canvas.create_oval(
                cx - ts // 3, cy - ts // 3, cx + ts // 3, cy + ts // 3, fill=color
            )
            self.canvas.create_text(cx, cy, text=str(ent.id), fill="white")

        self.update_info()

    def draw_overlays(self, ent: Entity) -> None:
        """Draw vision and optional memory overlays for the selected entity."""

        ts = self.tile_size
        world = self.sim.world
        r = ent.traits.perception
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x = ent.x + dx
                y = ent.y + dy
                if world.in_bounds(x, y):
                    self.canvas.create_rectangle(
                        x * ts,
                        y * ts,
                        (x + 1) * ts,
                        (y + 1) * ts,
                        outline="cyan",
                        width=1,
                    )
        if self.show_memory.get():
            for mx, my in ent.memory:
                if world.in_bounds(mx, my):
                    self.canvas.create_rectangle(
                        mx * ts,
                        my * ts,
                        (mx + 1) * ts,
                        (my + 1) * ts,
                        outline="blue",
                        width=1,
                        dash=(2, 2),
                    )

    def update_info(self) -> None:
        """Update the info panel for the currently selected entity."""

        if self.selected is None and self.selected_tile is not None:
            x, y = self.selected_tile
            tile = self.sim.world.get_tile(x, y)
            if tile.resources:
                res_text = ", ".join(
                    f"{res.name}: {amt}" for res, amt in tile.resources.items()
                )
                self.info_var.set(
                    f"Tile ({x}, {y})\nBiome: {tile.biome.value}\n{res_text}"
                )
            else:
                self.info_var.set(f"Tile ({x}, {y})\nBiome: {tile.biome.value}\nEmpty")
            return
        if not self.selected:
            self.info_var.set("Select an entity")
            return
        n = self.selected.needs
        text = (
            f"Entity {self.selected.id}\n"
            f"Pos: ({self.selected.x}, {self.selected.y})\n"
            f"Health: {n.health}/{n.max_health}\n"
            f"Hunger: {n.hunger}\n"
            f"Thirst: {n.thirst}\n"
            f"Energy: {n.energy}\n"
            f"Inventory: {self.selected.inventory}"
        )
        self.info_var.set(text)
