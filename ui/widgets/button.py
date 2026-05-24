from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Optional
from .widget import Widget

if TYPE_CHECKING:
    from ..screen import Screen


class Button(Widget):
    def __init__(
        self,
        label: str,
        x: int = 0, y: int = 0,
        key: Optional[str] = None,
        action: Optional[Callable[[], Any]] = None,
        disabled: bool = False,
        highlight: Optional[str] = 'reverse',
    ):
        super().__init__(x, y, w=len(label) + 4, h=1)
        self.label = label
        self.key = key.lower() if key else None
        self.action = action
        self.disabled = disabled
        self.highlight = highlight

    @property
    def focusable(self) -> bool:
        return not self.disabled

    def draw(self, screen: Screen):
        term = screen.term
        label = self.label
        if self.key:
            idx = label.lower().find(self.key)
            if idx >= 0:
                label = label[:idx] + term.underline(label[idx]) + label[idx+1:]
        text = f'[ {label} ]'
        if self.disabled:
            text = term.bright_black(text)
        elif self.is_focused and self.highlight:
            style = getattr(term, self.highlight, None)
            if style: text = style(text)
        screen.put(self.x, self.y, text)

    def handle_key(self, key):
        if self.disabled: return Widget.NO_EVENT
        if key.is_sequence:
            if key.name == 'KEY_ENTER' and self.action: return self.action()
        elif self.key and key.lower() == self.key:
            if self.action: return self.action()
        return Widget.NO_EVENT
