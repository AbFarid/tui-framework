from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from .widget import Widget

if TYPE_CHECKING:
    from ..screen import Screen


class Label(Widget):
    @property
    def focusable(self) -> bool:
        return False

    def __init__(
        self,
        text: str,
        x: int = 0, y: int = 0,
        color: Optional[str] = None,  # blessed attr (e.g. 'bold', 'cyan', 'bold_yellow') or None
    ):
        lines = text.splitlines() or ['']
        w = max(len(line) for line in lines)
        h = len(lines)
        super().__init__(x, y, w=w, h=h)
        self.lines = lines
        self.color = color

    def draw(self, screen: Screen):
        for i, line in enumerate(self.lines):
            text = line
            if self.color:
                style = getattr(screen.term, self.color, None)
                if style: text = style(text)
            screen.put(self.x, self.y + i, text)

    def handle_key(self, _key): return Widget.BUBBLE