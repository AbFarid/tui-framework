from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional
from .widgets.widget import Widget
from errors import PanelNotFoundError

if TYPE_CHECKING:
    from .screen import Screen
    from .panel import Panel

STATE_DIR = 'state'


class Scene:

    def __init__(self, screen: Screen):
        self.screen = screen
        self.panels: dict[str, Panel] = {}
        self._focused: Optional[str] = None
        self.commands: list[tuple[str, str, Any]] = []  # (key, label, action)

    def add(self, name: str, panel: Panel) -> Panel:
        self.panels[name] = panel
        panel.parent = self
        panel.alias = name
        if self._focused is None: self.focus(name)
        return panel

    def _handle_focus_bubble(self, panel_name: str):
        self.focus(panel_name)

    def tree(self):
        """Print the whole scene's panel/widget tree (debugging)."""
        for panel in self.panels.values():
            panel.tree()

    def _stateful(self):
        """Every widget in the tree that has state to persist, keyed by alias."""
        for panel in self.panels.values():
            for _, w in panel.walk():
                if w.alias and w.serialize() is not None:
                    yield w

    def _state_path(self, name: Optional[str] = None) -> str:
        name = name or type(self).__name__
        return os.path.join(STATE_DIR, f'{name}.json')

    def save(self, name: Optional[str] = None):
        path = self._state_path(name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {w.alias: w.serialize() for w in self._stateful()}  # requirement: serialization
        with open(path, 'w') as f: json.dump(data, f, indent=2)

    def load(self, name: Optional[str] = None, clear: bool = False):
        path = self._state_path(name)
        try:
            with open(path) as f:
                data = json.load(f)
        except FileNotFoundError: return
        for w in self._stateful():
            if w.alias in data:
                w.deserialize(data[w.alias])
        if clear: os.remove(path)

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
            if focusable: panel.focus_child(focusable[-1 if snap == 'last' else 0])
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

    def center_all(self, x: bool = True, y: bool = True) -> 'Scene':
        if not self.panels: return self
        min_x = min(p.x for p in self.panels.values())
        min_y = min(p.y for p in self.panels.values())
        max_x = max(p.x + p.w for p in self.panels.values())
        max_y = max(p.y + p.h for p in self.panels.values())
        dx = (self.screen.width  - (max_x - min_x)) // 2 - min_x if x else 0
        dy = (self.screen.height - (max_y - min_y)) // 2 - min_y if y else 0
        for p in self.panels.values():
            p.move_to(p.x + dx, p.y + dy)
        return self


    def add_command(self, key: str, label: str, action: Callable[[], Any]) -> 'Scene':
        self.commands.append((key, label, action))
        return self

    def get_command_hints(self, gap: int = 3) -> str:
        return (' ' * gap).join(f'[{k.upper()}] {label}' for k, label, _ in self.commands)

    def _run_command(self, key):
        if key.is_sequence: return None
        for k, _, action in self.commands:
            if key.lower() == k.lower():
                r = action()
                return r if r is not None else Widget.NO_EVENT
        return None

    def route_key(self, key):
        if not self._focused:
            hit = self._run_command(key)
            return hit if hit is not None else Widget.NO_EVENT
        result = self.panels[self._focused].handle_key(key)

        if result is Widget.CYCLE_OUT_FWD or result is Widget.CYCLE_OUT_BWD:
            reverse = result is Widget.CYCLE_OUT_BWD
            if self._cycle_panel(reverse=reverse, wrap=False): return Widget.NO_EVENT
            if self._cycle_panel(reverse=reverse, wrap=True):  return Widget.NO_EVENT
            self.panels[self._focused]._cycle_focus(reverse=reverse, wrap=True)
            return Widget.NO_EVENT

        if result is Widget.BUBBLE:
            hit = self._run_command(key)
            if hit is not None: return hit
            return Widget.NO_EVENT
        return result

    def _cycle_panel(self, reverse: bool = False, wrap: bool = False) -> bool:
        names = [n for n, p in self.panels.items() if p.focusable]
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
