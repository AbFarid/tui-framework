import sys
from blessed import Terminal
from typing import Optional

import debug

CANVAS_W = 120
CANVAS_H = 40


class Screen:
    def __init__(self):
        self.term = Terminal()
        self._cbreak = None
        self.width = CANVAS_W
        self.height = CANVAS_H
        self._ox = 0
        self._oy = 0
        self._out = sys.stdout
        self._cursor_at: Optional[tuple[int, int]] = None

    def __enter__(self):
        self._out = debug.install()  # hijack sys.stdout for print()
        self._cbreak = self.term.cbreak()
        self._cbreak.__enter__()
        self._write(self.term.enter_fullscreen + self.term.hide_cursor)
        self._ox = max(0, (self.term.width  - CANVAS_W) // 2)
        self._oy = max(0, (self.term.height - CANVAS_H) // 2)
        return self

    def __exit__(self, *args):
        self._write(self.term.exit_fullscreen + self.term.normal_cursor)
        if self._cbreak: self._cbreak.__exit__(*args)
        debug.restore()

    def _write(self, text: str):
        self._out.write(text)
        self._out.flush()

    def request_cursor(self, x: int, y: int):
        """Show terminal cursor at (x, y) on the next flush. Resets each frame."""
        self._cursor_at = (x, y)

    def flush(self):
        if self._cursor_at is not None:
            x, y = self._cursor_at
            self._out.write(self.term.move(y + self._oy, x + self._ox) + self.term.normal_cursor)  # type: ignore[arg-type]
            self._cursor_at = None
        else:
            self._out.write(self.term.hide_cursor)
        self._out.flush()

    def clear(self): self._write(self.term.clear)

    def put(self, x: int, y: int, text: str):
        self._out.write(self.term.move(y + self._oy, x + self._ox) + text)  # type: ignore[arg-type]

    def read_key(self, timeout: Optional[float] = None, esc_delay: float = 0.05):
        return self.term.inkey(timeout=timeout, esc_delay=esc_delay)
