from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Optional
from .widgets.widget import Widget
from errors import PanelNotFoundError

if TYPE_CHECKING:
    from .screen import Screen
    from .panel import Panel


class Scene:

    def __init__(self, screen: Screen):
        self.screen = screen
        self.panels: dict[str, Panel] = {}
        self._focused: Optional[str] = None

    def add(self, name: str, panel: Panel) -> Panel:
        self.panels[name] = panel
        panel.parent = self
        panel.alias = name
        if self._focused is None: self.focus(name)
        return panel

    def _handle_focus_bubble(self, panel_name: str):
        self.focus(panel_name)

    def focus(self, name: str, snap: Optional[Literal['first', 'last']] = None) -> 'Scene':
        if name not in self.panels: raise PanelNotFoundError(name, list(self.panels))
        if self._focused == name and self.panels[name].is_focused and snap is None: return self
        if self._focused and self._focused in self.panels:
            self.panels[self._focused].blur()
        self._focused = name
        panel = self.panels[name]
        panel.focus()
        if snap is not None:
            focusable = [n for n, w in panel.widgets.items() if w.focusable]
            if focusable: panel.focus(focusable[-1 if snap == 'last' else 0])
        return self

    def center(self, panel: Panel) -> Panel:
        panel.move_to(
            (self.screen.width  - panel.w) // 2,
            (self.screen.height - panel.h) // 2,
        )
        return panel

    def center_x(self, panel: Panel) -> Panel:
        panel.move_to((self.screen.width - panel.w) // 2, panel.y)
        return panel

    def center_y(self, panel: Panel) -> Panel:
        panel.move_to(panel.x, (self.screen.height - panel.h) // 2)
        return panel

    def route_key(self, key):
        if not self._focused: return Widget.NO_EVENT
        result = self.panels[self._focused].handle_key(key)

        if result is Widget.CYCLE_OUT_FWD or result is Widget.CYCLE_OUT_BWD:
            reverse = result is Widget.CYCLE_OUT_BWD
            if self._cycle_panel(reverse=reverse, wrap=False): return Widget.NO_EVENT
            if self._cycle_panel(reverse=reverse, wrap=True):  return Widget.NO_EVENT
            self.panels[self._focused]._cycle_focus(reverse=reverse, wrap=True)
            return Widget.NO_EVENT

        return result

    def _cycle_panel(self, reverse: bool = False, wrap: bool = False) -> bool:
        names = list(self.panels)
        if not names: return False
        delta = -1 if reverse else +1
        snap: Literal['first', 'last'] = 'last' if reverse else 'first'
        if self._focused not in names:
            self.focus(names[-1 if reverse else 0], snap=snap)
            return True
        i = names.index(self._focused)
        n = i + delta
        if 0 <= n < len(names):
            self.focus(names[n], snap=snap)
            return True
        if wrap and (n % len(names)) != i:
            self.focus(names[n % len(names)], snap=snap)
            return True
        return False

    def enter(self):
        self.screen.clear()

    def update(self, dt: float) -> Optional['Scene']:
        """Per-frame logic (timers, animations). Return a new Scene to transition,
        or None / no return to stay. Cannot quit the game from here."""
        return None

    def draw(self):
        for p in self.panels.values(): p.draw(self.screen)
        self.screen.flush()

    def handle_key(self, key) -> Optional['Scene']:
        """React to a key. Return self to stay, another Scene to switch, None to quit.
        Default does nothing — subclass overrides, typically calling self.route_key()."""
        return self
