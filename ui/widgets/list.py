from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Self, Union
from .widget import Widget
from errors import InvalidWidgetSizeError

if TYPE_CHECKING:
    from ..screen import Screen


@dataclass
class ListItem:
    label: str
    value: Any = None
    id: Optional[str] = None
    color: Optional[str] = None # blessed attr for non-selected rendering
    disabled: bool = False


class List(Widget):
    def __init__(
        self,
        x: int, y: int,
        w: int, h: int,
        items: Optional[list[Union[str, ListItem]]] = None,
        selectable: bool = False,
        required: bool = False,
        wrap: bool = True,
        highlight: Optional[str] = 'reverse',
        highlight_unfocused: Optional[str] = 'on_bright_black',
        show_scrollbar: bool = True,
    ):
        if show_scrollbar:
            if h < 4: raise InvalidWidgetSizeError(w, h, 'scrollbar needs h ≥ 4 (2 tips + 2 thumb positions)')
            if w < 2: raise InvalidWidgetSizeError(w, h, 'scrollbar reserves the rightmost column, so w ≥ 2')
        elif w < 1 or h < 1:
            raise InvalidWidgetSizeError(w, h, 'must be at least 1×1')

        super().__init__(x, y, w=w, h=h)
        self.items: list[ListItem] = [self._wrap_item(it) for it in (items or [])]
        self.selectable = selectable
        self.required = required
        self.wrap = wrap
        self.highlight = highlight
        self.highlight_unfocused = highlight_unfocused
        self.show_scrollbar = show_scrollbar
        self.selected = 0
        self.scroll   = 0

        if selectable and self.items and self.items[0].disabled: self._move(+1)

    @staticmethod
    def _wrap_item(it: Union[str, ListItem]) -> ListItem:
        return it if isinstance(it, ListItem) else ListItem(label=it)

    # ── mutation ────────────────────────────────────────────────────────────
    def set_items(self, items: list[Union[str, ListItem]]) -> Self:
        self.items = [self._wrap_item(it) for it in items]
        self.selected = 0
        self.scroll   = 0
        return self

    def append(self, item: Union[str, ListItem]) -> Self:
        self.items.append(self._wrap_item(item))
        return self

    def remove(self, index: int) -> Self:
        del self.items[index]
        n = len(self.items)
        if n == 0:
            self.selected = 0
            self.scroll   = 0
        else:
            self.selected = min(self.selected, n - 1)
            self.scroll   = min(self.scroll, max(0, n - self.h))
        return self

    def clear(self) -> Self:
        self.items = []
        self.selected = 0
        self.scroll   = 0
        return self

    def _move(self, delta: int):
        n = len(self.items)
        if not n: return
        enabled = [i for i in range(n) if not self.items[i].disabled]
        if not enabled: return

        i = self.selected + delta
        for _ in range(n):
            if self.wrap: i %= n
            elif i < 0 or i >= n: return
            if not self.items[i].disabled:
                self.selected = i
                self._scroll_to_selected()
                return
            i += delta

    def _scroll_to_selected(self):
        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + self.h:
            self.scroll = self.selected - self.h + 1

    def draw(self, screen: Screen):
        content_w = self.w - 1 if self.show_scrollbar else self.w
        term = screen.term

        for row in range(self.h):
            idx = self.scroll + row
            screen.put(self.x, self.y + row, ' ' * content_w)  # clear row
            if idx >= len(self.items): continue
            item = self.items[idx]
            text = item.label[:content_w].ljust(content_w)
            if item.disabled:
                text = term.bright_black(text)
            elif item.color:
                style = getattr(term, item.color, None)
                if style: text = style(text)
            if self.selectable and idx == self.selected:
                style_name = self.highlight if self.is_focused else self.highlight_unfocused
                if style_name:
                    style = getattr(term, style_name, None)
                    if style: text = style(text)
            screen.put(self.x, self.y + row, text)

        if self.show_scrollbar: self._draw_scrollbar(screen)

    def _draw_scrollbar(self, screen: Screen):
        bar_x = self.x + self.w - 1
        n = len(self.items)

        # scrollbar track
        screen.put(bar_x, self.y,              '╿')
        screen.put(bar_x, self.y + self.h - 1, '╽')
        for i in range(1, self.h - 1):
            screen.put(bar_x, self.y + i, '│')

        # scrollbar thumb
        if n <= self.h: return
        thumb_size = max(1, self.h * self.h // n)
        thumb_max  = self.h - thumb_size
        thumb_pos  = (self.scroll * thumb_max) // (n - self.h)
        for i in range(thumb_pos, thumb_pos + thumb_size):
            screen.put(bar_x, self.y + i, '┃')

    def handle_key(self, key):
        if not self.selectable: return Widget.NO_EVENT

        if key.is_sequence:
            if key.name == 'KEY_UP':   self._move(-1)
            if key.name == 'KEY_DOWN': self._move(+1)

            if key.name == 'KEY_ENTER' and self.items and not self.items[self.selected].disabled:
                return self.items[self.selected]

            if key.name == 'KEY_ESCAPE' and not self.required: return Widget.CANCELLED

        return Widget.NO_EVENT
