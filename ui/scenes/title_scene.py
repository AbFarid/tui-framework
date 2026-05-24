from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ..scene import Scene
from ..panel import Panel
from ..widgets import Menu, Option, Widget

if TYPE_CHECKING:
    from ..screen import Screen

TITLE_ART = """\
  ▄▄▄▄▄▄
 █▀██▀▀▀█▄                █▄
   ██▄▄▄█▀    ▄           ██
   ██▀▀▀▄█ ██ ████▄ ▄███▀ ████▄
 ▄ ██   ██ ██ ██ ██ ██    ██ ██
 ▀██▀  ▄▀██▀█▄██ ▀█▄▀███▄▄██ ██
   ▄▄▄▄
 ▄█▀▀███▄▄                  █▄
 ██    ██                  ▄██▄
 ██    ██ ██ ██ ▄█▀█▄ ▄██▀█ ██
 ██  ▄ ██ ██ ██ ██▄█▀ ▀███▄ ██
  ▀█████▄▄▀██▀█▄▀█▄▄▄█▄▄██▀▄██
       ▀█
"""


class TitleScene(Scene):
    def __init__(self, screen: Screen):
        super().__init__(screen)
        main = self.add('main', Panel(
            0, 0, screen.width, screen.height,
            border_style=Panel.BorderStyle.ROUNDED,
            render=self._render,
        ))

        from .game_scene import GameScene
        from .name_scene import NameScene
        options = [
            Option('New Game', action=lambda: NameScene(screen)), # requirement: lambda
            Option('Continue', disabled=True),
            Option('Quit',     action=lambda: None),
        ]
        menu = Menu(
            x=0, y=0,  # set below once auto-width is known
            options=options,
            required=True,
            gap=1,
            auto_key=True,
        )
        menu.x = main.ix + (main.iw - menu.w) // 2
        menu.y = main.iy + main.ih - 14
        main.add('menu', menu)

    def _render(self, panel: Panel, screen: Screen):
        lines = TITLE_ART.splitlines()
        block_w = max(len(l) for l in lines)
        start_x = (panel.iw - block_w) // 2
        start_y = (panel.ih - len(lines)) // 2 - 4
        for i, line in enumerate(lines):
            panel.put(screen, start_x, start_y + i, line)
        panel.put_centered(screen, panel.ih - 2, '[F5] Restart')

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT or result is Widget.CANCELLED: return self
        return result  # type: ignore[return-value]