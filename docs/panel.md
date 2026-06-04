# Panel

Source: [ui/panel.py](../ui/panel.py).

A `Panel` is a composite `Widget`. It owns a dict of child widgets, draws a border + title bar + optional header/footer + body, and routes keys to the focused child (with arrow cycling, shortcut broadcasting, and Tab bubble-out at boundaries).

Because `Panel` inherits from `Widget`, you can add a `Panel` to another `Panel` — that's how nested layouts work.

## Construction

```python
Panel(
    x, y, w, h,
    title: str = '',
    title_style: TitleStyle = TitleStyle.BRACKET,
    default_alignment: Alignment = Alignment.LEFT,
    border: bool = True,
    border_style: BorderStyle = BorderStyle.THIN,
    header: bool = False,
    footer: bool = False,
    render: Optional[Callable[[Panel, Screen], None]] = None,
)
```

| Param | Notes |
|-------|-------|
| `x, y, w, h` | Outer bounding box (includes border). |
| `title` | Initial title; placed in the slot indicated by `default_alignment`. Optional — pass `''` for no title. |
| `title_style` | How the title is rendered in the top border. See `TitleStyle` below. |
| `default_alignment` | Which of the three title slots (LEFT / CENTER / RIGHT) the initial title goes into. Also the default for later `set_title()` calls. |
| `border` | Draw a border. Disable for a borderless panel. |
| `border_style` | THIN / ROUNDED / THICK. When the panel is focused, the style is **forced to THICK** for visual feedback (see `_effective_border_style`). |
| `header` | Reserves a header row inside the border (text row + thin divider). |
| `footer` | Same but at the bottom. |
| `render` | Optional callback for custom body painting. Signature `(panel, screen) -> None`. If set, `_draw_lines` is skipped — your callback fully owns the body. |

The constructor computes `ix, iy, iw, ih` (inner content rectangle, excluding border and header/footer rows). Use these when positioning child widgets inside.

## Inner rectangle

| Attribute | Meaning |
|-----------|---------|
| `ix, iy` | Top-left of the inner content area. |
| `iw, ih` | Inner content width / height. |

If `border=True`, inner is inset by 1 cell on each side. If `header=True`, inner top moves down 2 rows. Same for footer.

## Nested types

### `Panel.TitleStyle`

How the title text is wrapped before being painted into the top border:

| Member | Format | Example |
|--------|--------|---------|
| `BRACKET` | `'[ {} ]'` | `[ Title ]` |
| `FORK` | `'┤ {} ├'` | `┤ Title ├` |
| `PLAIN` | `' {} '` | ` Title ` |
| `TIGHT` | `'{}'` | `Title` |

### `Panel.Alignment`

`LEFT`, `CENTER`, `RIGHT`. Used as the key in `self._slots` to indicate which of three title slots a title sits in.

### `Panel.BorderStyle`

Each member is a tuple of box-drawing characters: `(top_left, top_right, bottom_left, bottom_right, horizontal, vertical, tee_left, tee_right)`.

| Member | Look |
|--------|------|
| `THIN` | `┌─┐ │ └─┘` with `├ ┤` tees |
| `ROUNDED` | `╭─╮ │ ╰─╯` with `├ ┤` tees |
| `THICK` | `┏━┓ ┃ ┗━┛` with `┠ ┨` tees |

When a panel is focused, drawing always uses THICK regardless of `border_style`. This is the focus indicator.

### `Panel.Anchor` (Flag)

Bit flags for `align(widget, anchor)`:

`LEFT`, `RIGHT`, `TOP`, `BOTTOM`, `CENTER_X`, `CENTER_Y`, and `CENTER` (= `CENTER_X | CENTER_Y`).

Combine with `|`. Order of evaluation in `align()`: center flags applied first, then specific edges, so e.g. `Anchor.CENTER_Y | Anchor.RIGHT` puts the widget against the right edge, vertically centered.

## Adding widgets

### `add(name, widget, anchor=None) -> Widget`

Register `widget` under `name`. Sets `widget.parent = self` and `widget.alias = name`. If `anchor` is given, calls `self.align(widget, anchor)` first. If no widget is currently focused and the new one is focusable, the new widget becomes focused.

Returns the widget so you can chain:

```python
ti = main.add('name', TextInput(...)).move_by(dy=-1)
main.add('hint', label.place_below(ti, 0))
```

### Positioning helpers

| Method | Effect |
|--------|--------|
| `center(widget)` | Center widget inside the inner area (X and Y). |
| `center_x(widget)` / `center_y(widget)` | One axis only. |
| `align(widget, Anchor)` | Edge/center alignment using `Anchor` flags. |

All return the widget so you can chain.

### `move_to(x, y) -> Self`

Override of `Widget.move_to` that **also moves all child widgets and the inner rectangle** by the same delta. This is why `Panel.add(...).place_below(other_panel)` works — children come along.

### `fit_to_content(pad_x=1, pad_y=1) -> Self`

Re-size the panel so its inner area tightly contains all current child widgets, with the given padding on each axis. Adjusts `ix, iy, iw, ih` and the outer `x, y, w, h` (accounting for border + header + footer rows).

Use after laying out children with relative placement to get a panel that's the "right size":

```python
panel.add(...).place_below(other)
panel.fit_to_content(pad_x=2)
self.center(panel)
```

## Focus

### `focus(name=None) -> Self`

Two-mode method:
- `focus()` (no arg) — focus the panel itself (delegates to `Widget.focus()`).
- `focus(name)` — set internal focus to the child named `name`. Blurs the previously focused child, focuses the new one if `self.is_focused`.

Raises `WidgetNotFoundError` if `name` isn't registered.

### `_handle_focus_bubble(child_name)`

Called by a child widget's `request_focus()`. Sets internal focus to that child, then bubbles to `self.parent` (typically the Scene) so scene focus also moves to this panel.

### `_cycle_focus(reverse=False, wrap=False) -> bool`

Move internal focus to next/previous focusable child. Returns `True` if focus moved. Used by Tab (no-wrap) and ↑/↓ (wrap) handling.

If the current focus isn't in the focusable list, it lands on the first (or last) focusable widget.

## Key handling

`handle_key(key)` in [panel.py:179](../ui/panel.py#L179). Order of operations:

1. **Plain-char shortcut broadcast.** Scans `self.widgets.values()` for any with `.key` matching `key.lower()` and not disabled. First match fires its `.action()` (or returns `NO_EVENT` if no action). This **pre-empts** the focused widget — that's how `c` fires the Create button even while a TextInput is focused.
2. **Forward** to focused child's `handle_key`.
3. **`CYCLE_OUT_FWD/BWD`** → cycle no-wrap, bubble at boundary.
4. **`BUBBLE` + ↑/↓/←/→** → cycle with wrap (↑/← backward, ↓/→ forward), return `NO_EVENT` (never bubbles out for arrows).
5. **`BUBBLE` + Tab/BTab** → cycle no-wrap, bubble at boundary.
6. Otherwise return child's result (often `BUBBLE`, sometimes a value).

See [architecture.md](architecture.md#how-panelhandle_key-routes-a-key) for the full bubble-up rationale.

## Title and content mutation

| Method | Purpose |
|--------|---------|
| `set_title(text, alignment=None)` | Set/replace the title in the slot indicated by `alignment` (defaults to `default_alignment`). |
| `clear_titles()` | Wipe all three title slots. |
| `set_lines(list[str])` | Replace body lines (used when no `render` callback). |
| `set_text(str)` | Same but splits on newlines. |
| `set_header(str)` | Set header text (no-op visually if `header=False`). |
| `set_footer(str)` | Same for footer. |

All return `self` for chaining.

## Render helpers (for `render` callbacks)

If you pass a custom `render` to the constructor, you can use:

- `panel.put(screen, dx, dy, text)` — draw at inner-relative `(dx, dy)`, clipped to inner width.
- `panel.put_centered(screen, dy, text)` — draw centered on row `dy` (inner-relative).

`TitleScene` is the main example.

## Notable behaviors

- **Focus indicator**: focused Panels always render with `THICK` border, regardless of `border_style`.
- **Three title slots**: a single Panel can show up to three titles (LEFT, CENTER, RIGHT). Useful for header rows like `[ Name ]   Stats   [ Inv ]`.
- **`fit_to_content` is destructive**: it changes the panel's geometry. Call it after laying out children, not before adding more.
