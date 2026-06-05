from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from ..scene import Scene
from ..panel import Panel
from ..widgets import (
    Widget,
    Label, TextBlock,
    List, ListItem, RadioGroup,
    Button, NumberInput, TextInput,
)

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


        l1 = Label('[Enter] confirm')
        l2 = Label('[Esc] cancel', color='bright_black')
        ls = List(
            0, 0, 30, 5,
            items=[ListItem(f'Item {i+1}', disabled=i%2 == 0) for i in range(12)],
            selectable=True,
            wrap=False
        )

        body_types = {
            'Buff':  'Punches hard.\n\nPrefers swords and  clubs. Your typical ADC.',
            'Slim':  'Twinkle toes.\n\nBenefits from using daggers and knuckles.',
            'Chonk': 'Damage sponge.\n\nEffectively utilizes heavy weapons, like maces and hammers.'
        }

        rg_desc = TextBlock(w=50, h=5, text=body_types['Buff']) # TODO add update() to reflow text vertically
        rg = RadioGroup(
            items=list(body_types.keys()),
            auto_key=True,
            gap=1,
            # orientation=RadioGroup.Orientation.VERTICAL,
            on_change=lambda v: (setattr(rg_desc, 'text', body_types[v.value]), Widget.NO_EVENT)[-1]
        )


        main.add('name', ti) # , anchor=Panel.Anchor.CENTER
        ti.move_by(dy=-1)
        main.add('hint_enter', l1.place_below(ti, 0))
        main.add('hint_esc', l2.place_right_of(l1, 3))
        main.add('list', ls.place_right_of(ti, 5))
        main.add('radio', rg.place_below(l1, 3))
        main.add('radio-desc', rg_desc.place_right_of(rg, 10))

        main.fit_to_content()
        main.align(ls, Panel.Anchor.RIGHT)

        main.separate(l1, rg)
        main.separate(ti, ls)
        # self.center(main)

        desc = self.add('desc', Panel(0, 0, 0, 0, title='About', pad_x=2))
        tb = TextBlock(
            'A wandering brawler. Loved by tavern keepers, feared by tax collectors.\n\n'
            'Born under a rusted lamppost, raised by stray cats, trained by a one-eyed monk who insisted everything could be solved with a left hook. So far, mostly correct.\n\n',
            w=main.lw, h=6,
            wrap=False,
        )
        desc.add('text', tb)
        desc.fit_to_content()
        desc.place_below(main, 1)

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
        side.fit_to_content()
        side.place_right_of(main, 2)

        stats = self.add('stats', Panel(0, 0, 30, 15, title='Stats'))
        stats_w = 18
        hp_in  = NumberInput(label='HP:',  width=stats_w, value=100, min_value=1, max_value=999)
        str_in = NumberInput(label='STR:', width=stats_w, value=10,  min_value=1, max_value=99)
        dex_in = NumberInput(label='DEX:', width=stats_w, value=10,  min_value=1, max_value=99)
        int_in = NumberInput(label='INT:', width=stats_w, value=10,  min_value=1, max_value=99)
        create = Button('Create', key='C', action=lambda: GameScene(self.screen))
        stats.add('hp',  hp_in)
        stats.add('str', str_in.place_below(hp_in, 0))
        stats.add('dex', dex_in.place_below(str_in, 0))
        stats.add('int', int_in.place_below(dex_in, 0))
        stats.add('create', create.place_below(int_in, 1))
        stats.fit_to_content()
        (stats.align(stats.widgets['create'], Panel.Anchor.RIGHT)).move_by(-2)
        stats.place_below(side, 1)

        self.center_all()

        
        # self._label_dy = (main.ih // 2) - 2

    # def _render(self, panel: Panel, screen: Screen):
    #     # panel.put_centered(screen, self._label_dy, 'Enter your name:')
    #     # panel.put_centered(screen, panel.ih - 2, )

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT: return self
        if result is Widget.CANCELLED: return TitleScene(self.screen)
        return GameScene(self.screen)
