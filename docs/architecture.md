# Architecture

The UI is a three-level tree. Each level owns the next.

```
Screen           ← terminal lifecycle, draw buffer, key reader
  │
  Scene          ← top of the UI tree; owns panels
    │
    Panel        ← composite widget; owns child widgets (and can own nested Panels)
      │
      Widget     ← leaves: Label, Button, List, Menu, TextInput, NumberInput
```

`Scene`, `Panel`, and every `Widget` share two things:
1. A position and size (`x, y, w, h`).
2. A `handle_key(key)` method that returns an `Event` sentinel (or some value).

`Panel` inherits from `Widget`, which is why a `Panel` can live inside another `Panel`. `Scene` is its own thing — it has the same focus/routing concepts but is not a `Widget`.

## Focus

Focus is tracked at every level:

| Level | Where focus lives |
|-------|-------------------|
| Scene | `Scene._focused: Optional[str]` — name of the currently focused panel |
| Panel | `Panel._focused: Optional[str]` — name of the currently focused child widget |
| Widget | `Widget.is_focused: bool` |

Setting focus cascades **down**: focusing a panel calls `focus()` on its currently focused widget. Blurring cascades down too. This means at any moment there is a single chain of focused widgets from Scene root down to one leaf.

### Programmatic focus (`request_focus`)

Any widget can call `self.request_focus()` to ask to be focused. This bubbles **up** the parent chain via `_handle_focus_bubble(child_name)`, hopping Panel → Panel → Scene, with each level setting itself focused on the way up. The result: focus is correctly set at every level, even when crossing panels.

Used heavily in `on_submit` callbacks — e.g. the name TextInput's submit handler calls `list_widget.request_focus()` to hand control to the list across the Tab boundary.

## Event protocol

`handle_key` returns one of these sentinels (defined on `Widget.Event`):

| Sentinel | Meaning |
|----------|---------|
| `NO_EVENT` | I consumed the key (or chose to ignore it). Don't do anything else with it. |
| `BUBBLE` | I didn't handle this key. Parent, please try. |
| `CANCELLED` | The user pressed Esc on me. Parent: treat as cancel. |
| `CYCLE_OUT_FWD` | I was on my last focusable element and the user pressed Tab. Parent: cycle to your next child. |
| `CYCLE_OUT_BWD` | Same but Shift-Tab. |

Anything that isn't a sentinel is treated as a **value** (an `Option.action()` result, a `TextInput.value`, a `ListItem`, a `Scene` to transition to). Values propagate up the chain until a `Scene.handle_key` reads them.

### Bubble-up rule

The architectural contract is: **a widget returns `BUBBLE` for keys it doesn't actually handle, and `NO_EVENT` only for keys it deliberately consumed.** This is what lets the parent decide whether to do something with the key.

Example: a focused `List` consumes ↑/↓ to move its selection → returns `NO_EVENT`. A focused `Button` doesn't care about ↑/↓ → returns `BUBBLE`. The parent `Panel` sees `BUBBLE` + ↑/↓ and cycles focus to the next sibling widget.

## How `Panel.handle_key` routes a key

Order of operations in [panel.py:179](../ui/panel.py#L179):

1. **Panel-scoped shortcut broadcast.** If the key is a plain character (`not key.is_sequence`), Panel scans its children for any with a matching `.key` attribute (currently only `Button`). If one matches and is enabled, fire its action. This happens **before** the focused widget gets the key — that's why `c` fires the Create button even when a `TextInput` is focused.
2. **Forward to focused child.** Call `self.widgets[self._focused].handle_key(key)`.
3. **`CYCLE_OUT_FWD` / `CYCLE_OUT_BWD`** from child → cycle to next sibling (no wrap). If at boundary, re-bubble the same `CYCLE_OUT_*` so the parent Panel (or Scene) gets to try.
4. **`BUBBLE` + ↑/↓** → cycle focus within panel **with wrap**. Returns `NO_EVENT` (never bubbles out of the panel for arrows).
5. **`BUBBLE` + Tab/Shift-Tab** → cycle focus within panel (no wrap). If at boundary, return `CYCLE_OUT_FWD`/`CYCLE_OUT_BWD` so the parent can hop scope.
6. Otherwise, return whatever the child returned (could be a `BUBBLE`, an event, or a value).

### `Scene.route_key`

[scene.py:56](../ui/scene.py#L56) is the entry point from `Scene.handle_key`. It:

1. Forwards to the focused panel.
2. On `CYCLE_OUT_*`: cycles the panel ring (no-wrap → wrap → in-panel wrap as a last resort).
3. Collapses any leftover `BUBBLE` to `NO_EVENT` (scene is top of chain; nothing further to try).
4. Returns the result.

Each concrete `Scene` subclass wraps `route_key` in its own `handle_key` to interpret values:
- `NO_EVENT` / `CANCELLED` → return `self` (stay).
- A `Scene` value → return it (transition).
- Custom values → up to the scene.

## Key intercept summary (cheat sheet)

| Key | Panel intercepts when... | Otherwise |
|-----|--------------------------|-----------|
| Plain char (e.g. `c`) | A child has matching `.key` (Button shortcut). Pre-empts focused. | Forwarded to focused. |
| ↑ / ↓ / ← / → | Focused child returned `BUBBLE`. Panel cycles focus with wrap (↑/← go backward, ↓/→ go forward). | Focused consumes. |
| Tab / Shift-Tab | Focused returned `BUBBLE`. Panel cycles no-wrap; bubbles out at boundary so the parent can hop. | Focused consumes (none currently do). |
| Enter | Never — always forwarded; whatever the child returns. | — |
| Esc | Never intercepted by Panel; widgets return `CANCELLED` for it. | — |

## Nested panels

A `Panel` can be added to another `Panel` (it's a `Widget`). Routing falls out for free:

- Outer Panel's broadcast pass scans its **direct** children. A nested Panel has no `.key` attribute → skipped. Outer then forwards to the nested Panel, which runs **its own** broadcast on its children.
- Outer Panel sees the nested Panel's return value (which will itself be the result of nested routing, possibly `BUBBLE`).
- Arrow cycling: outer only cycles ↑/↓ if the nested Panel returned `BUBBLE` — but the nested Panel intercepts arrows for its own scope, so it almost always returns `NO_EVENT`. Outer leaves nested-panel arrow nav alone.

Consequence: if two nested Panels both bind `.key='c'`, the outer Panel's button wins (parent precedence). Currently accepted; revisit later.

## Drawing

Drawing is recursive and immediate:

- `Scene.draw()` iterates panels and calls `panel.draw(screen)`, then `screen.flush()`.
- `Panel.draw()` draws borders/header/footer/lines/`render`, then iterates child widgets calling `w.draw(screen)`.
- Widgets call `screen.put(x, y, text)` directly. `Screen` offsets writes by `(_ox, _oy)` to center the 120×40 canvas in the terminal.
- A widget that wants the system cursor calls `screen.request_cursor(x, y)` during its draw. `Screen.flush` honors the latest request once per frame and hides the cursor otherwise.

There is no double-buffer — Screen writes go straight to stdout. The full canvas is repainted each tick by re-drawing every panel.

## Lifecycle (from `main.py`)

```
Screen __enter__  ─→  enter fullscreen, hide cursor, compute canvas offsets
Scene = TitleScene(screen)
scene.enter()     ─→  Scene base clears the screen
loop:
  scene.update(dt)        ─→  optional per-frame logic; returns next scene or None
  scene.draw()
  key = screen.read_key(timeout=TICK)
  scene.handle_key(key)   ─→  returns next scene; None quits, self stays
Screen __exit__   ─→  exit fullscreen, restore cursor
```
