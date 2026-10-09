"""Where text may go. Pure geometry, no drawing."""

from __future__ import annotations

Box = tuple[int, int, int, int]  # x0, y0, x1, y1

SIZES: dict[str, tuple[int, int]] = {
    "post": (1080, 1350),  # Instagram 4:5 post
    "square": (1080, 1080),
    "story": (1080, 1920),  # story / reel cover, 9:16
    "wide": (1920, 1080),  # YouTube thumbnail, 16:9
}


def grid_frame(width: int, height: int, aspect: tuple[int, int] = (3, 4)) -> Box:
    """The part of the image shown in a profile grid tile: the centre crop with the given aspect.

    Landscape images are not cropped. Anything placed outside this box can be cut off in the grid,
    and the corners of the box are covered by overlay icons (play, view count).
    """
    aw, ah = aspect
    if width > height:
        return 0, 0, width, height
    if height * aw > width * ah:  # taller than the tile -> crop top and bottom
        ch = width * ah // aw
        y0 = (height - ch) // 2
        return 0, y0, width, y0 + ch
    cw = height * aw // ah  # wider than the tile -> crop the sides
    x0 = (width - cw) // 2
    return x0, 0, x0 + cw, height


def contains(outer: Box, inner: Box) -> bool:
    return (
        inner[0] >= outer[0]
        and inner[1] >= outer[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )
