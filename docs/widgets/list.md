# List + ListItem

Source: [ui/widgets/list.py](../../ui/widgets/list.py).

A scrollable, optionally selectable list of items. Each row holds a `ListItem` with label, value, color, and disabled flag. The widget renders a vertical scrollbar in the rightmost column.

## `ListItem` (dataclass)

```python
@dataclass
class ListItem:
    label: str
    value: Any = None
    id: Optional[str] = None
    color: Optional[str] = None
    disabled: bool = False
```

| Field | Notes |
|-------|-------|
| `label` | Display text. |
| `value` | Arbitrary payload returned when the user picks this item. |
| `id` | Optional stable identifier; not used internally but available to callers. |
| `color` | Optional blessed attribute applied when the row is not selected (e.g. `'bright_black'` for tombstoned entries). |
| `disabled` | Renders dimmed and is skipped by selection movement. |

You can also pass plain strings to `List` — they're auto-wrapped into `ListItem(label=str)`.

## `List` construction

```python
List(
    x, y, w, h,
    items: Optional[list[Union[str, ListItem]]] = None,
    selectable: bool = False,
    required: bool = False,
    wrap: bool = True,
    highlight: Optional[str] = 'reverse',
    highlight_unfocused: Optional[str] = 'on_bright_black',
    show_scrollbar: bool = True,
)
```

| Param | Notes |
|-------|-------|
| `x, y, w, h` | Bounding box. With `show_scrollbar=True`, the last column is the scrollbar — content uses `w - 1`. |
| `items` | List of `ListItem` or plain strings. May be empty/None. |
| `selectable` | If `False`, the list is a passive scrolling viewport: no selection, no highlight, ignores all keys (returns `BUBBLE`). |
| `required` | If `True`, Esc returns `BUBBLE` instead of `CANCELLED`. |
| `wrap` | Whether selection movement wraps at the ends. |
| `highlight` | Blessed attribute applied to the selected row when the list is focused. |
| `highlight_unfocused` | Style applied to the selected row when the list isn't focused. `'on_bright_black'` gives a gray background; the cursor position is still visible. Set to `None` to hide selection when unfocused. |
| `show_scrollbar` | Reserve the rightmost column for a scrollbar with `╿` / `╽` tips and a `┃` thumb. |

### Size constraints

If `show_scrollbar=True`:
- `h < 4` raises `InvalidWidgetSizeError` (needs room for the two tips plus at least two thumb positions).
- `w < 2` raises `InvalidWidgetSizeError` (one column for content, one for the bar).

Otherwise just `w >= 1, h >= 1`.

## Attributes

| Attribute | Type |
|-----------|------|
| `items` | `list[ListItem]` |
| `selected` | `int` (index into `items`) |
| `scroll` | `int` (index of first visible row) |
| `selectable`, `required`, `wrap`, `show_scrollbar` | `bool` |
| `highlight`, `highlight_unfocused` | `Optional[str]` |

## Mutation methods

All return `self` for chaining.

| Method | Effect |
|--------|--------|
| `set_items(items)` | Replace all items. Resets `selected` and `scroll` to 0. |
| `append(item)` | Add to the end. |
| `remove(index)` | Delete by index. Clamps `selected` / `scroll` to remain valid. |
| `clear()` | Empty the list. |

## Rendering

`draw(screen)` paints each visible row:

1. Clears the row to spaces (over the content width).
2. If the row's item is `disabled`, dim it.
3. Else if `color` is set, apply that style.
4. If selected and `selectable`, overlay the focus highlight (or the unfocused highlight if the list isn't focused).

The scrollbar is drawn last on the rightmost column:
- Top tip `╿`, bottom tip `╽`, track filled with `│`.
- Thumb (`┃`) sized proportionally to the visible window vs. total items.
- Thumb is hidden when all items fit.

## Key handling

Only does anything when `selectable=True` — a non-selectable list returns `BUBBLE` for every key (it's just a display).

| Input | Result |
|-------|--------|
| ↑ | Move selection up (skipping disabled items). `NO_EVENT`. |
| ↓ | Move selection down. `NO_EVENT`. |
| Enter (on non-disabled item) | Return the selected `ListItem` (propagates as value). |
| Esc (when not `required`) | `CANCELLED`. |
| Anything else | `BUBBLE`. |

When `wrap=True`, ↑ at the top jumps to the bottom and vice versa. With `wrap=False`, hits the boundary and stops. Disabled items are skipped during movement.

`_scroll_to_selected()` keeps the selected row visible by adjusting `scroll`.

## Usage

```python
ls = List(0, 0, 30, 9,
    items=[f'Item {i+1}' for i in range(20)],
    selectable=True,
    wrap=False,
)
main.add('list', ls.place_right_of(ti, 3))
main.focus('list')
```

To distinguish picks by type, give items meaningful `value`:

```python
items = [
    ListItem(label='New Game', value='new'),
    ListItem(label='Continue', value='continue', disabled=True),
]
```

Then in `handle_key`:

```python
result = self.route_key(key)
if isinstance(result, ListItem):
    match result.value:
        case 'new': return NameScene(self.screen)
        case ...
```
