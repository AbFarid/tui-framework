# NumberInput

Source: [ui/widgets/number_input.py](../../ui/widgets/number_input.py).

A widget for entering an integer with optional min/max bounds. Rendered as a label on the left plus a `− NNNN +` control on the right, with an optional underline below. Supports both digit-typing and arrow-key adjustment.

## Construction

```python
NumberInput(
    x: int = 0, y: int = 0,
    width: Optional[int] = None,
    max_digits: int = 4,
    value: int = 0,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    label: Optional[str] = None,
    style: Style = Style.UNDERLINE,
    required: bool = False,
    on_submit: Optional[Callable[[int], Any]] = None,
)
```

| Param | Notes |
|-------|-------|
| `x, y` | Position. |
| `width` | Total widget width (label + control). `None` = compute as `len(label) + gap(1) + control_w`. Setting wider than the natural width pushes the control to the right edge — useful for vertically aligning controls across multiple NumberInputs with different label lengths. |
| `max_digits` | Maximum digits the value can hold. Determines the slot width: `control_w = max_digits + 4` for the `− NNNN +` format. |
| `value` | Initial value, clamped to `[min_value, max_value]` immediately. |
| `min_value` | Lower bound (inclusive). `None` = unbounded. Negative values are possible if no min is set. |
| `max_value` | Upper bound (inclusive). `None` = unbounded. |
| `label` | Optional label text painted on the left. |
| `style` | `Style.UNDERLINE` (default) or `Style.NONE`. Adds a `────────` row below the control. |
| `required` | If `True`, Esc returns `NO_EVENT` instead of `CANCELLED`. |
| `on_submit` | Called with the current `value` when the user presses Enter. May return a value or another `Widget.Event`. If `None`, Enter just returns `value`. |

## Nested: `NumberInput.Style`

| Member | Effect |
|--------|--------|
| `NONE` | Just the label and control, no decoration. |
| `UNDERLINE` | Plus a `─` row below the control of width `control_w`. |

## Attributes

| Attribute | Type |
|-----------|------|
| `label`, `max_digits` | as constructed |
| `value` | `int` — clamped on init and on every mutation |
| `min_value`, `max_value` | `Optional[int]` |
| `style` | `Style` |
| `required`, `on_submit` | as constructed |
| `is_dirty` | `bool` — `True` once the user has touched the field. Used to distinguish "first edit replaces value" from "subsequent edits append/trim". |
| `_control_w` | precomputed `max_digits + 4` |

## Clamping

`_clamp(v, lo, hi)` is the single internal helper: applies `min_value` and `max_value` (each optional). Called:
- Once in `__init__` on the initial `value`.
- After every digit-append.
- After every ←/→ adjust.

Backspace does **not** clamp upward (since you're shrinking). Backspace on a value already below `min_value` would be possible if `min_value` weren't enforced at init — but it is, so the path is safe.

## Dirty flag semantics

The `is_dirty` flag distinguishes "this is a freshly seeded value, the first interaction should overwrite it" from "the user is editing":

| Action | When `is_dirty=False` | When `is_dirty=True` |
|--------|----------------------|----------------------|
| Type digit | Replace value with that digit; set dirty. | Append digit (if within `max_digits`); clamp. |
| Backspace | Reset value to `0`; set dirty. | Trim the last digit (or set `0` if empty). |
| ← / → | Adjust value by ±1; set dirty. | Same. |

So the first digit you type replaces the initial value; subsequent digits append. Same intuition as how a number field in most UI toolkits works.

## Rendering

`draw(screen)`:

- If `label` is set, paint at `(self.x, self.y)`.
- Compute `ctrl_x = self.x + self.w - control_w` (right-align the control).
- Format value as `str(value).rjust(max_digits)` and frame it as `'− {value} +'`. When focused, wrap with `term.bold`.
- If `style == UNDERLINE`, paint `─` repeated `control_w` times on `self.y + 1`.

The minus is U+2212 (`−`) for visual symmetry with `+`.

## Key handling

Sequence keys:

| Input | Effect |
|-------|--------|
| ← | `_adjust(-1)`. Sets dirty. `NO_EVENT`. |
| → | `_adjust(+1)`. Sets dirty. `NO_EVENT`. |
| Backspace | Trim/reset per dirty flag. `NO_EVENT`. |
| Enter | Call `on_submit(value)` if set, else return `value`. |
| Esc (when not `required`) | `CANCELLED`. |
| Anything else (↑/↓, F-keys, …) | `BUBBLE`. |

Plain chars:

| Input | Effect |
|-------|--------|
| Digit | Type/append per dirty flag, clamping. `NO_EVENT`. |
| Letter / punctuation | `BUBBLE` — these don't apply to numbers, so they're free for panel shortcuts. |

This BUBBLE-on-letters behavior is what makes `c` fire the Create button even when a NumberInput is focused: Panel's shortcut broadcast pre-empts, but for any character that doesn't match a button, it bubbles cleanly.

↑/↓ bubble so the parent Panel can cycle focus between stat fields and the Create button.

## Usage

```python
hp_in  = NumberInput(label='HP:',  width=22, value=100, min_value=0, max_value=999)
str_in = NumberInput(label='STR:', width=22, value=10,  min_value=0, max_value=99)
dex_in = NumberInput(label='DEX:', width=22, value=10,  min_value=0, max_value=99)

stats.add('hp',  hp_in)
stats.add('str', str_in.place_below(hp_in, 0))
stats.add('dex', dex_in.place_below(str_in, 0))
```

Passing the same `width=22` to all three ensures the `− NNN +` controls line up vertically despite the labels having different lengths.
