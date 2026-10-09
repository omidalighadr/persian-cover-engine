"""Gradient backgrounds built from Pillow primitives (no NumPy)."""

from __future__ import annotations

from PIL import Image, ImageChops

from .color import RGB

# Image.radial_gradient("L") reaches 179 at the middle of each edge and 255 in the corners.
# Dividing by a slightly smaller number makes the rim colour arrive just before the edge.
_RADIAL_RIM_VALUE = 168.0


def _lut(edge: RGB, center: RGB, saturate_at: float = 255.0) -> list[list[int]]:
    """Per-channel lookup tables mapping a 0..255 mask value (0 = centre) to a colour."""
    tables: list[list[int]] = []
    for k in range(3):
        table = []
        for v in range(256):
            t = min(1.0, v / saturate_at)
            table.append(round(center[k] + (edge[k] - center[k]) * t))
        tables.append(table)
    return tables


def _colorize(mask: Image.Image, edge: RGB, center: RGB, saturate_at: float) -> Image.Image:
    luts = _lut(edge, center, saturate_at)
    return Image.merge("RGB", [mask.point(luts[k]) for k in range(3)])


def radial(width: int, height: int, edge: RGB, center: RGB) -> Image.Image:
    """Soft vignette: ``center`` in the middle fading to ``edge`` towards the rim."""
    base = Image.radial_gradient("L").resize((int(width * 1.5), int(height * 1.5)), Image.BICUBIC)
    x0, y0 = (base.width - width) // 2, (base.height - height) // 2
    mask = base.crop((x0, y0, x0 + width, y0 + height))
    return _colorize(mask, edge, center, _RADIAL_RIM_VALUE)


def linear(width: int, height: int, edge: RGB, center: RGB) -> Image.Image:
    """Diagonal gradient: ``edge`` at the top-left corner, ``center`` at the bottom-right."""
    vertical = Image.linear_gradient("L").resize((width, height), Image.BICUBIC)
    horizontal = (
        Image.linear_gradient("L").transpose(Image.Transpose.ROTATE_90).resize((width, height))
    )
    mask = ImageChops.add(vertical, horizontal, scale=2.0)
    return _colorize(mask, edge, center, 255.0)
