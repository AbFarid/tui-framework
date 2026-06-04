# errors.py

Custom exception hierarchy. All project errors derive from `GameError`, so:

```python
try:
    ...
except GameError as e:
    ...  # catches anything raised by this project
```

Source: [errors.py](../errors.py).

## `GameError(Exception)`

Base for every custom exception in the project. Has no extra attributes — exists so callers can write a single `except GameError` and catch any project-raised error.

## `WidgetNotFoundError(GameError)`

Raised by `Panel.focus(name)` when `name` isn't a registered child widget.

| Attribute | Type | Meaning |
|-----------|------|---------|
| `name` | `str` | The name that was looked up. |
| `available` | `list[str]` | Names that are actually registered on the panel. |

Message format: `No widget named 'X' in panel; have: [...]`.

## `PanelNotFoundError(GameError)`

Raised by `Scene.focus(name)` when `name` isn't a registered panel.

Same attribute shape as `WidgetNotFoundError`.

## `InvalidWidgetSizeError(GameError)`

Raised by widget constructors when given dimensions that would render unusable. Currently raised by `List.__init__` for sizes too small to host a scrollbar (`h < 4` or `w < 2`).

| Attribute | Type | Meaning |
|-----------|------|---------|
| `w` | `int` | Requested width. |
| `h` | `int` | Requested height. |
| `requirement` | `str` | Human-readable constraint that was violated. |

Message format: `Invalid widget size WxH: <requirement>`.
