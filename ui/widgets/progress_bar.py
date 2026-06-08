from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from .widget import Widget

if TYPE_CHECKING:
    from ..screen import Screen


class ProgressBar(Widget):
    FILLED = '█'
    EMPTY  = '░'

    @property
    def focusable(self) -> bool:
        return False

    def __init__(
        self,
        x: int = 0, y: int = 0,
        bar_w: int = 20,
        value: float = 0, max_value: float = 100,
        label: Optional[str] = None,
        show_value: bool = True,
        percent: bool = False,
        style: Optional[str] = None,
    ):
        self.label      = label
        self.bar_w      = bar_w
        self.max_value  = max(1, max_value)
        self._value     = self._clamp(value)
        self.show_value = show_value
        self.percent    = percent
        self.style      = style
        self._value_w   = len('100%') if percent else len(f'{int(self.max_value)}/{int(self.max_value)}')

        head = len(label) + 1 if label else 0
        tail = self._value_w + 1 if show_value else 0
        super().__init__(x, y, w=head + bar_w + tail, h=1)

    def _clamp(self, v: float) -> float:
        return max(0, min(v, self.max_value))

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float):
        self._value = self._clamp(v)

    @property
    def ratio(self) -> float:
        return self._value / self.max_value

    def serialize(self): return self._value
    def deserialize(self, data): self.value = float(data)

    def _value_text(self) -> str:
        if self.percent: text = f'{round(self.ratio * 100)}%'
        else:
            v = int(self._value) if self._value == int(self._value) else self._value
            text = f'{v}/{int(self.max_value)}'
        return text.rjust(self._value_w)

    def draw(self, screen: Screen):
        x = self.x
        if self.label:
            screen.put(x, self.y, self.label)
            x += len(self.label) + 1

        fill = round(self.ratio * self.bar_w)
        bar  = self.FILLED * fill + self.EMPTY * (self.bar_w - fill)
        if self.style:
            attr = getattr(screen.term, self.style, None)
            if attr: bar = attr(bar)
        screen.put(x, self.y, bar)

        if self.show_value: screen.put(x + self.bar_w + 1, self.y, self._value_text())

    def handle_key(self, key): return Widget.BUBBLE
