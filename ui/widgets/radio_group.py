from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, Union
from .widget import Widget
from .list import ListItem

if TYPE_CHECKING:
    from ..screen import Screen


class RadioGroup(Widget):
    class Orientation(Enum):
        VERTICAL   = 'vertical'
        HORIZONTAL = 'horizontal'

    def __init__(
        self,
        x: int = 0, y: int = 0,
        items: Optional[list[Union[str, ListItem]]] = None,
        w: Optional[int] = None,
        orientation: Orientation = Orientation.VERTICAL,
        selected: int = 0,
        glyph_on: str = '◉ ',
        glyph_off: str = '○ ',
        highlight: Optional[str] = 'bold',
        gap: int = 0,
        auto_key: bool = False,
        on_change: Optional[Callable[[ListItem], Any]] = None,
    ):
        super().__init__(x, y)
        self.items: list[ListItem] = [self._wrap(it) for it in (items or [])]
        self.orientation = orientation
        self.glyph_on  = glyph_on
        self.glyph_off = glyph_off
        self.highlight = highlight
        self.gap = gap
        self.auto_key = auto_key
        self.on_change = on_change
        self.selected = selected
        if auto_key: self._assign_auto_keys()
        if self.items and self.items[self.selected].disabled: self._move(+1)

        self.w = w if w is not None else self._compute_width()
        self.h = self._compute_height()

    @staticmethod
    def _wrap(it: Union[str, ListItem]) -> ListItem:
        return it if isinstance(it, ListItem) else ListItem(label=it)

    def _assign_auto_keys(self):
        used = {it.key for it in self.items if it.key}
        for it in self.items:
            if it.key: continue
            for ch in it.label:
                if ch.isalpha() and ch.lower() not in used:
                    it.key = ch.lower()
                    used.add(it.key)
                    break

    @property
    def value(self) -> Any:
        return self.items[self.selected].value if self.items else None

    @property
    def item(self) -> Optional[ListItem]:
        return self.items[self.selected] if self.items else None

    def _label(self, i: int) -> str:
        glyph = self.glyph_on if i == self.selected else self.glyph_off
        return glyph + self.items[i].label

    def _compute_width(self) -> int:
        if not self.items: return 0
        labels = [self._label(i) for i in range(len(self.items))]
        if self.orientation == RadioGroup.Orientation.VERTICAL:
            return max(len(l) for l in labels)
        return sum(len(l) for l in labels) + self.gap * (len(labels) - 1)

    def _compute_height(self) -> int:
        n = len(self.items)
        if self.orientation == RadioGroup.Orientation.VERTICAL:
            return max(0, n * (1 + self.gap) - self.gap)
        return 1

    def _format(self, term, i: int) -> str:
        item = self.items[i]
        text = self._label(i)
        if self.auto_key and item.key:
            idx = item.label.lower().find(item.key)
            if idx >= 0:
                offset = len(self.glyph_on)
                text = text[:offset + idx] + term.underline(text[offset + idx]) + text[offset + idx + 1:]
        if item.disabled:
            return term.bright_black(text)
        if self.is_focused and i == self.selected and self.highlight:
            style = getattr(term, self.highlight, None)
            if style: text = style(text)
        return text

    def draw(self, screen: Screen):
        if self.orientation == RadioGroup.Orientation.VERTICAL:
            for i in range(len(self.items)):
                screen.put(self.x, self.y + i * (1 + self.gap), self._format(screen.term, i))
        else:
            parts = [self._format(screen.term, i) for i in range(len(self.items))]
            screen.put(self.x, self.y, (' ' * self.gap).join(parts))

    def _move(self, delta: int):
        n = len(self.items)
        enabled = [i for i in range(n) if not self.items[i].disabled]
        if not enabled: return
        i = (self.selected + delta) % n
        while self.items[i].disabled: i = (i + delta) % n
        if i == self.selected: return
        self.selected = i
        if self.on_change: self.on_change(self.items[i])

    def _select(self, i: int):
        if i == self.selected or self.items[i].disabled: return
        self.selected = i
        if self.on_change: self.on_change(self.items[i])

    def handle_key(self, key):
        if key.is_sequence:
            if self.orientation == RadioGroup.Orientation.VERTICAL:
                if key.name == 'KEY_UP':   self._move(-1); return Widget.NO_EVENT
                if key.name == 'KEY_DOWN': self._move(+1); return Widget.NO_EVENT
            else:
                if key.name == 'KEY_LEFT':  self._move(-1); return Widget.NO_EVENT
                if key.name == 'KEY_RIGHT': self._move(+1); return Widget.NO_EVENT
            return Widget.BUBBLE

        for i, item in enumerate(self.items):
            if item.key and not item.disabled and key.lower() == item.key:
                self._select(i)
                return Widget.NO_EVENT
        return Widget.BUBBLE
