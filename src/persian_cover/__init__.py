"""Persian (RTL) cover images: correct shaping, WCAG-checked palettes, grid-safe layout."""

from .color import PALETTES, Palette, contrast_ratio
from .layout import SIZES, grid_frame
from .render import CoverSpec, Layout, plan, render, render_bytes
from .text import ShapingUnavailableError, shaping_backend

__all__ = [
    "PALETTES",
    "SIZES",
    "CoverSpec",
    "Layout",
    "Palette",
    "ShapingUnavailableError",
    "contrast_ratio",
    "grid_frame",
    "plan",
    "render",
    "render_bytes",
    "shaping_backend",
]
__version__ = "0.1.0"
