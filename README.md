# Punch Quest — TUI Framework

This is a semester project for the **PPY** course (_Podstawy programowania w języku Python_ – _Fundamentals of Python Programming_).

A terminal UI framework built in Python using `blessed`, demonstrated through an interactive demo. Renders to a fixed 120×40 canvas, centred in the terminal.

## Requirements

- Python 3.11+
- [blessed](https://pypi.org/project/blessed/) — terminal rendering

## Installation & Usage

0. Optionally, to use a virtual environment:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```

1. Install the requirements:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the demo:

   ```bash
   python main.py
   ```

## Controls

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Cycle focus |
| `↑` `↓` | Move selection |
| `←` `→` | Adjust value / release focus |
| `Enter` | Confirm |
| `Esc` | Cancel / back |
| `F5` | Restart |

## Project Structure

```
ui/         # framework — widgets, panels, scenes, screen
demo/       # game built on top of the framework
  scenes/   # title, character creation, town
  state.py  # shared game state (Character dataclass)
main.py     # entry point
```

## Framework Features

- **Widget tree** — Panel (nestable), TextInput, NumberInput, Button, List, Menu, RadioGroup, TextBlock, ProgressBar, Label
- **Focus system** — Tab cycling, directional focus, snap-on-entry, bubble-up event protocol
- **Panels** — border styles, header/footer rows, title slots, padding, auto-junction separators, `fit_to_content`
- **State persistence** — `Scene.save` / `Scene.load` (JSON under `state/`)
- **Validation** — TextInput regex blocklist rules
- **Debug logging** — stdout hijack (`debug.py`), `@traced` decorator, `Panel.walk` / `tree`
