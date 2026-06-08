from __future__ import annotations
from random import choice
from typing import TYPE_CHECKING, Optional

from ui.scene import Scene
from ui.panel import Panel
from ui.widgets import (
    Widget,
    Label, TextBlock,
    List, ListItem, RadioGroup,
    Button, NumberInput, TextInput,
)

from .town_scene import TownScene
from .title_scene import TitleScene
from demo.state import state, Character

if TYPE_CHECKING:
    from ui.screen import Screen
    from .creation_scene_single import CreationScene_S

premade = ['Ser Pummelot', 'Fistopher Walken', 'Leeroy Jenkins', 'Reginald', 'Glass Joe']
towns   = ['Soggybottom (Easy)', 'Punchester (Medium)', 'Painsylvania (Hard)']

body_types = {
    'Buff':  'Punches hard.\n\nPrefers swords and  clubs. Your typical ADC.',
    'Slim':  'Twinkle toes.\n\nBenefits from using daggers and knuckles.',
    'Chonk': 'Damage sponge.\n\nEffectively utilizes heavy weapons, like maces and hammers.'
}

class_stats = {
    'Buff':  {'hp': 60, 'str': 16, 'def': 10, 'agi': 10},
    'Slim':  {'hp': 50, 'str': 12, 'def':  8, 'agi': 18},
    'Chonk': {'hp': 80, 'str': 10, 'def': 18, 'agi': 10},
}

about = '''A wandering brawler. Loved by tavern keepers, feared by tax collectors.

Born under a rusted lamppost, raised by stray cats, trained by a one-eyed monk who insisted everything could be solved with a left hook. So far, mostly correct.'''



class CreationScene_M(Scene):
    def __init__(self, screen: Screen):
        super().__init__(screen)

        self.add_command('t', 'Toggle Panel Mode', lambda: (self.save('Creation'), CreationScene_S(self.screen))[-1])
        self.add_command('q', 'Save & Quit', lambda: (self.save(), Widget.CANCELLED)[-1])
        h = self.get_command_hints()

        char_panel = self.add('main', Panel(
            0, 0, screen.width, screen.height,
            title='Character',
            # border_style=Panel.BorderStyle.THICK,
            # render=self._render,
        ))

        name_input = TextInput(
            x=0, y=0, width=30,
            label='Enter your fighter\'s name:',
            # label_centered=True,
            placeholder=choice(premade),
            max_length=20,
            required=True,
            # style=TextInput.Style.BORDER,
            # on_submit=lambda _: (ls.request_focus(), Widget.NO_EVENT)[-1]
            rules=[
                (r'^.{0,2}$', 'At least 3 characters'), # requirement: regex
                (r'[0-9]', 'No numbers allowed'),
                (r'[^A-Za-z0-9 -]', 'No special symbols'),
                (r'^[^A-Z]', 'Must be capitalized'),
            ],
        )

        # l1 = Label('[Enter] confirm')
        # l2 = Label('[Esc] cancel', color='bright_black')

        selector_title = Label('Or choose a fighter:')
        name_selector = List(
            0, 0, 30, 4,
            items=[ListItem(x) for x in premade],
            selectable=True,
            # wrap=False
            on_select=lambda item: (setattr(name_input, 'value', item.value), Widget.NO_EVENT)[-1],
        )

        body_type_desc = TextBlock(w=50, h=5, text=body_types['Buff'])
        body_type_selector = RadioGroup(
            items=list(body_types.keys()),
            auto_key=True,
            gap=1,
            # orientation=RadioGroup.Orientation.VERTICAL,
            on_change=lambda v: (
                setattr(body_type_desc, 'text', body_types[v.value]),
                setattr(hp_in,  'value', class_stats[v.value]['hp']),
                setattr(str_in, 'value', class_stats[v.value]['str']),
                setattr(def_in, 'value', class_stats[v.value]['def']),
                setattr(agi_in, 'value', class_stats[v.value]['agi']),
                Widget.NO_EVENT,
            )[-1]
        )

        char_panel.add('name_input', name_input) # , anchor=Panel.Anchor.CENTER
        # char_panel.add('hint_enter', l1.place_below(name_input, 0))
        # char_panel.add('hint_esc', l2.place_right_of(l1, 3))
        char_panel.add('selector_title', selector_title.place_right_of(name_input, 7))
        char_panel.add('name_selector', name_selector.place_below(selector_title, 1))
        char_panel.add('body_type_selector', body_type_selector.place_below(name_input, 4))
        char_panel.add('body_type_desc', body_type_desc.place_right_of(body_type_selector, 10))

        char_panel.fit_to_content()
        char_panel.align(name_selector, Panel.Anchor.RIGHT)
        # char_panel.align(selector_title, Panel.Anchor.RIGHT)

        char_panel.separate(name_input, body_type_selector)
        char_panel.separate(name_input, name_selector)

        about_panel = self.add('about', Panel(0, 0, 0, 0, title='About'))
        about_content = TextBlock(about, w=char_panel.lw, h=4, wrap=False,)
        about_panel.add('text', about_content)
        about_panel.fit_to_content()
        about_panel.place_below(char_panel, 1)

        location_panel = self.add('location', Panel(0, 0, 30, 15, title='Location',))
        loc_label = Label('Choose starting town:')
        town_selector = RadioGroup(items=[ListItem(t) for t in towns], auto_key=True, gap=1)
        location_panel.add('loc_label', loc_label)
        location_panel.add('town_selector', town_selector.place_below(loc_label, 2))
        location_panel.fit_to_content()
        location_panel.place_right_of(char_panel, 2)

        # side.add('a', a)
        # side.add('b', b.place_below(a, 1))
        # side.fit_to_content()
        # side.place_right_of(char_panel, 2)

        stats_panel = self.add('stats', Panel(0, 0, 30, 15, title='Stats'))
        stats_w = 21
        hp_in  = NumberInput(label='HP:',  width=stats_w, value=class_stats['Buff']['hp'],  min_value=1, max_value=999)
        str_in = NumberInput(label='STR:', width=stats_w, value=class_stats['Buff']['str'], min_value=1, max_value=99)
        def_in = NumberInput(label='DEF:', width=stats_w, value=class_stats['Buff']['def'], min_value=1, max_value=99)
        agi_in = NumberInput(label='AGI:', width=stats_w, value=class_stats['Buff']['agi'], min_value=1, max_value=99)
        create = Button('Create', key='C', action=lambda: (
            setattr(state, 'character', Character(
                name=name_input.value,
                body=body_type_selector.value,
                town=town_selector.value,
                hp=hp_in.value, strength=str_in.value,
                defense=def_in.value, agility=agi_in.value,
            )),
            TownScene(self.screen),
        )[-1])
        stats_panel.add('hp',  hp_in)
        stats_panel.add('str', str_in.place_below(hp_in, 0))
        stats_panel.add('def', def_in.place_below(str_in, 0))
        stats_panel.add('int', agi_in.place_below(def_in, 0))
        stats_panel.add('create', create.place_below(agi_in, 1))
        stats_panel.fit_to_content()
        stats_panel.align(create, Panel.Anchor.RIGHT)
        stats_panel.place_below(location_panel, 1)


        foot = self.add('footer', Panel(0,0, about_panel.w + stats_panel.w + 2, 3, pad_x=1, pad_y=0))
        # foot.set_title("Commands", alignment=Panel.Alignment.RIGHT)
        foot.add('text', Label(f'[Tab] Cycle   [↑↓] Move   [Esc] Cancel  {h}'), anchor=Panel.Anchor.LEFT | Panel.Anchor.TOP)
        foot.place_below(about_panel, 1)


        name_input.move_by(dy=1)


        self.center_all()

        
        # self._label_dy = (main.ih // 2) - 2

    # def _render(self, panel: Panel, screen: Screen):
    #     # panel.put_centered(screen, self._label_dy, 'Enter your name:')
    #     # panel.put_centered(screen, panel.ih - 2, )

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT: return self
        if result is Widget.CANCELLED: return TitleScene(self.screen)
        if isinstance(result, Scene): return result  # layout toggle or Create
        return TownScene(self.screen)

    def enter(self):
        super().enter()
        self.load('Creation', clear=True)


from .creation_scene_single import CreationScene_S  # late import
