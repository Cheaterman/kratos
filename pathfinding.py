from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.properties import (
    ListProperty,
    NumericProperty,
)

from map.tile_highlight import TileHighlight


Config.remove_option('input', '%(name)s')
Config.set('input', 'mouse', 'mouse,disable_multitouch')


def mix_colors(color_1, color_2):
    """A _very_ naive color mixer (add + clamp for each channel)."""
    return tuple(
        min(1.0, c1 + c2) for c1, c2 in zip(color_1, color_2)
    )


class PathFinding(App):
    startpoint = NumericProperty(None, allownone=True)
    endpoint = NumericProperty(None, allownone=True)
    blocks = ListProperty()

    button_map = {
        'left': 'startpoint',
        'right': 'endpoint',
        'middle': 'block',
    }

    tile_colors = {
        'startpoint': (0, 1, 0, 1),
        'endpoint': (1, 0, 0, 1),
        'block': (.5, .5, .5, 1),
    }

    def build(self):
        self.map = map = self.root.map
        map.bind(on_touch_down=lambda _, touch: self.handle_buttons(touch))
        TileHighlight(map=map)
        self.bind(
            startpoint=self.update_pathfinding,
            endpoint=self.update_pathfinding,
            blocks=self.update_pathfinding,
        )
        Window.bind(on_keyboard=self.handle_keyboard)

    def handle_keyboard(self, _, key, scancode, codepoint, modifiers):
        if key == 103:  # g
            self.map.grid = not self.map.grid

    def update_pathfinding(self, *args):
        """Calculates shortest path between startpoint and endpoint.

        Displays result on map as colors if any path was found.
        """
        pass

    def handle_buttons(self, touch):
        """Sets startpoint/endpoint if touch.button is in button_map.

        Takes touch.pos and scatter.pos into account, and does nothing if the
        touch is outside the map or the tile under the cursor already has that
        attribute.
        """
        if 'button' not in touch.profile:
            return

        button = touch.button

        if button not in self.button_map:
            return

        map = self.map
        map_model = map.map
        tile_coords = map.tile_coords(*map.scatter.to_widget(*touch.pos))

        if not tile_coords:
            return

        index = tile_coords[1] * map_model.cols + tile_coords[0]
        attribute = self.button_map[button]
        extra_update_index = None

        if attribute == 'startpoint':
            if self.startpoint == index:
                self.startpoint = None
            else:
                extra_update_index = self.startpoint
                self.startpoint = index

        elif attribute == 'endpoint':
            if self.endpoint == index:
                self.endpoint = None
            else:
                extra_update_index = self.endpoint
                self.endpoint = index

        elif attribute == 'block':
            if index in self.blocks:
                self.blocks.remove(index)
            else:
                self.blocks.append(index)

        if extra_update_index is not None:
            self.update_tile_color(extra_update_index)

        self.update_tile_color(index)

    def update_tile_color(self, tile_index):
        """Updates color for tile at tile_index according to start/endpoint.

        Takes blocks into account.
        """
        color = (0, 0, 0, 0)

        if tile_index == self.startpoint:
            color = mix_colors(color, self.tile_colors['startpoint'])

        if tile_index == self.endpoint:
            color = mix_colors(color, self.tile_colors['endpoint'])

        if tile_index in self.blocks:
            color = mix_colors(color, self.tile_colors['block'])

        self.map.set_tile_at(tile_index, color=color)


if __name__ == '__main__':
    PathFinding().run()
