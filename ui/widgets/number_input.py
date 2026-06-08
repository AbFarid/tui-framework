from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional
from .widget import Widget

if TYPE_CHECKING:
    from ..screen import Screen


class NumberInput(Widget):
    class Style(Enum):
        NONE      = 'none'
        UNDERLINE = 'underline'

    def __init__(
        self,
        x: int = 0, y: int = 0,
        width: Optional[int] = None,
        max_digits: int = 4,
        value: int = 0,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        label: Optional[str] = None,
        style: Style = Style.UNDERLINE,
        required: bool = False,
        on_submit: Optional[Callable[[int], Any]] = None,
    ):
        is_underline  = style == NumberInput.Style.UNDERLINE
        control_w     = max_digits + 4
        label_w       = len(label) if label else 0
        gap           = 1 if label_w else 0
        bbox_w        = width if width is not None else (label_w + gap + control_w)
        bbox_h        = 1 + (1 if is_underline else 0)

        super().__init__(x, y, w=bbox_w, h=bbox_h)

        self.label       = label
        self.max_digits  = max_digits
        self.value       = self._clamp(value, min_value, max_value)
        self.min_value   = min_value
        self.max_value   = max_value
        self.style       = style
        self.required    = required
        self.on_submit   = on_submit
        self.is_dirty    = False
        self._control_w  = control_w

    @staticmethod
    def _clamp(v: int, lo: Optional[int], hi: Optional[int]) -> int:
        if lo is not None and v < lo: return lo
        if hi is not None and v > hi: return hi
        return v

    def serialize(self): return self.value
    def deserialize(self, data): self.value = self._clamp(int(data), self.min_value, self.max_value)

    def draw(self, screen: Screen):
        term = screen.term
        if self.label: screen.put(self.x, self.y, self.label)

        ctrl_x = self.x + self.w - self._control_w
        value_str = str(self.value).rjust(self.max_digits)
        control = f'− {value_str} +'
        if self.is_focused: control = term.bold(control)
        screen.put(ctrl_x, self.y, control)

        if self.style == NumberInput.Style.UNDERLINE:
            screen.put(ctrl_x, self.y + 1, '─' * self._control_w)

    def handle_key(self, key):
        if key.is_sequence:
            if key.name == 'KEY_LEFT':  self._adjust(-1); return Widget.NO_EVENT
            if key.name == 'KEY_RIGHT': self._adjust(+1); return Widget.NO_EVENT
            if key.name == 'KEY_BACKSPACE':
                if self.is_dirty:
                    s = str(self.value)[:-1]
                    self.value = self._clamp(int(s) if s else 0, self.min_value, self.max_value)
                else:
                    self.value = self._clamp(0, self.min_value, self.max_value)
                    self.is_dirty = True
                return Widget.NO_EVENT
            if key.name == 'KEY_ENTER':
                if self.on_submit: return self.on_submit(self.value)
                return self.value
            if key.name == 'KEY_ESCAPE' and not self.required: return Widget.CANCELLED
            return Widget.BUBBLE
        if key.isdigit():
            if self.is_dirty:
                new_str = str(self.value) + str(key)
                if len(new_str) <= self.max_digits:
                    self.value = self._clamp(int(new_str), self.min_value, self.max_value)
            else:
                self.value = self._clamp(int(str(key)), self.min_value, self.max_value)
                self.is_dirty = True
            return Widget.NO_EVENT
        return Widget.BUBBLE

    def _adjust(self, delta: int):
        self.value = self._clamp(self.value + delta, self.min_value, self.max_value)
        self.is_dirty = True
