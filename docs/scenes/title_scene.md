# TitleScene

Source: [ui/scenes/title_scene.py](../../ui/scenes/title_scene.py).

The entry scene shown when the game starts. Renders the "Punch Quest" ASCII art via a custom `render` callback and a 3-option `Menu` (`New Game`, `Continue`, `Quit`).

## Layout

A single full-screen Panel (`screen.width × screen.height`) with `BorderStyle.ROUNDED`. The Panel uses a `render` callback (`_render`) rather than the default lines-based body:

- ASCII title art centered horizontally, with vertical offset 4 rows above center.
- `[F5] Restart` hint centered on the bottom inner row.
- The `Menu` is added as a child widget, positioned 14 rows from the inner bottom.

The Menu uses `auto_key=True`, so `N`, `C`, `Q` are auto-assigned as letter shortcuts and rendered underlined in their labels.

## Menu options

```python
options = [
    Option('New Game', action=lambda: NameScene(screen)),
    Option('Continue', disabled=True),
    Option('Quit',     action=lambda: None),
]
```

| Option | Action |
|--------|--------|
| `New Game` | Returns a fresh `NameScene` — propagates up to `handle_key`, becomes the next scene. |
| `Continue` | `disabled=True` (save/load isn't implemented). Skipped by cursor movement and shortcut. |
| `Quit` | Returns `None` — `main.py` interprets a `None` return from `handle_key` as "quit the game". |

`required=True` on the Menu means Esc doesn't cancel — you have to pick.

## `_render(panel, screen)`

Custom body painter passed via the `render` parameter. Splits `TITLE_ART` on newlines, computes centering offsets, and uses `panel.put()` and `panel.put_centered()` to paint the art and the F5 hint.

## `handle_key(key) -> Optional[Scene]`

```python
def handle_key(self, key):
    result = self.route_key(key)
    if result is Widget.NO_EVENT or result is Widget.CANCELLED: return self
    return result
```

- `NO_EVENT` / `CANCELLED` → stay (`return self`).
- Anything else (a `Scene` from `New Game`, or `None` from `Quit`) → return it. `main.py` does the actual transition or quit.

## Notable details

- The `NameScene` import is deferred inside `__init__` to avoid a circular import (NameScene also imports TitleScene for its Esc-back behavior).
- `F5` is **not** handled here — it's intercepted at the top of `main.py`'s key loop and triggers a full process restart via `os.execv`. So F5 works from any scene.
