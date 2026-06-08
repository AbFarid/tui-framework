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
    from .creation_scene_multi import CreationScene_M, premade, towns, body_types, class_stats, about


class CreationScene_S(Scene):

    def __init__(self, screen: Screen):
        super().__init__(screen)

        master = self.add('master', Panel(
            0, 0, screen.width, screen.height,
            header=True,
            footer=True,
        ))

        self.add_command('t', 'Toggle Panel Mode', lambda: (self.save('Creation'), CreationScene_M(self.screen))[-1])
        self.add_command('q', 'Save & Quit', lambda: (self.save(), Widget.CANCELLED)[-1])
        h = self.get_command_hints()

        master.set_header('  Create your brawler')
        master.set_footer(f'  [Tab] Cycle   [↑↓] Move   [Esc] Cancel  {h}')

        main = Panel(0, 0, 2, 2, title='Character', border=False)
        name_input = TextInput(
            x=0, y=0, width=30,
            label='Enter your fighter\'s name:',
            placeholder=choice(premade),
            max_length=20,
            required=True,
            rules=[
                (r'^.{0,2}$', 'At least 3 characters'), # requirement: regex
                (r'[0-9]', 'No numbers allowed'),
                (r'[^A-Za-z0-9 -]', 'No special symbols'),
                (r'^[^A-Z]', 'Must be capitalized'),
            ],
        )
        selector_title = Label('Or choose a fighter:')
        name_selector = List(
            0, 0, 30, 4,
            items=[ListItem(x) for x in premade],
            selectable=True,
            wrap=False,
            on_select=lambda item: (setattr(name_input, 'value', item.value), Widget.NO_EVENT)[-1],
        )
        body_type_desc = TextBlock(w=50, h=5, text=body_types['Buff'])
        body_type_selector = RadioGroup(
            items=list(body_types.keys()),
            auto_key=True,
            gap=1,
            on_change=lambda v: (
                setattr(body_type_desc, 'text', body_types[v.value]),
                setattr(hp_in,  'value', class_stats[v.value]['hp']),
                setattr(str_in, 'value', class_stats[v.value]['str']),
                setattr(def_in, 'value', class_stats[v.value]['def']),
                setattr(agi_in, 'value', class_stats[v.value]['agi']),
                Widget.NO_EVENT,
            )[-1],
        )

        char_title = Label('Character', color='bold')
        main.add('title', char_title)
        main.add('name_input', name_input.place_below(char_title, 1))
        main.add('selector_title', selector_title.place_right_of(name_input, 5))
        main.add('name_selector', name_selector.place_below(selector_title, 1))
        main.add('body_type_selector', body_type_selector.place_below(name_input, 3))
        main.add('body_type_desc', body_type_desc.place_right_of(body_type_selector, 10))
        main.fit_to_content()

        location = Panel(0, 0, 2, 2, title='Location', border=False)
        location_title = Label('Location', color='bold')
        loc_label = Label('Choose starting town:')
        town_selector = RadioGroup(items=[ListItem(t) for t in towns], auto_key=True, gap=1)
        location.add('title', location_title)
        location.add('loc_label', loc_label.place_below(location_title, 1))
        location.add('town_selector', town_selector.place_below(loc_label, 2))
        location.fit_to_content()

        stats = Panel(0, 0, 2, 2, title='Stats', border=False)
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
        stats_title = Label('Stats', color='bold')
        stats.add('title', stats_title)
        stats.add('hp',  hp_in.place_below(stats_title, 1))
        stats.add('str', str_in.place_below(hp_in, 0))
        stats.add('def', def_in.place_below(str_in, 0))
        stats.add('int', agi_in.place_below(def_in, 0))
        stats.add('create', create.place_below(agi_in, 1))
        stats.fit_to_content()
        stats.align(create, Panel.Anchor.RIGHT)

        about_panel = Panel(0, 0, 2, 2, title='About', border=False)
        about_title = Label('About', color='bold')
        about_tb = TextBlock(about, w=main.lw, h=5, wrap=False)
        about_panel.add('title', about_title)
        about_panel.add('text', about_tb.place_below(about_title, 1))
        about_panel.fit_to_content()

        master.align(main, Panel.Anchor.TOP | Panel.Anchor.LEFT)
        location.place_right_of(main, 5)
        stats.place_below(location)
        about_panel.place_below(main)

        master.add('main', main)
        master.add('location', location)
        master.add('about', about_panel)
        master.add('stats', stats)

        master.fit_to_content()
        self.center(master)

        master.separate(main, location)
        master.separate(main, about_panel)
        master.separate(location, stats)

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT: return self
        if result is Widget.CANCELLED: return TitleScene(self.screen)
        if isinstance(result, Scene): return result
        return TownScene(self.screen)

    def enter(self):
        super().enter()
        self.load('Creation', clear=True)


# late import
from .creation_scene_multi import CreationScene_M, premade, towns, body_types, class_stats, about
