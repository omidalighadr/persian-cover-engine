"""Plan the layout of a cover, then draw it."""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont

from . import background
from .color import PALETTES, RGB, Palette, parse_hex
from .layout import SIZES, Box, grid_frame
from .text import (
    fit,
    is_rtl,
    layout_kwargs,
    load_font,
    localize_digits,
    measure,
    prepare,
    shaping_backend,
)

_PUNCT = " ‌؟?!.,،:;؛«»\"'()[]{}-–—"


@dataclass(frozen=True)
class CoverSpec:
    title: str
    subtitle: str = ""
    handle: str = ""
    highlight: str = ""  # one word of the title, drawn in the accent colour
    size: str = "post"  # key of layout.SIZES
    palette: str = "teal"  # key of color.PALETTES
    background: str = "radial"  # "radial" | "linear"
    outline: bool = False  # draw an accent rectangle just inside the safe box
    grid_safe: bool = True  # lay text out inside the profile-grid crop
    grid_aspect: tuple[int, int] = (3, 4)
    font_path: str | None = None
    bold_font_path: str | None = None


@dataclass(frozen=True)
class PlacedLine:
    text: str
    cx: int  # horizontal centre
    y: int  # top of the line box
    size: int  # font size in px
    width: float  # measured width in px

    @property
    def box(self) -> Box:
        half = self.width / 2
        return int(self.cx - half), self.y, int(self.cx + half) + 1, self.y + self.size


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    safe: Box
    title: list[PlacedLine] = field(default_factory=list)
    subtitle: list[PlacedLine] = field(default_factory=list)
    handle: PlacedLine | None = None
    bar: Box | None = None


def _canvas(spec: CoverSpec) -> tuple[int, int]:
    try:
        return SIZES[spec.size]
    except KeyError:
        raise ValueError(f"unknown size {spec.size!r}; choose from {sorted(SIZES)}") from None


def _palette(spec: CoverSpec) -> Palette:
    try:
        return PALETTES[spec.palette]
    except KeyError:
        raise ValueError(
            f"unknown palette {spec.palette!r}; choose from {sorted(PALETTES)}"
        ) from None


def plan(spec: CoverSpec) -> Layout:
    """Compute font sizes, wrapped lines and positions. Nothing is drawn here."""
    if not spec.title.strip():
        raise ValueError("title must not be empty")
    w, h = _canvas(spec)
    wide = w > h
    safe = grid_frame(w, h, spec.grid_aspect) if spec.grid_safe else (0, 0, w, h)
    fw, fh = safe[2] - safe[0], safe[3] - safe[1]
    title = localize_digits(spec.title.strip())
    sub = localize_digits(spec.subtitle.strip())

    # text box: 7% side padding and 15%..76% of the safe height (wide: 9% and 20%..80%)
    if wide:
        box: Box = (int(w * 0.09), int(h * 0.20), w - int(w * 0.09), int(h * 0.80))
    else:
        padx = int(fw * 0.07)
        box = (safe[0] + padx, safe[1] + int(fh * 0.15), safe[2] - padx, safe[1] + int(fh * 0.76))
    bw, bh = box[2] - box[0], box[3] - box[1]

    def bold(size: int) -> ImageFont.FreeTypeFont:
        return load_font(size, True, spec.bold_font_path)

    def regular(size: int) -> ImageFont.FreeTypeFont:
        return load_font(size, False, spec.font_path)

    top = int((h if wide else min(fw, fh)) * (0.12 if wide else 0.135))
    t = fit(
        title,
        bold,
        max_width=bw,
        max_height=bh * (0.72 if sub else 0.9),
        top=top,
        low=int(top * 0.45),
        max_lines=5,
    )
    s = None
    if sub:  # the subtitle never exceeds 46% of the title size
        s = fit(
            sub,
            regular,
            max_width=bw,
            max_height=bh * 0.28,
            top=int(t.size * 0.46),
            low=26,
            max_lines=3,
        )

    block = len(t.lines) * t.line_height
    total = block
    if s:
        total += int(t.line_height * 0.35) + len(s.lines) * s.line_height
    cx = (box[0] + box[2]) // 2
    y = box[1] + max(int(t.line_height * 0.45), (bh - total) // 2)  # leave room for the bar

    bar_w = int(bw * 0.14)
    bar_h = max(8, h // 140)
    bar_y = y - int(t.line_height * 0.35)
    bar: Box = (cx - bar_w // 2, bar_y, cx + bar_w // 2, bar_y + bar_h)

    bold_font = bold(t.size)
    title_lines = []
    for ln in t.lines:
        title_lines.append(PlacedLine(ln, cx, y, t.size, measure(bold_font, ln)))
        y += t.line_height
    sub_lines: list[PlacedLine] = []
    if s:
        y += int(t.line_height * 0.35)
        reg_font = regular(s.size)
        for ln in s.lines:
            sub_lines.append(PlacedLine(ln, cx, y, s.size, measure(reg_font, ln)))
            y += s.line_height

    handle = None
    if spec.handle.strip():
        hs = max(30, int(w * 0.038))
        hy = h - int(w * 0.09) if wide else safe[1] + int(fh * 0.80)
        text = spec.handle.strip()
        handle = PlacedLine(text, w // 2, hy, hs, measure(regular(hs), text))
    return Layout(w, h, safe, title_lines, sub_lines, handle, bar)


def _norm(word: str) -> str:
    return word.strip(_PUNCT).lower()


def _draw_line(
    d: ImageDraw.ImageDraw,
    line: PlacedLine,
    font: ImageFont.FreeTypeFont,
    fill: RGB,
    accent: RGB,
    highlight: str,
    used: list[bool],
) -> None:
    """Draw one centred line. The first word equal to ``highlight`` is drawn in ``accent``."""
    off = max(2, line.size // 40)
    shadow = (0, 0, 0, 90)
    words = line.text.split()
    idx = -1
    if highlight and not used:
        key = _norm(highlight)
        idx = next((i for i, wd in enumerate(words) if _norm(wd) == key), -1)
    if idx < 0:
        s = prepare(line.text)
        kw = layout_kwargs(line.text)
        d.text((line.cx + off, line.y + off), s, font=font, fill=shadow, anchor="ma", **kw)
        d.text((line.cx, line.y), s, font=font, fill=fill, anchor="ma", **kw)
        return
    used.append(True)
    rtl = is_rtl(line.text)
    if rtl:
        space = measure(font, "ا ا") - measure(font, "اا")
    else:
        space = measure(font, "a a") - measure(font, "aa")
    segments = [(words[:idx], fill), ([words[idx]], accent), (words[idx + 1 :], fill)]
    segments = [(seg, col) for seg, col in segments if seg]
    widths = [measure(font, " ".join(seg)) for seg, _ in segments]
    total = sum(widths) + space * (len(segments) - 1)
    # RTL: first logical segment sits at the right end; LTR: at the left end
    cursor = line.cx + total / 2 if rtl else line.cx - total / 2
    for (seg, col), wd in zip(segments, widths, strict=True):
        text = " ".join(seg)
        s, kw = prepare(text), layout_kwargs(text)
        anchor = "ra" if rtl else "la"
        x = cursor
        d.text((x + off, line.y + off), s, font=font, fill=shadow, anchor=anchor, **kw)
        d.text((x, line.y), s, font=font, fill=col, anchor=anchor, **kw)
        cursor += -(wd + space) if rtl else (wd + space)


def render(spec: CoverSpec) -> Image.Image:
    """Render the cover as an RGB image."""
    shaping_backend()  # fail early with a clear message if Persian cannot be shaped
    pal = _palette(spec)
    layout = plan(spec)
    edge, center = pal.backgrounds()
    make_bg = background.radial if spec.background == "radial" else background.linear
    if spec.background not in ("radial", "linear"):
        raise ValueError("background must be 'radial' or 'linear'")
    im = make_bg(layout.width, layout.height, edge, center)
    d = ImageDraw.Draw(im, "RGBA")
    accent, text_col, sub_col = parse_hex(pal.accent), parse_hex(pal.text), pal.subtitle_color()

    if spec.outline:
        m = int((layout.safe[2] - layout.safe[0]) * 0.035)
        x0, y0, x1, y1 = layout.safe
        d.rectangle(
            (x0 + m, y0 + m, x1 - m, y1 - m),
            outline=accent + (255,),
            width=max(4, layout.width // 270),
        )
    if layout.bar:
        d.rounded_rectangle(layout.bar, radius=6, fill=accent)

    used: list[bool] = []
    for ln in layout.title:
        _draw_line(
            d,
            ln,
            load_font(ln.size, True, spec.bold_font_path),
            text_col,
            accent,
            localize_digits(spec.highlight),
            used,
        )
    for ln in layout.subtitle:
        font = load_font(ln.size, False, spec.font_path)
        d.text(
            (ln.cx, ln.y),
            prepare(ln.text),
            font=font,
            fill=sub_col,
            anchor="ma",
            **layout_kwargs(ln.text),
        )
    if layout.handle:
        ln = layout.handle
        font = load_font(ln.size, False, spec.font_path)
        d.text(
            (ln.cx, ln.y),
            prepare(ln.text),
            font=font,
            fill=accent,
            anchor="ms",
            **layout_kwargs(ln.text),
        )
    return im


def render_bytes(spec: CoverSpec, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    render(spec).save(buf, format=fmt, **({"quality": 92} if fmt.upper() == "JPEG" else {}))
    return buf.getvalue()
