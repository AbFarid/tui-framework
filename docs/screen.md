# Screen

Source: [ui/screen.py](../ui/screen.py).

The terminal façade. Wraps a `blessed.Terminal`, manages the fullscreen lifecycle, and exposes the only legal API for drawing characters and reading keys. Everything above this layer (Scene, Panel, Widget) draws via `Screen.put(x, y, text)`.

## Canvas model

There is a **fixed logical canvas** of `120 × 40` cells (`CANVAS_W`, `CANVAS_H` in [screen.py:5-6](../ui/screen.py#L5-L6)). All `(x, y)` coordinates that scenes and widgets use are canvas-relative. `Screen` translates them to terminal coordinates by adding `_ox` / `_oy`, which are computed at `__enter__` time to center the canvas in the actual terminal window.

Consequence: widgets never need to know how big the terminal is. They lay out within `screen.width × screen.height` (always 120×40).

There is **no double-buffering**. `Screen.put` writes straight to stdout. The full canvas is re-drawn every tick by re-rendering every panel.

## Construction

```python
Screen()
```

No arguments. Use as a context manager:

```python
with Screen() as screen:
    ...
```

`__enter__` enters `cbreak` mode, switches to the alternate screen buffer, hides the cursor, and computes centering offsets. `__exit__` reverses all of that. Always use `with` — otherwise the terminal stays in an unusable state if anything raises.

## Attributes

| Attribute | Type | Meaning |
|-----------|------|---------|
| `term` | `blessed.Terminal` | The underlying blessed terminal. Widgets read text-attribute callables off it (e.g. `term.bold`, `term.bright_black`, `term.underline`). |
| `width` | `int` | Always `CANVAS_W` (120). |
| `height` | `int` | Always `CANVAS_H` (40). |
| `_ox`, `_oy` | `int` | Terminal-space offsets to center the canvas. Computed at `__enter__`. |
| `_cbreak` | context manager | The active blessed cbreak context. Internal. |
| `_cursor_at` | `Optional[tuple[int, int]]` | Cursor position requested for the next flush. Reset each frame. |

## Methods

### `put(x, y, text)`

Write `text` at canvas coordinates `(x, y)`. The text may contain ANSI escape sequences (from `term.bold(...)` etc.) — `Screen` does not interpret them.

Does **not** flush. Call `flush()` after all drawing for the frame.

### `request_cursor(x, y)`

Ask `Screen` to position the terminal's text cursor at `(x, y)` on the next `flush()`. Used by `TextInput` while focused.

Only the **last** request before `flush` wins. Reset to `None` after each flush — meaning a widget that wants the cursor must re-request it every frame (which they do, in their `draw` method).

### `flush()`

End-of-frame call. If a cursor position was requested this frame, move the terminal cursor there and make it visible. Otherwise hide the cursor. Then flush stdout.

Call once per frame after all `panel.draw(screen)` calls — `Scene.draw()` does this for you.

### `clear()`

Full terminal clear. Called by `Scene.enter()` on scene entry.

### `read_key(timeout=None, esc_delay=0.05)`

Blocks for up to `timeout` seconds and returns whatever `blessed.Terminal.inkey` returns. The result is a blessed `Keystroke` object:

- `key.is_sequence` — `True` for arrow keys, function keys, etc.
- `key.name` — e.g. `'KEY_UP'`, `'KEY_ENTER'`, `'KEY_ESCAPE'`, `'KEY_TAB'`, `'KEY_BTAB'`, `'KEY_BACKSPACE'`, `'KEY_F5'`.
- `key.isdigit()`, `key.isprintable()`, `str(key)` — character-style queries for non-sequence keys.

`esc_delay` is how long blessed waits to disambiguate a standalone Escape from the prefix of a sequence. 50 ms is responsive enough that Esc-to-cancel feels instant.

If the timeout elapses with no key pressed, returns a falsy `Keystroke` — `main.py` does `if not key: continue` to keep the frame loop going.
