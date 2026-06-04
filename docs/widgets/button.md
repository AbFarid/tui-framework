# Button

Source: [ui/widgets/button.py](../../ui/widgets/button.py).

A focusable, clickable widget rendered as `[ Label ]`. Fires its `action` callback on Enter (when focused) or when its shortcut key is pressed anywhere in the panel.

## Construction

```python
Button(
    label: str,
    x: int = 0, y: int = 0,
    key: Optional[str] = None,
    action: Optional[Callable[[], Any]] = None,
    disabled: bool = False,
    highlight: Optional[str] = 'reverse',
)
```

| Param | Notes |
|-------|-------|
| `label` | The text inside the brackets (without the brackets). |
| `x, y` | Position. Usually set via `place_below(...)` etc. after construction. |
| `key` | Optional shortcut character. Stored lowercase. When set, the first occurrence of that letter in the label is rendered underlined as a hint. |
| `action` | Zero-arg callable invoked when the button fires. May return a value (e.g. a `Scene`) which propagates up as the `handle_key` result. |
| `disabled` | If `True`, the button is not focusable and renders dimmed; the shortcut doesn't fire. |
| `highlight` | Name of a blessed attribute (e.g. `'reverse'`, `'bold'`, `'on_blue'`) applied while focused. Set to `None` for no focus highlight. |

Width is computed as `len(label) + 4` to account for the `[ ` and ` ]` brackets.

## Attributes

| Attribute | Type |
|-----------|------|
| `label` | `str` |
| `key` | `Optional[str]` (lowercase) |
| `action` | `Optional[Callable[[], Any]]` |
| `disabled` | `bool` |
| `highlight` | `Optional[str]` |

## `focusable` (property)

Returns `not self.disabled`. So enabling/disabling a button at runtime correctly updates its focusability.

## Rendering

`draw(screen)`:

- Renders `[ label ]`.
- If `key` is set and that letter appears in `label`, the first occurrence is wrapped in `term.underline(...)` as a shortcut hint.
- If `disabled`, the whole text is dimmed with `term.bright_black`.
- Else if `is_focused` and `highlight` is set, applies `getattr(term, highlight)`.

## Key handling

| Input | Result |
|-------|--------|
| Enter while focused (and `action` is set) | Calls `action()`, returns its result. |
| Other sequence keys (arrows, Tab, …) | `BUBBLE`. |
| Matching `key` char (anywhere in the panel; pre-empted by Panel before forwarding) | Calls `action()`, returns its result. |
| Non-matching plain chars | `BUBBLE`. |
| Anything while `disabled` | `BUBBLE`. |

Note: the shortcut fire mostly comes from `Panel`'s pre-empt broadcast, **not** the button's own `handle_key`. But the button still handles its key in `handle_key` for the case where it's focused and you press its shortcut (the broadcast happens first, so this path is effectively dead in normal use — kept for completeness).

## Usage

```python
create = Button('Create', key='C', action=lambda: GameScene(self.screen))
stats.add('create', create.place_below(dex_in, 1))
```

The `'C'` in `Create` will be underlined as a hint, and pressing `c` (uppercase or lowercase) anywhere in the `stats` panel will fire the action.
