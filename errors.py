# requirement: custom errors

class GameError(Exception):
    """Base for all custom errors in this project. Catch this to handle any project error."""


class WidgetNotFoundError(GameError):
    """Raised when referencing a widget by name that isn't registered on a panel."""
    def __init__(self, name: str, available: list[str]):
        super().__init__(f"No widget named {name!r} in panel; have: {available}")
        self.name = name
        self.available = available


class PanelNotFoundError(GameError):
    """Raised when referencing a panel by name that isn't registered on a scene."""
    def __init__(self, name: str, available: list[str]):
        super().__init__(f"No panel named {name!r} in scene; have: {available}")
        self.name = name
        self.available = available


class InvalidWidgetSizeError(GameError):
    """Raised when a widget is constructed with dimensions that make it unusable."""
    def __init__(self, w: int, h: int, requirement: str):
        super().__init__(f"Invalid widget size {w}x{h}: {requirement}")
        self.w = w
        self.h = h
        self.requirement = requirement
