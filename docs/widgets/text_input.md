# TextInput

Source: [ui/widgets/text_input.py](../../ui/widgets/text_input.py).

Single-line text entry. Optional label, placeholder, and length cap. Renders one of three styles: bare, underlined, or boxed. While focused, requests the terminal cursor at the next character position.

## Construction

```python
TextInput(
    x: int, y: int,
    width: int,
    value: str = '',
    placeholder: str = '',
    max_length: Optional[int] = None,
    required: bool = False,
    label: Optional[str] = None,
    label_centered: bool = False,
    style: Style = Style.UNDERLINE,
    gap: int = 1,
    on_submit: Optional[Callable[[str], Any]] = None,
)
```

| Param | Notes |
|-------|-------|
| `x, y` | Position. |
| `width` | The **field** width (visible character slots), not including border padding. |
| `value` | Initial value. |
| `placeholder` | Shown dimmed when `value` is empty. |
| `max_length` | Optional cap on `len(value)`. `None` = unlimited. |
| `required` | If `True`, Enter on empty does nothing; Esc returns `NO_EVENT` instead of `CANCELLED`. |
| `label` | Optional label above the field. |
| `label_centered` | If `True`, center the label across the widget's bounding box (otherwise left-align with a 1-cell indent for `BORDER` style, 0 for others). |
| `style` | `NONE`, `UNDERLINE`, or `BORDER`. See below. |
| `gap` | Rows of vertical space between the label and the field. |
| `on_submit` | Called with the current `value` on Enter. May return a value (e.g. a `Scene`) which propagates. |

Bounding-box size is computed from style + label + gap. The widget's `w, h` reflect the full footprint (label + gap + field + decoration).

## Nested: `TextInput.Style`

| Member | Effect |
|--------|--------|
| `NONE` | Bare field, no decoration. |
| `UNDERLINE` | A `────────` row below the field. |
| `BORDER` | A `┌─┐ │ └─┘` box around the field with 1 cell of horizontal padding inside. |

## Attributes

| Attribute | Type |
|-----------|------|
| `field_width` | `int` — visible character slots. |
| `value` | `str` — current contents. |
| `placeholder`, `label`, `style`, `gap`, `required` | as constructed |
| `max_length`, `on_submit` | as constructed |
| `label_centered` | `bool` |
| `is_dirty` | `bool` — `True` once the user has typed or pressed Backspace. |

## Dirty flag

The first Backspace on a non-empty initial value clears the whole field (treated as "delete the seeded value"). Subsequent Backspaces trim one char at a time. Typing always appends.

This means if you seed `value='alpha'` and the user wants to edit, the first key is the awkward one — Backspace wipes, then they retype. Acceptable trade-off for the common case where seeded values are usually accepted as-is.

## Rendering

`draw(screen)`:

1. Label (if set), positioned per `label_centered` and `style`.
2. The field background: spaces of length `field_width` (or a bordered box for `BORDER` style).
3. The value (or placeholder, dimmed via `term.bright_black`).
4. The underline (for `UNDERLINE` style only).
5. If focused, `screen.request_cursor(cursor_x, fy)` so the terminal cursor blinks at the next character position.

`cursor_x` clamps to `fx + field_width - 1` so it doesn't visually run off the end of the field even if `len(value) >= field_width`.

## Key handling

Sequence keys:

| Input | Effect |
|-------|--------|
| Enter (when `value` is non-empty OR not `required`) | Call `on_submit(value)` if set, else return `value`. |
| Enter (when `required` and empty) | `NO_EVENT` (silently ignored — user must type something). |
| Esc (when not `required`) | `CANCELLED`. |
| Esc (when `required`) | `NO_EVENT`. |
| Backspace | Clear (if first edit on dirty value) or trim one char. `NO_EVENT`. |
| Anything else (arrows, Tab, F-keys, …) | `BUBBLE`. |

Plain chars:

| Input | Effect |
|-------|--------|
| `key.isprintable()` and under `max_length` | Append to `value`. `NO_EVENT`. |
| `key.isprintable()` at `max_length` | Silently ignored. `NO_EVENT` (still consumed — typing past the cap doesn't bubble). |
| Non-printable, non-sequence (rare) | `BUBBLE`. |

### Interaction with Panel shortcut broadcasting

TextInput consumes printable characters via `NO_EVENT`. That would normally block Panel-scoped shortcuts (e.g. `c` for Create) when the field is focused. But Panel intercepts plain-char keys **before** forwarding to the focused widget — so shortcuts still fire even when a TextInput is the focus target.

**Side effect**: the user can't type a literal character that's bound to a Button shortcut in the same Panel. E.g. in the New Game scene, you can't type `c` into the name field because `c` always fires Create. Documented limitation; acceptable for the current scenes.

## Cross-widget focus pattern

A common idiom: a TextInput's `on_submit` hands focus to another widget via `request_focus()`:

```python
ti = TextInput(..., on_submit=lambda _: (ls.request_focus(), Widget.NO_EVENT)[-1])
```

Tuple-with-index trick is the workaround for lambda's single-expression limitation: evaluate the side effect, then return the sentinel.

Or copy the submitted value across panels:

```python
a = TextInput(..., on_submit=lambda v: (
    setattr(ti, 'value', v),
    ti.request_focus(),
    Widget.NO_EVENT,
)[-1])
```

## Usage

```python
ti = TextInput(
    x=0, y=0, width=30,
    label='Enter your name:',
    placeholder='Your name…',
    max_length=20,
    required=True,
    on_submit=lambda _: (ls.request_focus(), Widget.NO_EVENT)[-1],
)
main.add('name', ti)
```
