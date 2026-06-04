# Menu + Option

Source: [ui/widgets/menu.py](../../ui/widgets/menu.py).

A list of action items (`Option`s) rendered with a cursor (`❯ `) on the selected row. Each `Option` fires a callback when picked via Enter or its shortcut key. Supports vertical and horizontal orientation, numbered prefixes, and auto-assigned letter shortcuts.

Use `Menu` when each item is an **action** with its own callback (Title scene's `New Game / Continue / Quit`). Use `List` when items are **data** the user picks and you handle the result.

## `Option` (dataclass)

```python
@dataclass
class Option:
    label: str
    action: Callable = field(default_factory=lambda: lambda: None)
    disabled: bool = False
    key: Optional[str] = None  # normalized to lowercase in __post_init__
```

| Field | Notes |
|-------|-------|
| `label` | Display text. |
| `action` | Zero-arg callable invoked on Enter / shortcut press. Defaults to a no-op. Return value propagates up the chain (e.g. return a `Scene`). |
| `disabled` | Dimmed, skipped by selection, ignored by shortcut/number keys. |
| `key` | Optional explicit shortcut letter. If `auto_key=True` on the Menu, unset keys are auto-assigned from the label. |

## `Menu` construction

```python
Menu(
    x, y,
    options: list[Option],
    w: Optional[int] = None,
    orientation: Orientation = Orientation.VERTICAL,
    number_style: Optional[NumberStyle] = None,
    required: bool = False,
    highlight: Optional[str] = 'bold',
    cursor: str = '❯ ',
    gap: int = 0,
    auto_key: bool = False,
)
```

| Param | Notes |
|-------|-------|
| `x, y` | Position. |
| `options` | The items. Must be non-empty (constructor accesses `options[0]`). |
| `w` | Width. `None` = auto-fit to the widest rendered label (including cursor). |
| `orientation` | `VERTICAL` (default) stacks items rows-wise; `HORIZONTAL` lays them out left-to-right. |
| `number_style` | If set, items are prefixed with `1.`, `1)`, or `[1]` depending on style (or the option's `key` letter if set). |
| `required` | If `True`, Esc returns `NO_EVENT` (not `CANCELLED`) — Menu must be resolved by picking. |
| `highlight` | Blessed attribute applied to the selected option's label (e.g. `'bold'`, `'cyan'`). |
| `cursor` | The cursor string. Default `'❯ '`. |
| `gap` | Spacing between options (rows for vertical, spaces for horizontal). |
| `auto_key` | Auto-assign a `key` to each option without one, picking the first letter of the label not already taken. The chosen letter is rendered underlined in the label. |

## Nested types

### `Menu.Orientation`

`VERTICAL` or `HORIZONTAL`. Controls layout and which arrow keys move selection (↑/↓ vs ←/→).

### `Menu.NumberStyle`

How numeric prefixes look:

| Member | Format | Example |
|--------|--------|---------|
| `DOT` | `'{n}. {label}'` | `1. New Game` |
| `PAREN` | `'{n}) {label}'` | `1) New Game` |
| `BRACKET` | `'[{n}] {label}'` | `[1] New Game` |

`{n}` is the option index + 1, **unless** the option has a `key` set, in which case the key letter (uppercased) is used. So `[N] New Game` if `key='n'`, or `[1] New Game` otherwise.

## Attributes

| Attribute | Type |
|-----------|------|
| `options` | `list[Option]` |
| `selected` | `int` |
| `orientation`, `number_style`, `highlight`, `cursor`, `gap`, `auto_key` | as constructed |
| `required` | `bool` |

## Auto-key assignment

When `auto_key=True`, `_assign_auto_keys()` runs once in `__init__`:

1. Collect already-assigned keys from `options` (set comprehension).
2. For each option without a key, scan the label left-to-right for the first alphabetic letter not already taken (case-insensitive).
3. Assign that letter (lowercase) and add to the taken set.

If every letter in a label is taken, that option ends up without a key. Order matters — define options in priority order.

## Rendering

Vertical: each option painted at `(self.x, self.y + i * (1 + gap))`. Horizontal: all options joined with `' ' * gap` and painted on one row.

Each option's text comes from `_format()`:

1. Start with the label (or the number-styled label if `number_style` is set).
2. If `auto_key` is on and the option has a key, underline the first occurrence of that letter.
3. Prefix with the cursor (`❯ `) if this is the selected option, else with `' '` of the same width.
4. If disabled, dim with `bright_black`.
5. Else if selected and `highlight` is set, apply it.

## Key handling

Sequence keys:

| Input | Effect |
|-------|--------|
| ↑ / ↓ (vertical) | Move selection. `NO_EVENT`. |
| ← / → (horizontal) | Move selection. `NO_EVENT`. |
| Enter (on non-disabled option) | Calls `action()`, returns its result. |
| Esc (when not `required`) | `CANCELLED`. |
| Anything else | `BUBBLE`. |

Plain chars:

| Input | Effect |
|-------|--------|
| Matches an option's `key` (option enabled) | Calls that option's `action()`, returns its result. |
| Digit `n` when `number_style` is set and option `n-1` exists, isn't disabled, and has no explicit `key` | Calls that option's `action()`. |
| Anything else | `BUBBLE`. |

Selection movement via `_move(delta)` skips disabled options and **always wraps** (uses modulo). Different from `List`, which has a `wrap` flag.

## Usage

Title screen pattern:

```python
options = [
    Option('New Game', action=lambda: NameScene(screen)),
    Option('Continue', disabled=True),
    Option('Quit',     action=lambda: None),
]
menu = Menu(0, 0, options=options, required=True, gap=1, auto_key=True)
```

`auto_key=True` underlines `N`, `C`, `Q` (first letters) — pressing those triggers the corresponding action even when the cursor is elsewhere.
