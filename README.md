# Combat Game

A turn-based combat game( with timed decisions?).

## Requirements

- Python 3.10+
- [blessed](https://pypi.org/project/blessed/) — terminal UI library

## Setup

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install blessed
```

## Running

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `1` `2` `3` `4` | Attack Head / Torso / Hips / Legs |
| `Q` `W` `E` `R` | Block Head / Torso / Hips / Legs |
| `Z` `X` `C` | Stance: Defensive / Offensive / Agile |
| `ESC` / `Ctrl+C` | Quit |

Each turn you have a limited time to choose your attack target, block location, and stance before the round resolves automatically.
