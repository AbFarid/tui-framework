# Label

Source: [ui/widgets/label.py](../../ui/widgets/label.py).

A non-focusable, non-interactive text widget. Use for headings, hints, instructions, etc. Supports multi-line text and a single blessed color attribute.

## Construction

```python
Label(
    text: str,
    x: int = 0, y: int = 0,
    color: Optional[str] = None,
)
```

| Param | Notes |
|-------|-------|
| `text` | The label text. Use `\n` for multi-line. |
| `x, y` | Position. |
| `color` | Optional blessed text attribute name (`'bold'`, `'cyan'`, `'bright_black'`, `'on_blue'`, etc.) applied to every line. |

Width is computed as the longest line. Height is the number of lines.

## Class attributes

| Attribute | Value |
|-----------|-------|
| `focusable` | `False` |

Labels are skipped by Panel focus cycling.

## Attributes

| Attribute | Type |
|-----------|------|
| `lines` | `list[str]` (the text split on newlines) |
| `color` | `Optional[str]` |

## Rendering

Each line is drawn at `(self.x, self.y + i)`. If `color` is set and resolves to a valid `term` attribute, the line is wrapped with that attribute before being painted. Unknown color names are silently ignored (the text is drawn unstyled).

## Key handling

Returns `BUBBLE` for everything. Labels never get focused, so this is mostly a formality — but it means if a Label somehow ends up in the chain, keys correctly propagate past it.

## Usage

```python
hint = Label('[Enter] confirm   [Esc] cancel')
main.add('hint', hint.place_below(input_widget, 0))
```
