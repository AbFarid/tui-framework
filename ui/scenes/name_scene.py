from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ..scene import Scene
from ..panel import Panel
from ..widgets import TextInput, Widget, Label, List, NumberInput, Button

from .game_scene import GameScene
from .title_scene import TitleScene

if TYPE_CHECKING:
    from ..screen import Screen


class NameScene(Scene):
    def __init__(self, screen: Screen):
        super().__init__(screen)

        main = self.add('main', Panel(
            0, 0, screen.width, screen.height,
            title='New Game',
            # border_style=Panel.BorderStyle.THICK,
            # render=self._render,
        ))

        input_w = 30
        # ix = main.ix + (main.iw - input_w) // 2
        # iy = main.iy + main.ih // 2
        ti = TextInput(
            x=0, y=0, width=input_w,
            label='Enter your name:',
            # label_centered=True,
            placeholder='Your name…',
            max_length=20,
            required=True,
            # style=TextInput.Style.BORDER,
            on_submit=lambda _: (ls.request_focus(), Widget.NO_EVENT)[-1]
        )

        l = Label('[Enter] confirm   [Esc] cancel')
        ls = List(
            0, 0, 30, 9,
            items=[f'Item {i+1}' for i in range(20)],
            selectable=True,
            wrap=False
        )

        main.add('name', ti) # , anchor=Panel.Anchor.CENTER
        # main.widgets['name']
        ti.move_by(dy=-1)
        main.add('hint', l.place_below(ti, 0))
        main.add('list', ls.place_right_of(ti, 3))
        main.focus('list')

        main.fit_to_content(pad_x=2)
        self.center(main)

        side = self.add('side', Panel(
            0, 0, 30, 15,
            title='Side',
        ))
        a = TextInput(
            x=0, y=0, width=18,
            label='Field A:',
            placeholder='alpha…',
            on_submit=lambda v: (setattr(ti, 'value', v), ti.request_focus(), Widget.NO_EVENT)[-1]
        )
        b = TextInput(x=0, y=0, width=18, label='Field B:', placeholder='beta…')
        side.add('a', a)
        side.add('b', b.place_below(a, 1))
        side.fit_to_content(pad_x=2)
        side.place_right_of(main, 2)

        stats = self.add('stats', Panel(0, 0, 30, 15, title='Stats'))
        hp_in  = NumberInput(label='HP:',  width=22, value=100, max_value=999)
        str_in = NumberInput(label='STR:', width=22, value=10,  max_value=99)
        dex_in = NumberInput(label='DEX:', width=22, value=10,  max_value=99)
        create = Button('Create', key='C', action=lambda: GameScene(self.screen))
        stats.add('hp',  hp_in)
        stats.add('str', str_in.place_below(hp_in, 0))
        stats.add('dex', dex_in.place_below(str_in, 0))
        stats.add('create', create.place_below(dex_in, 1))
        stats.fit_to_content(pad_x=2)
        stats.place_below(side, 1)

        
        # self._label_dy = (main.ih // 2) - 2

    # def _render(self, panel: Panel, screen: Screen):
    #     # panel.put_centered(screen, self._label_dy, 'Enter your name:')
    #     # panel.put_centered(screen, panel.ih - 2, )

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT: return self
        if result is Widget.CANCELLED: return TitleScene(self.screen)
        return GameScene(self.screen)
