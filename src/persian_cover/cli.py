"""Command line: ``persian-cover "عنوان" --subtitle ... --out cover.png``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .color import PALETTES
from .layout import SIZES
from .render import CoverSpec, render
from .text import ShapingUnavailableError


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="persian-cover", description=__doc__)
    p.add_argument("title", nargs="?", help="cover title (use \\n for a line break)")
    p.add_argument("--subtitle", default="")
    p.add_argument("--highlight", default="", help="title word to draw in the accent colour")
    p.add_argument(
        "--handle", default="", help="e.g. @yourname, drawn at the bottom of the safe area"
    )
    p.add_argument("--size", choices=sorted(SIZES), default="post")
    p.add_argument("--palette", choices=sorted(PALETTES), default="teal")
    p.add_argument("--background", choices=("radial", "linear"), default="radial")
    p.add_argument("--outline", action="store_true", help="accent rectangle inside the safe area")
    p.add_argument(
        "--no-grid-safe", action="store_true", help="use the whole canvas, not the grid crop"
    )
    p.add_argument("--font", help="regular .ttf/.otf (default: bundled Vazirmatn)")
    p.add_argument("--bold-font", help="bold .ttf/.otf")
    p.add_argument("--spec", type=Path, help="JSON file with CoverSpec fields (flags are ignored)")
    p.add_argument("--out", type=Path, default=Path("cover.png"))
    p.add_argument(
        "--contrast-report", action="store_true", help="print WCAG contrast of all palettes"
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.contrast_report:
        print(f"{'palette':10} {'text':>6} {'subtitle':>9} {'accent':>7}  WCAG min 4.5 / 3")
        for pal in PALETTES.values():
            print(
                f"{pal.name:10} {pal.text_contrast():6.1f} {pal.subtitle_contrast():9.1f} "
                f"{pal.accent_contrast():7.1f}"
            )
        return 0
    if args.spec:
        spec = CoverSpec(**json.loads(args.spec.read_text(encoding="utf-8")))
    elif args.title:
        spec = CoverSpec(
            title=args.title.replace("\\n", "\n"),
            subtitle=args.subtitle.replace("\\n", "\n"),
            handle=args.handle,
            highlight=args.highlight,
            size=args.size,
            palette=args.palette,
            background=args.background,
            outline=args.outline,
            grid_safe=not args.no_grid_safe,
            font_path=args.font,
            bold_font_path=args.bold_font,
        )
    else:
        _parser().error("give a title or --spec")
    try:
        im = render(spec)
    except (ShapingUnavailableError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    im.save(args.out)
    print(f"{args.out}  {im.width}x{im.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
