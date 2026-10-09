"""Colour maths and palettes, with WCAG 2.x contrast checks."""

from __future__ import annotations

from dataclasses import dataclass

RGB = tuple[int, int, int]

TEXT_MIN_CONTRAST = 4.5  # WCAG AA, normal text
ACCENT_MIN_CONTRAST = 3.0  # WCAG AA, large text / graphical objects


def parse_hex(value: str) -> RGB:
    """Parse ``#rrggbb`` (the ``#`` is optional) into an RGB tuple."""
    h = value.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"expected a 6-digit hex colour, got {value!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _linear(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: RGB) -> float:
    r, g, b = rgb
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contrast_ratio(a: RGB, b: RGB) -> float:
    """WCAG contrast ratio between two colours, from 1.0 (identical) to 21.0 (black on white)."""
    hi, lo = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def mix(a: RGB, b: RGB, t: float) -> RGB:
    """Linear blend: ``t=0`` gives ``a``, ``t=1`` gives ``b``."""
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


@dataclass(frozen=True)
class Palette:
    """Two background colours plus text and accent colours, all as ``#rrggbb``.

    ``edge`` is the colour at the corners / outer rim, ``center`` the colour in the middle
    (radial) or at the opposite corner (linear).
    """

    name: str
    edge: str
    center: str
    accent: str
    text: str

    def backgrounds(self) -> tuple[RGB, RGB]:
        return parse_hex(self.edge), parse_hex(self.center)

    def text_contrast(self) -> float:
        """Worst-case contrast of the text colour against either background colour."""
        t = parse_hex(self.text)
        return min(contrast_ratio(t, bg) for bg in self.backgrounds())

    def accent_contrast(self) -> float:
        a = parse_hex(self.accent)
        return min(contrast_ratio(a, bg) for bg in self.backgrounds())

    def subtitle_color(self) -> RGB:
        """Text colour softened 22% towards the rim colour, to separate subtitle from title."""
        return mix(parse_hex(self.text), parse_hex(self.edge), 0.22)

    def subtitle_contrast(self) -> float:
        s = self.subtitle_color()
        return min(contrast_ratio(s, bg) for bg in self.backgrounds())

    def validate(self) -> None:
        if self.text_contrast() < TEXT_MIN_CONTRAST:
            raise ValueError(f"{self.name}: text contrast {self.text_contrast():.1f} < 4.5")
        if self.accent_contrast() < ACCENT_MIN_CONTRAST:
            raise ValueError(f"{self.name}: accent contrast {self.accent_contrast():.1f} < 3.0")
        if self.subtitle_contrast() < TEXT_MIN_CONTRAST:
            raise ValueError(f"{self.name}: subtitle contrast {self.subtitle_contrast():.1f} < 4.5")


PALETTES: dict[str, Palette] = {
    p.name: p
    for p in (
        Palette("midnight", edge="#0f172a", center="#1e3a8a", accent="#fbbf24", text="#ffffff"),
        Palette("teal", edge="#001e20", center="#025259", accent="#e3c99a", text="#f4eee2"),
        Palette("ivory", edge="#e7ddc9", center="#f4eee2", accent="#02494f", text="#06272a"),
        Palette("graphite", edge="#0b0b0c", center="#2a2a2e", accent="#4ade80", text="#f5f5f5"),
    )
}
