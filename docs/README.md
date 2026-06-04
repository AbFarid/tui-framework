# Punch Quest — Internal Docs

Reference docs for the project's classes. Source of truth is the code; this index exists to orient newcomers (and future you) without re-deriving the architecture from scratch.

## Read this first

- **[architecture.md](architecture.md)** — the only doc you have to read. Explains how `Scene`, `Panel`, and `Widget` compose, how focus moves, and how key events bubble. Every other doc assumes this vocabulary.

## Reference (one page per class)

### Core
- **[errors.md](errors.md)** — `GameError`, `WidgetNotFoundError`, `PanelNotFoundError`, `InvalidWidgetSizeError`
- **[screen.md](screen.md)** — `Screen` (terminal lifecycle, draw buffer, key reader)
- **[scene.md](scene.md)** — `Scene` (top of the tree; owns panels)
- **[panel.md](panel.md)** — `Panel` (composite widget; owns widgets)

### Widgets
- **[widgets/widget.md](widgets/widget.md)** — `Widget` (abstract base) + `Event` sentinels
- **[widgets/button.md](widgets/button.md)** — `Button`
- **[widgets/label.md](widgets/label.md)** — `Label`
- **[widgets/list.md](widgets/list.md)** — `List`, `ListItem`
- **[widgets/menu.md](widgets/menu.md)** — `Menu`, `Option`
- **[widgets/number_input.md](widgets/number_input.md)** — `NumberInput`
- **[widgets/text_input.md](widgets/text_input.md)** — `TextInput`

### Concrete scenes
- **[scenes/title_scene.md](scenes/title_scene.md)** — `TitleScene`
- **[scenes/game_scene.md](scenes/game_scene.md)** — `GameScene`
- **[scenes/name_scene.md](scenes/name_scene.md)** — `NameScene` (the integration test scene)

## Project entry point

[`main.py`](../main.py) drives a fixed-tick loop (~30 fps):

1. Construct a `Screen` (context manager handles terminal setup/teardown).
2. Construct an initial `TitleScene`, call `enter()`.
3. Each tick: `scene.update(dt)` → `scene.draw()` → `screen.read_key(timeout=TICK)` → `scene.handle_key(key)`.
4. `scene.handle_key` returns the next scene (`self` to stay, another scene to transition, `None` to quit). `F5` triggers a full process restart.

## Conventions used in these docs

- **Signature** blocks list the constructor as written, then prose for each notable parameter.
- **Behavior** sections describe what the widget consumes vs. lets bubble. This matters because Panel-level cycling and shortcut broadcasting depend on whether the focused widget returns `NO_EVENT` (consumed) or `BUBBLE` (didn't handle).
- Links into source use line numbers, e.g. [panel.py:179](../ui/panel.py#L179).
