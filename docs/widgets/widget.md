# Widget (base)

Source: [ui/widgets/widget.py](../../ui/widgets/widget.py).

Abstract base class for everything that lives inside a `Panel`. Defines:
- Position + size attributes.
- Focus state and the bubble path to set focus from anywhere.
- The `Event` enum sentinels returned by `handle_key`.
- Position helpers that return `Self` so you can chain.

Every concrete widget (`Button`, `Label`, `List`, `Menu`, `NumberInput`, `TextInput`) extends `Widget`. `Panel` also extends `Widget`, which is why panels can be nested inside other panels.

## Nested: `Widget.Event`

The sentinel enum returned by `handle_key`. Each member is re-exported as a class attribute for ergonomic access (`Widget.NO_EVENT` etc.).

| Member | Meaning |
|--------|---------|
| `NO_EVENT` | I consumed (or deliberately ignored) the key. Parent: don't do anything else with it. |
| `BUBBLE` | I didn't handle this key. Parent: please try. |
| `CANCELLED` | The user pressed Esc on me. Parent: treat as cancel. |
| `CYCLE_OUT_FWD` | I'm at my last position and Tab was pressed. Parent: cycle me out forward. |
| `CYCLE_OUT_BWD` | Same but Shift-Tab. |

Anything not in this enum is treated as a **value** by the chain — it propagates upward until a `Scene.handle_key` reads it.

See [architecture.md](../architecture.md#event-protocol) for the full protocol.

## Properties

| Property | Default | Override when... |
|----------|---------|------------------|
| `focusable` | `True` | The widget should never receive focus (e.g. `Label` returns `False`), or focusability is dynamic (e.g. `Button` returns `not self.disabled`). |

`focusable` is a `@property` so subclasses can override with either a constant or a computed value uniformly.

## Instance attributes

| Attribute | Type | Meaning |
|-----------|------|---------|
| `x, y` | `int` | Top-left position in canvas coords. |
| `w, h` | `int` | Width/height in cells. Most widgets compute this in `__init__` from their content. |
| `is_focused` | `bool` | Whether this widget currently has focus. Set by `focus()` / `blur()`. |
| `parent` | `Optional[Any]` | The owning Panel (or Scene, for top-level Panels). Set by `Panel.add()` / `Scene.add()`. |
| `alias` | `Optional[str]` | The name this widget is registered under in its parent. Used by `request_focus` to tell the parent which child wants focus. |

## Construction

```python
Widget(x: int, y: int, w: int = 0, h: int = 0)
```

Subclasses call this in their `__init__` after computing their own `w` and `h` from content + style.

## Focus

### `focus() -> Self`

Set `is_focused = True` (idempotent) and call `on_focus()`. Returns `self` for chaining.

### `blur() -> Self`

Inverse of `focus()`. Calls `on_blur()`. Returns `self`.

### `on_focus()` / `on_blur()`

Hooks for subclasses. Base implementations are no-ops. `Panel` overrides these to cascade focus to its currently focused child.

### `request_focus()`

Ask to be focused. Bubbles up via `self.parent._handle_focus_bubble(self.alias)`. The Panel sets internal focus to this widget; that Panel's `_handle_focus_bubble` then bubbles to its parent (Scene or outer Panel), and so on. Result: focus chain is correct at every level.

Use this in callbacks when you want focus to move to a different widget (typically a different panel) than the one currently focused:

```python
TextInput(..., on_submit=lambda v: (
    setattr(other_input, 'value', v),
    other_input.request_focus(),
    Widget.NO_EVENT,
)[-1])
```

## Position helpers

All return `Self` so they chain.

### `move_to(x, y) -> Self`

Set absolute position. Panel overrides to also move children.

### `move_by(dx=0, dy=0) -> Self`

Relative move. Implemented as `self.move_to(self.x + dx, self.y + dy)` — subclasses that override `move_to` automatically get the cascade.

### Relative placement

| Method | Effect |
|--------|--------|
| `place_right_of(target, gap=0)` | Same Y as target, X = `target.x + target.w + gap`. |
| `place_left_of(target, gap=0)` | Same Y, X = `target.x - self.w - gap`. |
| `place_above(target, gap=0)` | Same X, Y = `target.y - self.h - gap`. |
| `place_below(target, gap=0)` | Same X, Y = `target.y + target.h + gap`. |

`target` is another widget. All compute via `self.move_to(...)`, so Panel's move cascade still works.

## Abstract methods

Subclasses must implement:

### `draw(screen: Screen) -> None`

Paint the widget. Use `screen.put(x, y, text)` for individual characters/strings. Style via `screen.term.<attr>(text)` — e.g. `screen.term.bold('Hi')`.

### `handle_key(key) -> Any`

React to a key. Return one of the `Event` sentinels, or a value (which propagates up the chain). See the architecture doc for the full contract.

**Rule of thumb**: `NO_EVENT` for keys you handled (or chose to ignore), `BUBBLE` for keys you didn't recognize. The Panel needs `BUBBLE` to know it can do its own thing (cycle focus, etc.).
