# Scene

Source: [ui/scene.py](../ui/scene.py).

The top of the UI tree. A `Scene` owns a dict of `Panel`s, knows which one is focused, and routes keys down into the focused panel. `main.py` always has exactly one active scene.

## Construction

```python
Scene(screen: Screen)
```

You almost always subclass `Scene` rather than constructing it directly — the bare class has empty `update`, an empty `draw` loop, and a no-op `handle_key`. Concrete scenes are in [ui/scenes/](../ui/scenes/).

## Attributes

| Attribute | Type | Meaning |
|-----------|------|---------|
| `screen` | `Screen` | The terminal façade. Passed in at construction. |
| `panels` | `dict[str, Panel]` | All panels added via `add()`, keyed by user-given name. |
| `_focused` | `Optional[str]` | Name of the currently focused panel. |

## Methods

### `add(name, panel) -> Panel`

Register `panel` under `name`. Sets `panel.parent = self` and `panel.alias = name` (used by the focus-bubble path). Auto-focuses the first added panel. Returns the panel for chaining.

```python
main = self.add('main', Panel(0, 0, 60, 20, title='Hello'))
```

### `focus(name, snap=None) -> Scene`

Move scene focus to the panel registered as `name`. Cascades — blurs the previously focused panel, focuses the new one (which in turn focuses its child widget).

`snap`:
- `None` (default) — leave the new panel's internal focus alone.
- `'first'` — after focusing, jump the panel's internal focus to its first focusable widget.
- `'last'` — same but last.

Raises `PanelNotFoundError` if `name` isn't registered.

Returns `self` for chaining.

### `_handle_focus_bubble(panel_name)`

Internal. Called by a child Panel's `_handle_focus_bubble` when a widget deep in that panel calls `request_focus()`. The scene just delegates to `self.focus(panel_name)`.

### `center(panel) / center_x(panel) / center_y(panel) -> Panel`

Position helpers. Move `panel` so it's centered in the canvas (`(screen.width - panel.w) // 2`, etc.). Return the panel for chaining.

### `route_key(key)`

The standard key-routing implementation. Concrete scenes call this from their `handle_key`. Behavior:

1. If no focused panel, return `Widget.NO_EVENT`.
2. Forward to focused panel's `handle_key`.
3. On `CYCLE_OUT_FWD` / `CYCLE_OUT_BWD`: cycle the panel ring. Tries no-wrap first, then wrap. If the panel ring has only one panel, falls back to cycling within that panel with wrap.
4. Collapses `BUBBLE` to `NO_EVENT` (scene is top of chain).
5. Returns whatever the panel returned (a value, `CANCELLED`, `NO_EVENT`).

### `_cycle_panel(reverse=False, wrap=False) -> bool`

Move scene focus to the next/previous panel. Always snaps the new panel's internal focus to first/last (per direction). Returns `True` if focus moved.

### `enter()`

Called once when this scene becomes active. Base implementation just clears the screen. Override if you need to do setup on (re-)activation.

### `update(dt) -> Optional[Scene]`

Per-frame hook called before drawing. Default returns `None` (no transition). Override for timers, animations, or scripted scene transitions. Return value:
- `None` (or no return) — stay on this scene.
- another `Scene` — switch to it.

Note: `update` cannot quit the game (return `None` doesn't end the loop). Only `handle_key` can do that by returning `None`.

### `draw()`

Iterates `self.panels.values()` calling `panel.draw(screen)`, then `screen.flush()`. Subclasses typically don't override this — paint via panel rendering or panel `render` callbacks instead.

### `handle_key(key) -> Optional[Scene]`

Top-level key entry. Base returns `self` (stay). Subclasses must override and typically wrap `route_key`:

```python
def handle_key(self, key):
    result = self.route_key(key)
    if result is Widget.NO_EVENT: return self
    if result is Widget.CANCELLED: return TitleScene(self.screen)
    return GameScene(self.screen)  # or interpret `result` as needed
```

Return value:
- `self` — stay on this scene (most common).
- another `Scene` — transition; `main.py` will call `enter()` on it.
- `None` — quit the game.

## Composition rules

- One scene at a time. `main.py` swaps scenes; there is no scene stack (yet — see [todo.md](../todo.md)).
- Scenes hold strong references to their panels; transitioning to a new scene drops the old scene and its panels.
- Don't share `Panel` instances between scenes — focus state lives on the panel and would tangle.
