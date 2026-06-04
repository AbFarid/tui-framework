# GameScene

Source: [ui/scenes/game_scene.py](../../ui/scenes/game_scene.py).

The main gameplay scene. Currently a placeholder — a single full-screen Panel with a `THICK` border, a header line, a footer hint, and one body line. No game logic yet.

## Layout

```python
Panel(
    0, 0, screen.width, screen.height,
    border_style=Panel.BorderStyle.THICK,
    header=True,
    footer=True,
)
    .set_header('  HP: 100   Stance: —   Gold: 0')
    .set_footer('  [ESC] back to title')
    .set_lines(['', '  (main area — dialogue / scene description)'])
```

Uses the setter-chaining API on Panel — each `set_*` returns `self`, so the whole construction is one expression.

## Key handling

```python
def handle_key(self, key):
    if key.is_sequence and key.name == 'KEY_ESCAPE':
        return TitleScene(self.screen)
    return self
```

Esc → return to title. Everything else → stay. The route_key/Panel/Widget machinery isn't invoked here because there's nothing focusable yet.

## What's missing

See [todo.md](../../todo.md). The combat model, player state, world graph, save/load, and inventory all need to exist before this scene becomes interactive.
