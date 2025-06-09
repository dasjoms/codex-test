from civsim.visualize import (
    render_ascii,
    render_svg,
    render_vision_ascii,
    render_memory_ascii,
)
from civsim.world import World
from civsim.entity import Entity


def test_render_ascii_dimensions() -> None:
    world = World(width=4, height=3, seed=0)
    entities = [Entity(id=1, x=1, y=1)]
    output = render_ascii(world, entities)
    lines = output.splitlines()
    assert len(lines) == 3
    assert all(len(line) == 4 for line in lines)


def test_render_svg_contains_svg_tag() -> None:
    world = World(width=2, height=2, seed=1)
    entities = [Entity(id=1, x=0, y=0)]
    svg = render_svg(world, entities)
    assert svg.startswith("<svg") and svg.endswith("</svg>")


def test_render_vision_ascii_marks_tiles() -> None:
    world = World(width=3, height=3, seed=0)
    e = Entity(id=1, x=1, y=1)
    e.traits.perception = 1
    output = render_vision_ascii(world, e)
    lines = output.splitlines()
    assert lines[0][1] == "*"  # north
    assert lines[2][1] == "*"  # south
    assert lines[1][0] == "*"  # west
    assert lines[1][2] == "*"  # east


def test_render_memory_ascii_marks_memory() -> None:
    world = World(width=3, height=3, seed=0)
    e = Entity(id=1, x=1, y=1)
    for pos in {(0, 0), (2, 2)}:
        e.memory[pos] = float("inf")
    output = render_memory_ascii(world, e)
    lines = output.splitlines()
    assert lines[0][0] == "#"
    assert lines[2][2] == "#"
