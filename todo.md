# todo

## Widgets (next)
- [ ] **TextInput** — single-line entry. Needed for character name @ New Game, save-slot names. Should mirror Menu's contract: `handle_key` returns `NO_EVENT` / `CANCELLED` / submitted-string.
- [ ] **ScrollableList / Log** — for inventories and dialogue/event logs longer than the panel.
- [ ] **ProgressBar** — promote ad-hoc `hp_bar()` to a widget once HP shows up in more than one place.

## Scene / navigation plumbing
- [ ] **Back stack** — every transition currently hard-swaps. Needed the moment we want "Inventory → back to Game" without `GameScene` knowing about Inventory.
- [ ] **Scene-enter args** — convention for passing state into a new scene (e.g. which enemy you walked into). Fine to defer.

## Game model (entirely missing)
- [ ] `Player` — hp, gold, stance, inventory
- [ ] `World` / location graph
- [ ] `Combat` resolver — attack/block/stance from old README is unimplemented
- [ ] Save/load — `Continue` is permanently disabled until this exists

## Polish
- [ ] Update README
- [ ] Pin versions in `requirements.txt`
- [ ] Tests