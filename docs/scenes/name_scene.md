# NameScene

Source: [ui/scenes/name_scene.py](../../ui/scenes/name_scene.py).

The character-creation scene. Also the **integration playground** for the widget system — it deliberately exercises multiple panels, cross-panel focus, cross-widget callbacks, and Panel-scoped shortcuts. If you're testing whether something broke, run this scene first.

## Layout — three panels

```
┌──────────── New Game ────────────┐  ┌──── Side ────┐
│                                  │  │              │
│  Enter your name: [           ]  │  │  Field A:    │
│  [Enter] confirm  [Esc] cancel   │  │  ┌──────┐    │
│                                  │  │  └──────┘    │
│                ┌── Items ──┐     │  │              │
│                │ Item 1    │     │  │  Field B:    │
│                │ Item 2    │     │  └──────────────┘
│                │ ...       │     │
│                └───────────┘     │  ┌─── Stats ────┐
└──────────────────────────────────┘  │  HP:   100   │
                                      │  STR:   10   │
                                      │  DEX:   10   │
                                      │  [ Create ]  │
                                      └──────────────┘
```

### `main` panel (left)
- `TextInput` named `'name'` — required, max length 20. On submit, focuses the list across the Tab boundary via `request_focus`.
- `Label` `'hint'` — control hint below the input.
- `List` `'list'` — 20 dummy items, no wrap, selectable. Initially focused (`main.focus('list')`).
- Positioned with `fit_to_content(pad_x=2)`, then centered in the scene.

### `side` panel (top right)
- Two `TextInput`s `'a'` and `'b'`. `a.on_submit` writes the value into `main.name.value` and refocuses `main.name` (cross-panel focus via `request_focus`).
- Placed right of `main` with `place_right_of(main, 2)`.

### `stats` panel (bottom right)
- Three `NumberInput`s — `HP` (0–999, default 100), `STR` (0–99, default 10), `DEX` (0–99, default 10). All `width=22` so the `− NNN +` controls align.
- `Button` named `'create'` with `key='C'` — fires the scene transition. The `C` is rendered underlined in the label; pressing `c` anywhere in the `stats` panel triggers it.
- Placed below `side` with `place_below(side, 1)`.

## Cross-widget callbacks (the lambda showcase)

The TextInput on the left:

```python
TextInput(..., on_submit=lambda _: (ls.request_focus(), Widget.NO_EVENT)[-1])
```

Hands focus to the list when the user submits the name. The tuple-with-index-`-1` is the standard idiom for a side-effect-producing lambda that also returns a sentinel.

Field A on the right:

```python
TextInput(..., on_submit=lambda v: (
    setattr(ti, 'value', v),
    ti.request_focus(),
    Widget.NO_EVENT,
)[-1])
```

On submit, copies the value into the main name field and refocuses it across panels. Demonstrates that `request_focus` correctly handles cross-panel transitions — the Scene's `_handle_focus_bubble` repositions panel focus along with widget focus.

The Create button:

```python
Button('Create', key='C', action=lambda: GameScene(self.screen))
```

`action` returns the new scene; the value propagates up through `Button.handle_key` → `Panel.handle_key` (broadcast pre-empt) → `Scene.route_key` → `NameScene.handle_key`, which transitions.

## `handle_key(key) -> Optional[Scene]`

```python
def handle_key(self, key):
    result = self.route_key(key)
    if result is Widget.NO_EVENT: return self
    if result is Widget.CANCELLED: return TitleScene(self.screen)
    return GameScene(self.screen)
```

- `NO_EVENT` → stay.
- `CANCELLED` (any TextInput's Esc) → go back to title.
- Anything else (including the `GameScene` returned by Create) → go to GameScene.

The "any other return value = transition to GameScene" is a shortcut that works for this scene because the only thing that returns a value here is the Create button. Less general than dispatching on the actual return value, but fine for now.

## What this scene tests

| Behavior | Where to look |
|----------|---------------|
| Tab cycling within a panel | Tab inside `main` (name → list → name → …) |
| Tab cycling across panels at boundary | Tab from list's last focusable → side's Field A |
| ↑/↓ panel cycling in `stats` | NumberInput returns BUBBLE on arrows; Panel cycles hp → str → dex → create |
| ↑/↓ consumed by List | List in `main` returns NO_EVENT on ↑/↓; Panel doesn't cycle |
| `request_focus` cross-panel | Field A submit → name field focused, name submit → list focused |
| Panel-scoped shortcut while field focused | While in HP input, press `c` → Create fires |
| Scoped shortcut isolation | While in `main` panel, `c` does **not** fire Create (broadcast is Panel-scoped, Create lives in `stats`) |
| Backspace seeded value | Type into name, then Backspace — clears whole field first time |
| Min/max clamp | NumberInput won't go below 0 or above max |
| Esc cancel | Esc on name field → back to TitleScene |
