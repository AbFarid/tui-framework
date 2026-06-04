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


class NameSceneMaster(Scene):
    """NameScene rebuilt as a single master Panel with header/footer that
    contains the sub-panels as nested children. Used to exercise panel-in-panel
    focus, Tab/arrow cycling, and shortcut scoping."""

    def __init__(self, screen: Screen):
        super().__init__(screen)

        master = self.add('master', Panel(
            0, 0, screen.width, screen.height,
            # title='Punch Quest',
            header=True,
            footer=True,
        ))
        master.set_header('  New Game — create your brawler')
        master.set_footer('  [Tab] move   [↑↓] cycle   [C] create   [Esc] cancel')

        # ── main panel ────────────────────────────────────────────────────────
        main = Panel(0, 0, 2, 2, title='Character', border=False)
        ti = TextInput(
            x=0, y=0, width=30,
            label='Enter your name:',
            placeholder='Your name…',
            max_length=20,
            required=True,
            on_submit=lambda _: (ls.request_focus(), Widget.NO_EVENT)[-1],
        )
        hint = Label('[Enter] confirm   [Esc] cancel')
        ls = List(
            0, 0, 30, 5,
            items=[ListItem(f'Item {i+1}', disabled=i % 2 == 0) for i in range(12)],
            selectable=True,
            wrap=False,
        )

        body_types = {
            'Buff':  'Punches hard. Prefers swords and clubs. Your typical ADC.',
            'Slim':  'Twinkle toes. Benefits from using daggers and knuckles.',
            'Chonk': 'Damage sponge. Effectively utilizes heavy weapons, like maces and hammers.',
        }
        rg_desc = TextBlock(w=40, h=3, text=body_types['Buff'])
        rg = RadioGroup(
            items=list(body_types.keys()),
            auto_key=True,
            gap=1,
            on_change=lambda v: (rg_desc.set_text(body_types[v.value]), Widget.NO_EVENT)[-1],
        )

        main.add('name', ti)
        # ti.move_by(dy=-1)
        main.add('hint', hint.place_below(ti, 0))
        main.add('list', ls.place_right_of(ti, 3))
        main.add('radio', rg.place_below(hint, 2))
        main.add('radio-desc', rg_desc.place_right_of(rg, 6))
        main.focus_child('name')
        main.fit_to_content()

        # ── side panel ────────────────────────────────────────────────────────
        side = Panel(0, 0, 2, 2, title='Side', border=False)
        a = TextInput(
            x=0, y=0, width=18,
            label='Field A:',
            placeholder='alpha…',
            on_submit=lambda v: (setattr(ti, 'value', v), ti.request_focus(), Widget.NO_EVENT)[-1],
        )
        b = TextInput(x=0, y=0, width=18, label='Field B:', placeholder='beta…')
        side.add('a', a)
        side.add('b', b.place_below(a, 1))
        side.fit_to_content()

        # ── stats panel ───────────────────────────────────────────────────────
        stats = Panel(0, 0, 2, 2, title='Stats', border=False)
        w = 18
        hp_in  = NumberInput(label='HP:',  width=w, value=100, min_value=1, max_value=999)
        str_in = NumberInput(label='STR:', width=w, value=10,  min_value=1, max_value=99)
        dex_in = NumberInput(label='DEX:', width=w, value=10,  min_value=1, max_value=99)
        create = Button('Create', key='C', action=lambda: GameScene(self.screen))
        stats.add('hp',  hp_in)
        stats.add('str', str_in.place_below(hp_in, 0))
        stats.add('dex', dex_in.place_below(str_in, 0))
        stats.add('create', create.place_below(dex_in, 1))
        stats.fit_to_content()
        stats.align(stats.widgets['create'], Panel.Anchor.RIGHT).move_by(-2)

        # ── about panel ───────────────────────────────────────────────────────
        about = Panel(0, 0, 2, 2, title='About', border=False)
        about_tb = TextBlock(
            'A wandering brawler. Loved by tavern keepers, feared by tax collectors.\n\n'
            'Backstory: born under a rusted lamppost, raised by stray cats, trained by a '
            'one-eyed monk who insisted everything could be solved with a left hook. So far, '
            'mostly correct.\n\n'
            'Tip: stance changes are free, but combos cost stamina. Pick your moment.',
            w=main.lw, h=6,
        )
        about.add('text', about_tb)
        about.fit_to_content()

        # ── lay the sub-panels out inside master, then nest them ──────────────
        # main.move_to(master.lx, master.ly)
        master.align(main, Panel.Anchor.TOP | Panel.Anchor.LEFT)
        side.place_right_of(main, 5)
        stats.place_below(side)
        about.place_below(main)

        master.add('main', main)
        master.add('side', side)
        master.add('about', about)
        master.add('stats', stats)
        master.focus_child('main')

        master.fit_to_content()
        self.center(master)

        # vertical first (full span), then horizontals stop on it
        master.separate(main, side)
        master.separate(main, about)
        master.separate(side, stats)

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT: return self
        if result is Widget.CANCELLED: return TitleScene(self.screen)
        return GameScene(self.screen)
