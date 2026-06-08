from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from ui.scene import Scene
from ui.panel import Panel
from ui.widgets import Widget, Label, TextBlock, List, ListItem, ProgressBar

from .title_scene import TitleScene
from demo.state import state

if TYPE_CHECKING:
    from ui.screen import Screen


TOWN_ART = r"""~         ~~          __
       _T      .,,.    ~--~ ^^
 ^^   // \                    ~
      ][O]    ^^      ,-~ ~
   /''-I_I         _II____
__/_  /   \ ______/ ''   /'\_,__
  | II--'''' \,--:--..,_/,.-{ },
; '/__\,.--';|   |[] .-.| O{ _ }
:' |  | []  -|   ''--:.;[,.'\,/
'  |[]|,.--'' '',   ''-,.    |
  ..    ..-''    ;       ''. '"""

DESC = '''A muddy little town that reeks of ale and bad decisions. The cobbles are cracked, the guards are bored, and every other door leads to a tavern.
'''


class TownScene(Scene):
    def __init__(self, screen: Screen):
        super().__init__(screen)
        c = state.character
        town_name = (c.town.split() or ['Town'])[0]

        master = self.add('master', Panel(
            0, 0, screen.width, screen.height,
            header=True, footer=True,
        ))
        master.set_header(f'  {c.name} · {c.body}')
        master.set_footer('  [↑↓] Move   [Enter] Go   [Esc] Title')

        location = Panel(0, 0, 2, 2, border=False)
        loc_title = Label(town_name, color='bold')
        art = Label(TOWN_ART)
        loc_desc = TextBlock(DESC, w=50, h=5, wrap=False)
        location.add('title', loc_title)
        location.add('art', art.place_below(loc_title, 2))
        location.add('desc', loc_desc.place_below(art, 2))
        location.fit_to_content()
        art.move_by(8)

        whereto = Panel(0, 0, 2, 2, border=False)
        whereto_title = Label('Where to', color='bold')
        destinations = List(
            0, 0, 22, 5,
            items=[
                ListItem('Tavern'),
                ListItem('Shop',       disabled=True),
                ListItem('Inn',        disabled=True),
                ListItem('Blacksmith', disabled=True),
                ListItem('Leave town'),
            ],
            selectable=True,
            wrap=False,
            show_scrollbar=False,
            on_select=lambda item: Widget.CANCELLED if item.value == 'Leave town' else Widget.NO_EVENT,
        )
        whereto.add('title', whereto_title)
        whereto.add('list', destinations.place_below(whereto_title, 1))
        whereto.fit_to_content()

        stats = Panel(0, 0, 2, 2, border=False)
        stats_title = Label('Stats', color='bold')
        hp_bar  = ProgressBar(label='HP:', bar_w=12, value=c.hp, max_value=c.hp)
        xp_bar  = ProgressBar(label='XP:', bar_w=12, value=c.xp, max_value=30)
        str_lbl = Label(f'STR: {c.strength}')
        def_lbl = Label(f'DEF: {c.defense}')
        agi_lbl = Label(f'AGI: {c.agility}')
        gold_lbl  = Label(f'Gold:  {state.gold}')
        teeth_lbl = Label(f'Teeth: {c.teeth}')
        stats.add('title', stats_title)
        stats.add('hp',  hp_bar.place_below(stats_title, 1))
        stats.add('xp',  xp_bar.place_below(hp_bar, 1))
        stats.add('str', str_lbl.place_right_of(hp_bar, 4))
        stats.add('def', def_lbl.place_below(str_lbl, 0))
        stats.add('agi', agi_lbl.place_below(def_lbl, 0))
        stats.add('gold',  gold_lbl.place_right_of(str_lbl, 4))
        stats.add('teeth', teeth_lbl.place_below(gold_lbl, 1))
        stats.fit_to_content()


        inventory = Panel(0, 0, 2, 2, border=False)
        inv_title = Label('Inventory', color='bold')
        inv_list = List(
            0, 0, 22, 5,
            items=[ListItem('Can of Spinach'), ListItem('—'), ListItem('—'), ListItem('—'), ListItem('—')],
            selectable=True,
            show_scrollbar=False,
        )
        inventory.add('title', inv_title)
        inventory.add('list', inv_list.place_below(inv_title, 1))
        inventory.fit_to_content()


        equipment = Panel(0, 0, 2, 2, border=False)
        equip_title = Label('Equipment', color='bold')
        equip_list = List(
            0, 0, 22, 4,
            items=[ListItem('Tattered tunic'), ListItem('Patched trousers'),
                   ListItem('Worn boots'), ListItem('Frayed gloves')],
            selectable=True,
            show_scrollbar=False,
        )
        equipment.add('title', equip_title)
        equipment.add('list', equip_list.place_below(equip_title, 1))
        equipment.fit_to_content()


        log = Panel(0, 0, 2, 2, border=False)
        log_title = Label('Log', color='bold')
        log_text = TextBlock(
            '- You stumbled into Punchester, smelling of the road.\n'
            '- The barkeep eyed your coin purse with professional interest.\n'
            '- Won a scuffle behind the tavern (+12 XP).\n'
            '- Bought a Can of Spinach (-5 gold).\n'
            '- Lost a tooth. Worth it.\n'
            '- A stray cat has decided you are its problem now.',
            w=52, h=10, wrap=False,
        )
        log.add('title', log_title)
        log.add('text', log_text.place_below(log_title, 1))
        log.fit_to_content()


        master.align(location, Panel.Anchor.TOP | Panel.Anchor.LEFT)
        whereto.place_below(location, 0)
        stats.place_right_of(location, 8)
        inventory.place_below(stats, 3)
        equipment.place_right_of(inventory, 5)
        log.place_below(inventory, 3)

        master.add('location', location)
        master.add('whereto', whereto)
        master.add('stats', stats)
        master.add('inventory', inventory)
        master.add('equipment', equipment)
        master.add('log', log)

        master.fit_to_content()
        self.center(master)

        master.separate(location, stats)
        master.separate(stats, inventory)
        master.separate(inventory, log)
        master.separate(inventory, equipment)

    def handle_key(self, key) -> Optional[Scene]:
        result = self.route_key(key)
        if result is Widget.NO_EVENT: return self
        if result is Widget.CANCELLED: return TitleScene(self.screen)
        return self
