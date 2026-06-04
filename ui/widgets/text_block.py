from __future__ import annotations
import textwrap
from typing import TYPE_CHECKING, Optional, Self
from .widget import Widget
from ._scrollbar import draw_scrollbar
from errors import InvalidWidgetSizeError

if TYPE_CHECKING:
    from ..screen import Screen


class TextBlock(Widget):
    def __init__(
        self,
        text: str = '',
        x: int = 0, y: int = 0,
        w: int = 40,
        h: Optional[int] = None,
        color: Optional[str] = None,
        wrap: bool = False,
        show_scrollbar: bool = True,
    ):
        if w < (3 if show_scrollbar else 1):
            raise InvalidWidgetSizeError(w, h or 0, 'width too small for content')

        super().__init__(x, y, w=w, h=0)
        self.color = color
        self.wrap = wrap
        self.show_scrollbar = show_scrollbar
        self._h_param = h
        self._text = text
        self._lines: list[str] = []
        self.scroll = 0
        self._scrollable = False
        self._wrap_and_size()

    @property
    def focusable(self) -> bool:
        return self._scrollable

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self.scroll = 0
        self._wrap_and_size()

    def set_text(self, text: str) -> Self:
        self.text = text
        return self

    def set_width(self, w: int) -> Self:
        self.w = w
        self.scroll = 0
        self._wrap_and_size()
        return self

    def _wrap_and_size(self):
        text_w = max(1, self.w - 2 if self.show_scrollbar else self.w)
        wrapped: list[str] = []
        for para in self._text.split('\n'):
            if not para:
                wrapped.append('')
            else:
                chunks = textwrap.wrap(
                    para,
                    width=text_w,
                    break_long_words=True,
                    break_on_hyphens=False,
                    replace_whitespace=False,
                    drop_whitespace=True,
                )
                wrapped.extend(chunks or [''])
        self._lines = wrapped or ['']

        if self._h_param is None:
            self.h = max(1, len(self._lines))
            self._scrollable = False
        else:
            self.h = self._h_param
            self._scrollable = len(self._lines) > self.h

    def focus(self, snap: Optional[str] = None) -> Self:
        if self._scrollable:
            if snap == 'first': self.scroll = 0
            elif snap == 'last': self.scroll = max(0, len(self._lines) - self.h)
        return super().focus()

    def draw(self, screen: Screen):
        term = screen.term
        text_w = max(1, self.w - 2 if self.show_scrollbar else self.w)
        style = getattr(term, self.color, None) if self.color else None

        for row in range(self.h):
            idx = self.scroll + row
            screen.put(self.x, self.y + row, ' ' * text_w)
            if idx >= len(self._lines): continue
            line = self._lines[idx][:text_w].ljust(text_w)
            if style: line = style(line)
            screen.put(self.x, self.y + row, line)

        if self.show_scrollbar and self._scrollable:
            draw_scrollbar(screen, self.x + self.w - 1, self.y, self.h, len(self._lines), self.scroll, dim=not self.is_focused)

    def handle_key(self, key):
        if not self._scrollable: return Widget.BUBBLE
        if not key.is_sequence:   return Widget.BUBBLE

        if key.name == 'KEY_UP':     return self._scroll_by(-1)
        if key.name == 'KEY_DOWN':   return self._scroll_by(+1)
        if key.name == 'KEY_PGUP':   return self._scroll_by(-(self.h - 1))
        if key.name == 'KEY_PGDOWN': return self._scroll_by(+(self.h - 1))
        if key.name == 'KEY_HOME':   return self._scroll_to(0)
        if key.name == 'KEY_END':    return self._scroll_to(max(0, len(self._lines) - self.h))

        return Widget.BUBBLE

    def _scroll_by(self, delta: int):
        max_scroll = max(0, len(self._lines) - self.h)
        new = self.scroll + delta
        if new < 0:
            if self.wrap: new = max_scroll
            else: return Widget.BUBBLE
        elif new > max_scroll:
            if self.wrap: new = 0
            else: return Widget.BUBBLE
        if new == self.scroll: return Widget.BUBBLE
        self.scroll = new
        return Widget.NO_EVENT

    def _scroll_to(self, target: int):
        if target == self.scroll: return Widget.BUBBLE
        self.scroll = target
        return Widget.NO_EVENT
