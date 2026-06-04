from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Self

if TYPE_CHECKING:
    from ..screen import Screen

GAP = 3  # default spacing between widgets placed relative to one another


class Widget(ABC):
    class Event(Enum):
        NO_EVENT      = 'no_event'
        BUBBLE        = 'bubble'
        CANCELLED     = 'cancelled'
        CYCLE_OUT_FWD = 'cycle_out_fwd'
        CYCLE_OUT_BWD = 'cycle_out_bwd'

    NO_EVENT      = Event.NO_EVENT
    BUBBLE        = Event.BUBBLE
    CANCELLED     = Event.CANCELLED
    CYCLE_OUT_FWD = Event.CYCLE_OUT_FWD
    CYCLE_OUT_BWD = Event.CYCLE_OUT_BWD

    @property
    def focusable(self) -> bool:
        return True

    def __init__(self, x: int, y: int, w: int = 0, h: int = 0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_focused = False
        self.parent: Optional[Any] = None
        self.alias: Optional[str] = None

    def request_focus(self):
        if self.parent: self.parent._handle_focus_bubble(self.alias)

    def focus(self, snap: Optional[str] = None) -> Self:
        if self.is_focused: return self
        self.is_focused = True
        self.on_focus()
        return self

    def blur(self) -> Self:
        if not self.is_focused: return self
        self.is_focused = False
        self.on_blur()
        return self

    def on_focus(self): pass
    def on_blur(self):  pass

    def move_to(self, x: int, y: int) -> Self:
        self.x = x
        self.y = y
        return self

    def move_by(self, dx: int = 0, dy: int = 0) -> Self:
        return self.move_to(self.x + dx, self.y + dy)

    def place_right_of(self, target: Widget, gap: int = GAP) -> Self:
        return self.move_to(target.x + target.w + gap, target.y)

    def place_left_of(self, target: Widget, gap: int = GAP) -> Self:
        return self.move_to(target.x - self.w - gap, target.y)

    def place_above(self, target: Widget, gap: int = GAP) -> Self:
        return self.move_to(target.x, target.y - self.h - gap)

    def place_below(self, target: Widget, gap: int = GAP) -> Self:
        return self.move_to(target.x, target.y + target.h + gap)

    @abstractmethod
    def draw(self, screen: Screen) -> None: ...

    @abstractmethod
    def handle_key(self, key) -> Any: ...
