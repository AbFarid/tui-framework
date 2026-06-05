from __future__ import annotations
from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, Callable, Optional, Self
from .widgets.widget import Widget
from errors import WidgetNotFoundError, InvalidWidgetSizeError
from debug import traced

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

    class Orientation(Enum):
        VERTICAL   = 'vertical'
        HORIZONTAL = 'horizontal'

    _SEP_GLYPHS = {
        (0, 1, 0, 1): '─', (1, 0, 1, 0): '│',
        (1, 1, 1, 0): '├', (1, 0, 1, 1): '┤', (0, 1, 1, 1): '┬', (1, 1, 0, 1): '┴',
        (1, 1, 1, 1): '┼',
        (0, 2, 1, 2): '┯', (1, 2, 0, 2): '┷', (2, 1, 2, 0): '┠', (2, 0, 2, 1): '┨',
    }

    PAD_Y = 1
    PAD_X = 3

    def __init__(
        self,
        x: int = 0, y: int = 0, w: int = 2, h: int = 2,
        title: str = '',
        title_style: TitleStyle = TitleStyle.BRACKET,
        default_alignment: Alignment = Alignment.LEFT,
        border: bool = True,
        border_style: BorderStyle = BorderStyle.THIN,
        header: bool = False,
        footer: bool = False,
        pad_x: Optional[int] = None,  # None → 2 if bordered, else 0
        pad_y: Optional[int] = None,  # None → 1 if bordered, else 0
        # pad_t: int = 1,
        # pad_b: int = 1,
        # pad_l: int = 2,
        # pad_r: int = 2,
        render: Optional[Callable[['Panel', 'Screen'], None]] = None,
    ):
        if title: # case if panel too small for the title
            bpad   = 1 if border else 0
            offset = 0 if default_alignment == Panel.Alignment.CENTER else 2
            min_w  = 2 * bpad + offset + len(title_style.value.format(title))
            if w < min_w: w = min_w
                # raise InvalidWidgetSizeError(w, h, f'title {title!r} needs w ≥ {min_w}')

        super().__init__(x, y, w, h)
        self.title_style = title_style
        self.default_alignment = default_alignment
        self.border = border
        self.border_style = border_style
        self.has_header = header
        self.has_footer = footer
        self.pad_x = pad_x if pad_x is not None else (Panel.PAD_X if border else 0)
        self.pad_y = pad_y if pad_y is not None else (Panel.PAD_Y if border else 0)
        self.lines: list[str] = []
        self.header_text = ''
        self.footer_text = ''
        self._render = render

        # title slots
        self._slots: dict[Panel.Alignment, str] = {a: '' for a in Panel.Alignment} # requirement: dict comprehension
        if title: self._slots[default_alignment] = title

        # inner content area (inside border + header/footer rows)
        head = header * 2
        foot = footer * 2
        self.ix = x + border
        self.iy = y + border + head
        self.iw = w - 2 * border
        self.ih = h - 2 * border - head - foot

        self.widgets: dict[str, Widget] = {}
        self._focused: Optional[str] = None
        self._separators: list[tuple] = []

    # layout rectangle: inner content area minus padding. used by alignment helpers
    @property
    def lx(self) -> int: return self.ix + self.pad_x
    @property
    def ly(self) -> int: return self.iy + self.pad_y
    @property
    def lw(self) -> int: return self.iw - 2 * self.pad_x
    @property
    def lh(self) -> int: return self.ih - 2 * self.pad_y

    @property
    def focusable(self) -> bool:
        return any(w.focusable for w in self.widgets.values()) # requirement: generator expression

    def walk(self, depth: int = 0): # requirement: generator function
        """Depth-first iterator over descendants, yielding (depth, widget)."""
        for w in self.widgets.values():
            yield depth, w
            if isinstance(w, Panel):
                yield from w.walk(depth + 1)

    def tree(self):
        """Print an indented tree of this panel and its descendants (debugging)."""
        print(f'{self.alias}: {type(self).__name__} {self.w}x{self.h}')
        for depth, w in self.walk():
            print('  ' * (depth + 1) + f'{w.alias}: {type(w).__name__} {w.w}x{w.h}')

    def add(self, name: str, widget: Widget, anchor: Optional[Anchor] = None) -> Widget:
        if anchor: self.align(widget, anchor)
        self.widgets[name] = widget
        widget.parent = self
        widget.alias = name
        if self._focused is None and widget.focusable: self.focus_child(name)
        return widget

    def _handle_focus_bubble(self, child_name: str):
        self.focus_child(child_name)
        if self.parent: self.parent._handle_focus_bubble(self.alias)

    def focus(self, snap: Optional[str] = None) -> Self:
        super().focus()
        # entering a panel via snap should land on its first/last focusable child
        if snap is not None:
            names = [n for n, w in self.widgets.items() if w.focusable]
            if names: self.focus_child(names[-1 if snap == 'last' else 0], snap=snap)
        return self

    @traced
    def focus_child(self, name: str, snap: Optional[str] = None) -> Self:
        if name not in self.widgets: raise WidgetNotFoundError(name, list(self.widgets))
        if self._focused == name and self.widgets[name].is_focused and snap is None: return self
        if self._focused and self._focused in self.widgets:
            self.widgets[self._focused].blur()
        self._focused = name
        if self.is_focused: self.widgets[name].focus(snap)
        return self

    def on_focus(self):
        if self._focused: self.widgets[self._focused].focus()

    def on_blur(self):
        if self._focused: self.widgets[self._focused].blur()

    def _cycle_focus(self, reverse: bool = False, wrap: bool = False, snap: Optional[str] = None) -> bool:
        names = [n for n, w in self.widgets.items() if w.focusable]
        if not names: return False
        delta = -1 if reverse else +1

        # Tab cycling doesn't snap and leaves leaf widgets on their existing selection.
        def land(name: str):
            s = snap
            if s is None and isinstance(self.widgets[name], Panel):
                s = 'last' if reverse else 'first'
            self.focus_child(name, snap=s)

        if self._focused not in names:
            land(names[-1 if reverse else 0])
            return True
        i = names.index(self._focused) + delta
        if 0 <= i < len(names):
            land(names[i])
            return True
        if wrap and len(names) > 1:
            land(names[i % len(names)])
            return True
        return False

    def center(self, widget: Widget) -> Widget:
        widget.move_to(
            self.lx + (self.lw - widget.w) // 2,
            self.ly + (self.lh - widget.h) // 2,
        )
        return widget

    def center_x(self, widget: Widget) -> Widget:
        widget.move_to(self.lx + (self.lw - widget.w) // 2, widget.y)
        return widget

    def center_y(self, widget: Widget) -> Widget:
        widget.move_to(widget.x, self.ly + (self.lh - widget.h) // 2)
        return widget

    def align(self, widget: Widget, anchor: Anchor) -> Widget:
        A = Panel.Anchor
        x, y = widget.x, widget.y
        if A.CENTER_X in anchor: x = self.lx + (self.lw - widget.w) // 2
        if A.CENTER_Y in anchor: y = self.ly + (self.lh - widget.h) // 2
        if A.LEFT     in anchor: x = self.lx
        if A.RIGHT    in anchor: x = self.lx + self.lw - widget.w
        if A.TOP      in anchor: y = self.ly
        if A.BOTTOM   in anchor: y = self.ly + self.lh - widget.h
        widget.move_to(x, y)
        return widget

    def move_to(self, x: int, y: int) -> Self:
        dx, dy = x - self.x, y - self.y
        super().move_to(x, y)
        self.ix += dx
        self.iy += dy
        for w in self.widgets.values(): w.move_to(w.x + dx, w.y + dy)
        return self

    def fit_to_content(self) -> Self:
        if not self.widgets: return self
        min_x = min(w.x for w in self.widgets.values())
        min_y = min(w.y for w in self.widgets.values())
        max_x = max(w.x + w.w for w in self.widgets.values())
        max_y = max(w.y + w.h for w in self.widgets.values())

        self.ix = min_x - self.pad_x
        self.iy = min_y - self.pad_y
        self.iw = (max_x - min_x) + 2 * self.pad_x
        self.ih = (max_y - min_y) + 2 * self.pad_y

        border = self.border
        head = self.has_header * 2
        foot = self.has_footer * 2
        self.x = self.ix - border
        self.y = self.iy - border - head
        self.w = self.iw + 2 * border
        self.h = self.ih + 2 * border + head + foot
        return self

    def handle_key(self, key):
        # Panel-scoped shortcut
        if not key.is_sequence:
            ch = key.lower()
            for w in self.widgets.values():
                if getattr(w, 'key', None) == ch and not getattr(w, 'disabled', False):
                    action = getattr(w, 'action', None)
                    if action: return action()
                    return Widget.NO_EVENT

        if not self._focused: return Widget.BUBBLE
        result = self.widgets[self._focused].handle_key(key)

        if result is Widget.CYCLE_OUT_FWD or result is Widget.CYCLE_OUT_BWD:
            reverse = result is Widget.CYCLE_OUT_BWD
            if self._cycle_focus(reverse=reverse, wrap=False): return Widget.NO_EVENT
            return result

        if result is Widget.BUBBLE and key.is_sequence:
            if key.name in ('KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT'):
                reverse = key.name in ('KEY_UP', 'KEY_LEFT')
                self._cycle_focus(reverse=reverse, wrap=True, snap='last' if reverse else 'first')
                return Widget.NO_EVENT
            if key.name in ('KEY_TAB', 'KEY_BTAB'):
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

    # ── separators ───────────────────────────────────────────────────────────
    def separator(self, x: int, y: int, orientation: Orientation, penetrate: bool = False) -> Self:
        self._separators.append((orientation, x - self.x, y - self.y, penetrate))
        return self

    def separate(self, a: Widget, b: Widget, penetrate: bool = False) -> Self:
        if a.y + a.h <= b.y or b.y + b.h <= a.y: # stacked
            top, bot = (a, b) if a.y < b.y else (b, a)
            gap  = (top.y + top.h + bot.y) // 2
            seed = max(top.x, bot.x) + 1
            return self.separator(seed, gap, Panel.Orientation.HORIZONTAL, penetrate)
        if a.x + a.w <= b.x or b.x + b.w <= a.x: # side by side
            left, right = (a, b) if a.x < b.x else (b, a)
            gap  = (left.x + left.w + right.x) // 2
            seed = max(left.y, right.y) + 1
            return self.separator(gap, seed, Panel.Orientation.VERTICAL, penetrate)
        raise InvalidWidgetSizeError(0, 0, 'cannot separate overlapping widgets')

    # ── drawing ──────────────────────────────────────────────────────────────
    def draw(self, screen: Screen):
        if self.border: self._draw_border(screen)
        if self.has_header: self._draw_header(screen)
        if self.has_footer: self._draw_footer(screen)
        if self._render: self._render(self, screen)
        else: self._draw_lines(screen)
        for w in self.widgets.values(): w.draw(screen)
        if self._separators: self._draw_separators(screen)

    def _draw_separators(self, screen: Screen):
        H, W = self.h, self.w
        heavy = self._effective_border_style is Panel.BorderStyle.THICK
        bw = 2 if heavy else 1
        head_row = 2 if self.has_header else None
        foot_row = H - 3 if self.has_footer else None

        def frame_at(x: int, y: int) -> Optional[dict]:
            if self.border:
                if y == 0 or y == H - 1:  return {'N': 0, 'E': bw, 'S': 0, 'W': bw}
                if x == 0 or x == W - 1:  return {'N': bw, 'E': 0, 'S': bw, 'W': 0}
            if y == head_row or y == foot_row: return {'N': 0, 'E': 1, 'S': 0, 'W': 1}
            return None

        cells: dict[tuple[int, int], dict] = {}

        def add(cx: int, cy: int, **dirs):
            c = cells.setdefault((cx, cy), {'N': 0, 'E': 0, 'S': 0, 'W': 0})
            for k, v in dirs.items(): c[k] = max(c[k], v)

        for orientation, rx, ry, penetrate in self._separators:
            vertical = orientation is Panel.Orientation.VERTICAL
            add(rx, ry, **({'N': 1, 'S': 1} if vertical else {'E': 1, 'W': 1}))

            for step, trail_dir in ((-1, 'S' if vertical else 'E'), (+1, 'N' if vertical else 'W')):
                x, y = rx, ry
                while True:
                    nx, ny = (x, y + step) if vertical else (x + step, y)
                    if not (0 <= nx < W and 0 <= ny < H): break # ran off the panel
                    hit_frame = frame_at(nx, ny)
                    if hit_frame is not None: # hit the frame -> junction
                        add(nx, ny, **hit_frame); add(nx, ny, **{trail_dir: 1}); break
                    if (nx, ny) in cells and not penetrate: # hit another separator -> junction
                        add(nx, ny, **{trail_dir: 1}); break
                    add(nx, ny, **({'N': 1, 'S': 1} if vertical else {'E': 1, 'W': 1}))
                    x, y = nx, ny

        for (cx, cy), bit in cells.items():
            glyph = Panel._SEP_GLYPHS.get((bit['N'], bit['E'], bit['S'], bit['W']), '┼')
            screen.put(self.x + cx, self.y + cy, glyph)

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
