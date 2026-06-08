from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional
from .widget import Widget

if TYPE_CHECKING:
    from ..screen import Screen


@dataclass
class Option:
    label: str
    action: Callable = field(default_factory=lambda: lambda: None) # requirement: lambda
    disabled: bool = False
    key: Optional[str] = None

    def __post_init__(self):
        if self.key: self.key = self.key.lower()


class Menu(Widget):
    class Orientation(Enum):
        VERTICAL   = 'vertical'
        HORIZONTAL = 'horizontal'

    class NumberStyle(Enum):
        DOT     = '{n}. {label}'    # 1.
        PAREN   = '{n}) {label}'    # 1)
        BRACKET = '[{n}] {label}'   # [1]

    def __init__(
        self,
        x: int, y: int,
        options: list[Option],
        w: Optional[int] = None,  # None = auto-fit to widest rendered label
        orientation: Orientation = Orientation.VERTICAL,
        number_style: Optional[NumberStyle] = None,
        required: bool = False,
        highlight: Optional[str] = 'bold',  # blessed attr (e.g. 'bold', 'cyan', 'bold_yellow') or None
        cursor: str = '❯ ',
        gap: int = 0,
        auto_key: bool = False,  # render as [N]ew Game
    ):
        super().__init__(x, y)
        self.options = options
        self.orientation = orientation
        self.number_style = number_style
        self.required = required
        self.highlight = highlight
        self.cursor = cursor
        self.gap = gap
        self.auto_key = auto_key
        self.selected = 0
        if auto_key: self._assign_auto_keys()
        if self.options[0].disabled: self._move(+1)

        self.w = w if w is not None else self._compute_width()
        self.h = self._compute_height()

    def _compute_width(self) -> int:
        cursor_len = len(self.cursor)
        if self.orientation == Menu.Orientation.VERTICAL:
            return cursor_len + max(len(self._label(i)) for i in range(len(self.options)))
        per_option = [cursor_len + len(self._label(i)) for i in range(len(self.options))]
        return sum(per_option) + self.gap * (len(per_option) - 1)

    def _compute_height(self) -> int:
        if self.orientation == Menu.Orientation.VERTICAL:
            n = len(self.options)
            return n * (1 + self.gap) - self.gap
        return 1

    def _assign_auto_keys(self):
        used = {opt.key for opt in self.options if opt.key}  # requirement: set comprehension
        for opt in self.options:
            if opt.key: continue
            for ch in opt.label:
                if ch.isalpha() and ch.lower() not in used:
                    opt.key = ch.lower()
                    used.add(opt.key)
                    break

    def _label(self, i: int) -> str:
        opt = self.options[i]
        if self.number_style is None: return opt.label
        prefix = opt.key.upper() if opt.key else str(i + 1)
        return self.number_style.value.format(n=prefix, label=opt.label)

    def _prefix(self, i: int) -> str:
        return self.cursor if i == self.selected else ' ' * len(self.cursor)

    def _format(self, term, i: int) -> str:
        opt = self.options[i]
        label = self._label(i)
        if self.auto_key and opt.key:
            idx = label.lower().find(opt.key)
            if idx >= 0:
                label = label[:idx] + term.underline(label[idx]) + label[idx+1:]
        text = self._prefix(i) + label
        if self.options[i].disabled:
            return term.bright_black(text)
        if i == self.selected and self.highlight:
            style = getattr(term, self.highlight, None)
            if style: text = style(text)
        return text

    def draw(self, screen: Screen):
        if self.orientation == Menu.Orientation.VERTICAL:
            for i in range(len(self.options)):
                screen.put(self.x, self.y + i * (1 + self.gap), self._format(screen.term, i))
        else:  # HORIZONTAL
            parts = [self._format(screen.term, i) for i in range(len(self.options))]
            screen.put(self.x, self.y, (' ' * self.gap).join(parts))

    def _move(self, delta: int):
        n = len(self.options)
        enabled = [i for i in range(n) if not self.options[i].disabled] # requirement: list comprehension
        if not enabled: return
        
        i = (self.selected + delta) % n
        while self.options[i].disabled: i = (i + delta) % n
        self.selected = i

    def handle_key(self, key):
        if key.is_sequence:
            if self.orientation == Menu.Orientation.VERTICAL:
                if key.name == 'KEY_UP':   self._move(-1); return Menu.NO_EVENT
                if key.name == 'KEY_DOWN': self._move(+1); return Menu.NO_EVENT
            else:
                if key.name == 'KEY_LEFT':  self._move(-1); return Menu.NO_EVENT
                if key.name == 'KEY_RIGHT': self._move(+1); return Menu.NO_EVENT

            if key.name == 'KEY_ENTER' and not self.options[self.selected].disabled:
                return self.options[self.selected].action()

            if key.name == 'KEY_ESCAPE' and not self.required: return Menu.CANCELLED

            return Menu.BUBBLE

        for opt in self.options:
            if opt.key and not opt.disabled and key.lower() == opt.key:
                return opt.action()

        if self.number_style is not None and key.isdigit():
            n = int(key) - 1
            if 0 <= n < len(self.options) and not self.options[n].disabled and not self.options[n].key:
                return self.options[n].action()

        return Menu.BUBBLE
