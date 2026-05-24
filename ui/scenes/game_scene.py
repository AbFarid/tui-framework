from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ..scene import Scene
from ..panel import Panel

if TYPE_CHECKING:
    from ..screen import Screen


class GameScene(Scene):
    def __init__(self, screen: Screen):
        super().__init__(screen)

        p = (Panel(
            0, 0, screen.width, screen.height,
            # title='Main',
            border_style=Panel.BorderStyle.THICK,
            header=True,
            footer=True,
        )
            .set_header('  HP: 100   Stance: —   Gold: 0')
            .set_footer('  [ESC] back to title')
            .set_lines(['', '  (main area — dialogue / scene description)'])
        )

        self.add('main', p)

    def handle_key(self, key) -> Optional[Scene]:
        if key.is_sequence and key.name == 'KEY_ESCAPE':
            from .title_scene import TitleScene
            return TitleScene(self.screen)
        return self
    