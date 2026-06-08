from __future__ import annotations
import re
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional
from .widget import Widget

if TYPE_CHECKING:
    from ..screen import Screen


class TextInput(Widget):
    class Style(Enum):
        NONE      = 'none'
        UNDERLINE = 'underline'
        BORDER    = 'border'

    def __init__(
        self,
        x: int, y: int,
        width: int,
        value: str = '',
        placeholder: str = '',
        max_length: Optional[int] = None,
        required: bool = False,
        label: Optional[str] = None,
        label_centered: bool = False,
        style: Style = Style.UNDERLINE,
        gap: int = 1,
        on_submit: Optional[Callable[[str], Any]] = None,
        rules: Optional[list[tuple[str, str]]] = None,
        validator: Optional[Callable[[str], Optional[str]]] = None,
    ):
        has_label    = label is not None
        is_border    = style == TextInput.Style.BORDER
        is_underline = style == TextInput.Style.UNDERLINE
        validates    = bool(rules or validator)

        field_total_w = width + (4 if is_border else 0)
        label_w       = len(label) if label else 0
        bbox_w        = max(field_total_w, label_w)
        bbox_h        = 1 + ((1 + gap) if has_label else 0) + (2 if is_border else 1 if is_underline else 0)
        bbox_h       += 1 if validates else 0

        super().__init__(x, y, w=bbox_w, h=bbox_h)

        self.field_width    = width
        self.value          = value
        self.placeholder    = placeholder
        self.max_length     = max_length
        self.required       = required
        self.label          = label
        self.label_centered = label_centered
        self.style          = style
        self.gap            = gap
        self.on_submit      = on_submit
        self.rules          = [(re.compile(p), msg) for p, msg in rules] if rules else []
        self.validator      = validator
        self.is_dirty       = False
        self._error: Optional[str] = None

        self._field_dx = 2 if is_border else 0
        self._field_dy = ((1 + gap) if has_label else 0) + (1 if is_border else 0)
        self._validates = validates
        self._error_dy  = bbox_h - 1

    def serialize(self): return self.value
    def deserialize(self, data): self.value = str(data)

    def _check(self) -> Optional[str]:
        """Validate the current value."""
        if not self.value: return None
        for pat, msg in self.rules:
            if pat.search(self.value): return msg
        if self.validator: return self.validator(self.value)
        return None

    def on_blur(self):
        self._error = self._check()

    def draw(self, screen: Screen):
        term = screen.term
        if self.label:
            indent = 1 if self.style == TextInput.Style.BORDER else 0
            lx = self.x + ((self.w - len(self.label)) // 2 if self.label_centered else indent)
            screen.put(lx, self.y, self.label)

        fx = self.x + self._field_dx
        fy = self.y + self._field_dy

        if self.style == TextInput.Style.BORDER:
            inner_w = self.field_width + 2
            screen.put(self.x, fy - 1, '┌' + '─' * inner_w + '┐')
            screen.put(self.x, fy,     '│ ' + ' ' * self.field_width + ' │')
            screen.put(self.x, fy + 1, '└' + '─' * inner_w + '┘')
        else:
            screen.put(fx, fy, ' ' * self.field_width)

        if self.value:
            screen.put(fx, fy, self.value[:self.field_width])
            cursor_x = fx + min(len(self.value), self.field_width - 1)
        else:
            if self.placeholder:
                screen.put(fx, fy, term.bright_black(self.placeholder[:self.field_width]))
            cursor_x = fx

        if self.style == TextInput.Style.UNDERLINE:
            line = '─' * self.field_width
            screen.put(fx, fy + 1, term.red(line) if self._error else line)

        if self._validates:
            screen.put(self.x, self.y + self._error_dy, ' ' * self.w)
            if self._error:
                screen.put(self.x, self.y + self._error_dy, term.red(self._error[:self.w]))

        if self.is_focused: screen.request_cursor(cursor_x, fy)

    def handle_key(self, key):
        if key.is_sequence:
            if key.name == 'KEY_ENTER':
                if not self.value and self.required: return TextInput.NO_EVENT
                err = self._check()
                if err:
                    self._error = err
                    return TextInput.NO_EVENT
                self._error = None
                if self.on_submit: return self.on_submit(self.value)
                return self.value
            if key.name == 'KEY_ESCAPE':
                if not self.required: return TextInput.CANCELLED
                return TextInput.NO_EVENT
            if key.name == 'KEY_BACKSPACE':
                if not self.is_dirty and self.value: self.value = ''
                else: self.value = self.value[:-1]
                self.is_dirty = True
                self._error = None
                return TextInput.NO_EVENT
            return TextInput.BUBBLE
        if key.isprintable():
            if self.max_length is None or len(self.value) < self.max_length:
                self.value += str(key)
                self.is_dirty = True
                self._error = None
            return TextInput.NO_EVENT
        return TextInput.BUBBLE
