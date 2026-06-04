from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..screen import Screen


def draw_scrollbar(screen: Screen, x: int, y: int, h: int, total: int, scroll: int, dim: bool = False):
    """Draw a vertical scrollbar in column `x`, rows `y..y+h-1`.

    `total` is the total number of items/lines. `scroll` is the index of the
    first visible row. Thumb is omitted when content fits (`total <= h`).
    `dim` renders the whole bar in bright_black (e.g. when the owner isn't focused).
    """
    style = screen.term.bright_black if dim else (lambda s: s)
    def put(yy, glyph): screen.put(x, yy, style(glyph))

    put(y,         '╿')
    put(y + h - 1, '╽')
    for i in range(1, h - 1):
        put(y + i, '│')

    if total <= h: return
    thumb_size = max(1, h * h // total)
    thumb_max  = h - thumb_size
    thumb_pos  = (scroll * thumb_max) // (total - h)
    for i in range(thumb_pos, thumb_pos + thumb_size):
        put(y + i, '┃')
