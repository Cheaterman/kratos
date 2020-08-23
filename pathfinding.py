from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix
from kivy.properties import (
    ColorProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget


Config.remove_option('input', '%(name)s')
Config.set('input', 'mouse', 'mouse,disable_multitouch')


class Map(FloatLayout):
    cols = NumericProperty()
    rows = NumericProperty()

    tile_data = ListProperty()
    scatter = ObjectProperty()

    tile_size = (50, 50)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_tiles_trigger = trigger = Clock.create_trigger(
            self.create_tiles
        )
        self.bind(
            cols=trigger,
            rows=trigger,
        )

    def tile_coords(self, x, y):
        """Returns tile coordinates for tile under pixel (x, y).

        Returns None if (x, y) isn't inside the map.
        """
        x, y = int(x), int(y)
        max_x, max_y = (
            self.cols * self.tile_size[0],
            self.rows * self.tile_size[1],
        )

        if not (
            0 < x < max_x
        ) or not (
            0 < y < max_y
        ):
            return None

        col = int(x / max_x * self.cols)
        row = int((max_y - y - 1) / max_y * self.rows)
        return col, row

    def tile_pos(self, x, y):
        """Returns bottom-left pixel position for tile at (x, y).

        Returns None if (x, y) isn't inside the map.
        """
        if not (
            0 <= x < self.cols
        ) or not (
            0 <= y < self.rows
        ):
            return None

        max_x, max_y = (
            self.cols * self.tile_size[0],
            self.rows * self.tile_size[1],
        )

        return (
            x * max_x / self.cols,
            max_y - (y + 1)  # y coord from top, pos from bottom
            * max_y / self.rows,
        )

    def get_tile_at(self, x, y):
        """Returns tile data for tile under pixel (x, y).

        Returns None if (x, y) isn't inside the map.
        """
        coords = self.tile_coords(x, y)

        if not coords:
            return None

        return self.tile_data[coords[1] * self.cols + coords[0]]

    def create_tiles(self, *args):
        """Creates dummy tile data for map according to cols/rows."""
        self.tile_data = [
            {
                'color': (0, 0, 0, 0),
                'size': self.tile_size,
            }
            for _ in range(self.rows * self.cols)
        ]

    def handle_zoom(self, touch):
        """Zooms scatter in/out if touch.button is scrollup/down.

        Zooms from the center of the window and takes scatter.scale_min/max
        into account.
        Returns True if the touch was handled, None otherwise.
        """
        button = touch.button

        if not button.startswith('scroll') or button[6:] not in ('up', 'down'):
            return

        scatter = self.scatter
        scale_factor = min(scatter.scale_max, max(
            scatter.scale_min,
            scatter.scale + (
                .1 if button.endswith('down') else -.1
            )
        )) / scatter.scale
        scatter.apply_transform(
            Matrix().scale(*(scale_factor for xyz in 'xyz')),
            anchor=Window.center,
        )
        return True

    def on_touch_down(self, touch):
        if 'button' in touch.profile:
            if self.handle_zoom(touch):
                return True

        return super().on_touch_down(touch)


class Tile(Widget):
    color = ColorProperty()


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
        tile_coords = map.tile_coords(*map.scatter.to_widget(*touch.pos))

        if not tile_coords:
            return

        index = tile_coords[1] * map.cols + tile_coords[0]
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
        tile_data = self.map.tile_data
        tile = tile_data[tile_index].copy()
        tile['color'] = (
            (1, 1, 0, 1) if self.startpoint == self.endpoint == tile_index
            else (0, 1, 0, 1) if self.startpoint == tile_index
            else (1, 0, 0, 1) if self.endpoint == tile_index
            else (.5, .5, .5, 1) if tile_index in self.blocks
            else (0, 0, 0, 0)
        )
        tile_data[tile_index] = tile


if __name__ == '__main__':
    PathFinding().run()
