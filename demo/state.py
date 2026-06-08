from dataclasses import dataclass, field


@dataclass
class Character:
    name: str = 'Leeroy Jenkins'
    body: str = 'Buff'
    town: str = 'Punchester (Medium)'
    hp: int = 60
    strength: int = 16
    defense: int = 10
    agility: int = 10
    xp: int = 12
    teeth: int = 31


@dataclass
class GameState:
    character: Character = field(default_factory=Character)
    gold: int = 100


state = GameState()
