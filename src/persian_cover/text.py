"""Persian text handling: script, digits, shaping backend, measuring, wrapping, fitting."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont, features

_RTL_RE = re.compile("[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_FONT_DIR = Path(__file__).parent / "fonts"


class ShapingUnavailableError(RuntimeError):
    """Neither libraqm nor arabic-reshaper + python-bidi is available."""


def is_rtl(text: str) -> bool:
    return _RTL_RE.search(text) is not None


def localize_digits(text: str) -> str:
    """Latin digits become Persian digits, but only inside text that contains Persian letters."""
    return text.translate(_PERSIAN_DIGITS) if is_rtl(text) else text


def shaping_backend() -> str:
    """``"raqm"`` when Pillow can shape RTL text itself, else ``"reshaper"``.

    Override with ``PERSIAN_COVER_SHAPING=raqm|reshaper`` (useful for tests).
    """
    forced = os.environ.get("PERSIAN_COVER_SHAPING", "").strip()
    if forced in ("raqm", "reshaper"):
        return forced
    if features.check("raqm"):
        return "raqm"
    try:
        import arabic_reshaper  # noqa: F401
        import bidi  # noqa: F401
    except ImportError as exc:
        raise ShapingUnavailableError(
            "Persian shaping needs libraqm (+ fribidi) in Pillow, or: "
            "pip install 'persian-cover-engine[fallback-shaping]'"
        ) from exc
    return "reshaper"


def prepare(text: str) -> str:
    """Return the string to hand to Pillow. Only the reshaper backend rewrites it."""
    if shaping_backend() == "raqm" or not is_rtl(text):
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display

    return str(get_display(arabic_reshaper.reshape(text)))


def layout_kwargs(text: str) -> dict[str, str]:
    """Extra arguments for Pillow's text functions. Only raqm understands them."""
    if shaping_backend() != "raqm":
        return {}
    return {"direction": "rtl", "language": "fa"} if is_rtl(text) else {"direction": "ltr"}


@lru_cache(maxsize=64)
def _font(path: str, size: int, raqm: bool) -> ImageFont.FreeTypeFont:
    engine = ImageFont.Layout.RAQM if raqm else ImageFont.Layout.BASIC
    return ImageFont.truetype(path, size, layout_engine=engine)


def load_font(
    size: int, bold: bool = False, path: str | os.PathLike[str] | None = None
) -> ImageFont.FreeTypeFont:
    """Bundled Vazirmatn (SIL OFL) unless ``path`` points at another TrueType/OpenType font."""
    if path is None:
        path = _FONT_DIR / ("Vazirmatn-Bold.ttf" if bold else "Vazirmatn-Regular.ttf")
    return _font(str(path), size, shaping_backend() == "raqm")


def measure(font: ImageFont.FreeTypeFont, text: str) -> float:
    return float(font.getlength(prepare(text), **layout_kwargs(text)))


def wrap(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
    """Greedy word wrap. Newlines are kept; an over-long single word keeps its own line."""
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            candidate = f"{cur} {word}".strip()
            if cur and measure(font, candidate) > max_width:
                lines.append(cur)
                cur = word
            else:
                cur = candidate
        if cur:
            lines.append(cur)
    return lines


@dataclass(frozen=True)
class Fitted:
    lines: list[str]
    size: int
    line_height: int


def fit(
    text: str,
    make_font: Callable[[int], ImageFont.FreeTypeFont],
    *,
    max_width: float,
    max_height: float,
    top: int,
    low: int,
    max_lines: int,
    line_spacing: float = 1.5,
    step: int = 4,
) -> Fitted:
    """Largest font size in ``[low, top]`` for which the wrapped text fits the box.

    A size is accepted only if the widest word fits, the line count is within ``max_lines`` and the
    block height is within ``max_height``. If nothing fits, text is wrapped at ``low`` and truncated
    to the lines that still fit (at least one).
    """
    for size in range(top, low - 1, -step):
        font = make_font(size)
        lines = wrap(text, font, max_width)
        widest = max((measure(font, w) for w in text.split()), default=0.0)
        lh = int(size * line_spacing)
        if widest <= max_width and len(lines) <= max_lines and len(lines) * lh <= max_height:
            return Fitted(lines, size, lh)
    lines = wrap(text, make_font(low), max_width)
    lh = int(low * line_spacing)
    keep = max(1, min(len(lines), int(max_height // lh), max_lines))
    return Fitted(lines[:keep], low, lh)
