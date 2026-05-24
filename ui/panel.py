from __future__ import annotations
from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, Callable, Optional, Self
from .widgets.widget import Widget
from errors import WidgetNotFoundError

if TYPE_CHECKING:
    from .screen import Screen


class Panel(Widget):
    class TitleStyle(Enum):
        BRACKET = '[ {} ]'     # [ Title ]
        FORK    = '┤ {} ├'     # ┤ Title ├   (box-drawing tee junctions)
        PLAIN   = ' {} '       #   Title
        TIGHT   = '{}'         # Title       (no padding)

    class Alignment(Enum):
        LEFT   = 'left'
        CENTER = 'center'
        RIGHT  = 'right'

    class BorderStyle(Enum):
        # (tl, tr, bl, br, h, v, tee_left, tee_right)
        # tees connect outer verticals to thin internal dividers (─)
        THIN     = ('┌', '┐', '└', '┘', '─', '│', '├', '┤')
        ROUNDED  = ('╭', '╮', '╰', '╯', '─', '│', '├', '┤')
        THICK    = ('┏', '┓', '┗', '┛', '━', '┃', '┠', '┨')

    class Anchor(Flag):
        LEFT     = auto()
        RIGHT    = auto()
        TOP      = auto()
        BOTTOM   = auto()
        CENTER_X = auto()
        CENTER_Y = auto()
        CENTER   = CENTER_X | CENTER_Y

    def __init__(
        self,
        x: int, y: int, w: int, h: int,
        title: str = '',
        title_style: TitleStyle = TitleStyle.BRACKET,
        default_alignment: Alignment = Alignment.LEFT,
        border: bool = True,
        border_style: BorderStyle = BorderStyle.THIN,
        header: bool = False,
        footer: bool = False,
        render: Optional[Callable[['Panel', 'Screen'], None]] = None,
    ):
        super().__init__(x, y, w, h)
        self.title_style = title_style
        self.default_alignment = default_alignment
        self.border = border
        self.border_style = border_style
        self.has_header = header
        self.has_footer = footer
        self.lines: list[str] = []
        self.header_text = ''
        self.footer_text = ''
        self._render = render

        self._slots: dict[Panel.Alignment, str] = {a: '' for a in Panel.Alignment} # requirement: dict comprehension
        if title: self._slots[default_alignment] = title

        # inner content area
        pad = 1 if border else 0
        head = 2 if header else 0  # text row + divider row
        foot = 2 if footer else 0
        self.ix = x + pad
        self.iy = y + pad + head
        self.iw = w - 2 * pad
        self.ih = h - 2 * pad - head - foot

        self.widgets: dict[str, Widget] = {}
        self._focused: Optional[str] = None

    def add(self, name: str, widget: Widget, anchor: Optional[Anchor] = None) -> Widget:
        if anchor: self.align(widget, anchor)
        self.widgets[name] = widget
        widget.parent = self
        widget.alias = name
        if self._focused is None and widget.focusable: self.focus(name)
        return widget

    def _handle_focus_bubble(self, child_name: str):
        self.focus(child_name)
        if self.parent: self.parent._handle_focus_bubble(self.alias)

    def focus(self, name: Optional[str] = None) -> Self:
        if name is None: return super().focus()
        if name not in self.widgets: raise WidgetNotFoundError(name, list(self.widgets))
        if self._focused == name and self.widgets[name].is_focused: return self
        if self._focused and self._focused in self.widgets:
            self.widgets[self._focused].blur()
        self._focused = name
        if self.is_focused: self.widgets[name].focus()
        return self

    def on_focus(self):
        if self._focused: self.widgets[self._focused].focus()

    def on_blur(self):
        if self._focused: self.widgets[self._focused].blur()

    def _cycle_focus(self, reverse: bool = False, wrap: bool = False) -> bool:
        names = [n for n, w in self.widgets.items() if w.focusable]
        if not names: return False
        delta = -1 if reverse else +1
        if self._focused not in names:
            self.focus(names[-1 if reverse else 0])
            return True
        i = names.index(self._focused) + delta
        if 0 <= i < len(names):
            self.focus(names[i])
            return True
        if wrap:
            self.focus(names[i % len(names)])
            return True
        return False

    def center(self, widget: Widget) -> Widget:
        widget.move_to(
            self.ix + (self.iw - widget.w) // 2,
            self.iy + (self.ih - widget.h) // 2,
        )
        return widget

    def center_x(self, widget: Widget) -> Widget:
        widget.move_to(self.ix + (self.iw - widget.w) // 2, widget.y)
        return widget

    def center_y(self, widget: Widget) -> Widget:
        widget.move_to(widget.x, self.iy + (self.ih - widget.h) // 2)
        return widget

    def align(self, widget: Widget, anchor: Anchor) -> Widget:
        A = Panel.Anchor
        x, y = widget.x, widget.y
        if A.CENTER_X in anchor: x = self.ix + (self.iw - widget.w) // 2
        if A.CENTER_Y in anchor: y = self.iy + (self.ih - widget.h) // 2
        if A.LEFT     in anchor: x = self.ix
        if A.RIGHT    in anchor: x = self.ix + self.iw - widget.w
        if A.TOP      in anchor: y = self.iy
        if A.BOTTOM   in anchor: y = self.iy + self.ih - widget.h
        widget.move_to(x, y)
        return widget

    def move_to(self, x: int, y: int) -> Self:
        dx, dy = x - self.x, y - self.y
        super().move_to(x, y)
        self.ix += dx
        self.iy += dy
        for w in self.widgets.values(): w.move_to(w.x + dx, w.y + dy)
        return self

    def fit_to_content(self, pad_x: int = 1, pad_y: int = 1) -> Self:
        if not self.widgets: return self
        min_x = min(w.x for w in self.widgets.values())
        min_y = min(w.y for w in self.widgets.values())
        max_x = max(w.x + w.w for w in self.widgets.values())
        max_y = max(w.y + w.h for w in self.widgets.values())

        # inner area = content bounds + per-axis padding on each side
        self.ix = min_x - pad_x
        self.iy = min_y - pad_y
        self.iw = (max_x - min_x) + 2 * pad_x
        self.ih = (max_y - min_y) + 2 * pad_y

        bpad = 1 if self.border else 0
        head = 2 if self.has_header else 0
        foot = 2 if self.has_footer else 0
        self.x = self.ix - bpad
        self.y = self.iy - bpad - head
        self.w = self.iw + 2 * bpad
        self.h = self.ih + 2 * bpad + head + foot
        return self

    def handle_key(self, key):
        result = Widget.NO_EVENT
        if self._focused: result = self.widgets[self._focused].handle_key(key)

        if result is Widget.CYCLE_OUT_FWD or result is Widget.CYCLE_OUT_BWD:
            reverse = result is Widget.CYCLE_OUT_BWD
            if self._cycle_focus(reverse=reverse, wrap=False): return Widget.NO_EVENT
            return result

        if result is Widget.NO_EVENT and key.is_sequence and key.name in ('KEY_TAB', 'KEY_BTAB'):
            reverse = key.name == 'KEY_BTAB'
            if self._cycle_focus(reverse=reverse, wrap=False): return Widget.NO_EVENT
            return Widget.CYCLE_OUT_BWD if reverse else Widget.CYCLE_OUT_FWD

        return result

    def set_lines(self, lines: list[str]) -> Self:
        self.lines = lines
        return self

    def set_text(self, text: str) -> Self:
        self.lines = text.splitlines()
        return self

    def set_header(self, text: str) -> Self:
        self.header_text = text
        return self

    def set_footer(self, text: str) -> Self:
        self.footer_text = text
        return self

    def set_title(self, title: str, alignment: Optional[Alignment] = None) -> Self:
        self._slots[alignment or self.default_alignment] = title
        return self

    def clear_titles(self) -> Self:
        for a in Panel.Alignment:
            self._slots[a] = ''
        return self

    # ── drawing ──────────────────────────────────────────────────────────────
    def draw(self, screen: Screen):
        if self.border: self._draw_border(screen)
        if self.has_header: self._draw_header(screen)
        if self.has_footer: self._draw_footer(screen)
        if self._render: self._render(self, screen)
        else: self._draw_lines(screen)
        for w in self.widgets.values(): w.draw(screen)

    def _format_label(self, text: str) -> str:
        if not text: return ''
        return self.title_style.value.format(text)

    @property
    def _effective_border_style(self) -> BorderStyle:
        return Panel.BorderStyle.THICK if self.is_focused else self.border_style

    def _render_top_border(self) -> str:
        tl, tr, _, _, h, _, _, _ = self._effective_border_style.value
        line = [h] * self.iw

        def place(text: str, start: int):
            for i, ch in enumerate(text):
                pos = start + i
                if 0 <= pos < self.iw: line[pos] = ch

        left   = self._format_label(self._slots[Panel.Alignment.LEFT])
        center = self._format_label(self._slots[Panel.Alignment.CENTER])
        right  = self._format_label(self._slots[Panel.Alignment.RIGHT])

        OFFSET = 2
        place(left,   OFFSET)
        place(right,  self.iw - len(right) - OFFSET)
        place(center, (self.iw - len(center)) // 2)

        return tl + ''.join(line) + tr

    def _draw_border(self, screen: Screen):
        _, _, bl, br, h, v, _, _ = self._effective_border_style.value
        top = self._render_top_border()
        bot = bl + h * self.iw + br

        screen.put(self.x, self.y, top)
        for i in range(1, self.h - 1):
            screen.put(self.x, self.y + i, v + ' ' * self.iw + v)
        screen.put(self.x, self.y + self.h - 1, bot)

    def _draw_header(self, screen: Screen):
        *_, tee_l, tee_r = self._effective_border_style.value
        screen.put(self.x + 1, self.y + 1, self.header_text[:self.iw].ljust(self.iw))
        screen.put(self.x, self.y + 2, tee_l + '─' * self.iw + tee_r)

    def _draw_footer(self, screen: Screen):
        *_, tee_l, tee_r = self._effective_border_style.value
        screen.put(self.x, self.y + self.h - 3, tee_l + '─' * self.iw + tee_r)
        screen.put(self.x + 1, self.y + self.h - 2, self.footer_text[:self.iw].ljust(self.iw))

    def _draw_lines(self, screen: Screen):
        for i, line in enumerate(self.lines[:self.ih]):
            screen.put(self.ix, self.iy + i, line[:self.iw].ljust(self.iw))

    # ── helpers usable by custom render callbacks ────────────────────────────
    def put(self, screen: Screen, dx: int, dy: int, text: str):
        """Draw text at an offset INSIDE the panel (dx, dy from inner top-left)."""
        screen.put(self.ix + dx, self.iy + dy, text[:self.iw - dx])

    def put_centered(self, screen: Screen, dy: int, text: str):
        x = self.ix + (self.iw - len(text)) // 2
        screen.put(x, self.iy + dy, text)
