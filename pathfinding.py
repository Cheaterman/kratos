from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.widget import Widget

from map import MapView


Config.remove_option('input', '%(name)s')
Config.set('input', 'mouse', 'mouse,disable_multitouch')


class TileHighlight(Widget):
    pass


class PathFinding(App):
    tile_highlight = ObjectProperty()

    startpoint = NumericProperty(None, allownone=True)
    endpoint = NumericProperty(None, allownone=True)
    blocks = ListProperty()

    button_map = {
        'left': 'startpoint',
        'right': 'endpoint',
    }

    def build(self):
        self.map = map = self.root.map
        map.bind(on_touch_down=lambda _, touch: self.handle_buttons(touch))
        self.tile_highlight = tile_highlight = TileHighlight()
        map.scatter.add_widget(tile_highlight)
        self.bind(
            startpoint=self.update_pathfinding,
            endpoint=self.update_pathfinding,
            blocks=self.update_pathfinding,
        )
        Window.bind(mouse_pos=self.update_tile_highlight)

    def update_tile_highlight(self, window, pos):
        """Updates tile_highlight widget pos/size following mouse pos.

        Hides tile_highlight widget if mouse pos is outside of map.
        """
        map = self.map
        scatter = map.scatter
        pos = scatter.to_widget(*pos)
        tile_coords = map.tile_coords(*pos)
        tile_highlight = self.tile_highlight

        if not tile_coords:
            tile_highlight.pos = (0, 0)
            tile_highlight.size = (0, 0)
            return

        tile_highlight.pos = map.tile_pos(*tile_coords)
        tile_highlight.size = map.tile_size

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
        previous_index = getattr(self, attribute)

        if previous_index == index:
            return

        setattr(self, attribute, index)

        if previous_index is not None:
            self.update_tile_color(previous_index)

        self.update_tile_color(index)

    def update_tile_color(self, tile_index):
        """Updates color for tile at tile_index according to start/endpoint.

        Takes blocks into account.
        """
        map, startpoint, endpoint, blocks = (
            self.map, self.startpoint, self.endpoint, self.blocks
        )
        color = (
            (1, 1, 0, 1) if startpoint == endpoint == tile_index
            else (0, 1, 0, 1) if startpoint == tile_index
            else (1, 0, 0, 1) if endpoint == tile_index
            else (.5, .5, .5, 1) if tile_index in blocks
            else (0, 0, 0, 0)
        )
        map.set_tile_at(tile_index, color=color)


if __name__ == '__main__':
    PathFinding().run()
