from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget


Config.remove_option('input', '%(name)s')
Config.set('input', 'mouse', 'mouse,disable_multitouch')


class Map(FloatLayout):
    cols = NumericProperty()
    rows = NumericProperty()

    tile_data = ListProperty()
    scatter = ObjectProperty()
    tile_highlight = ObjectProperty()

    startpoint = NumericProperty(None, allownone=True)
    endpoint = NumericProperty(None, allownone=True)

    button_map = {
        'left': 'startpoint',
        'right': 'endpoint',
    }

    tile_size = (50, 50)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_tiles_trigger = trigger = Clock.create_trigger(
            self.create_tiles
        )
        self.bind(
            cols=trigger,
            rows=trigger,
            startpoint=self.update_pathfinding,
            endpoint=self.update_pathfinding,
        )
        Window.bind(mouse_pos=self.update_tile_highlight)

    def update_tile_highlight(self, window, pos):
        pos = self.scatter.to_widget(*pos)
        tile_coords = self.tile_coords(*pos)
        self.tile_highlight.index = (
            tile_coords[1] * self.cols + tile_coords[0]
        ) if tile_coords else None

    def tile_coords(self, x, y):
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
        coords = self.tile_coords(x, y)

        if not coords:
            return None

        return self.tile_data[coords[1] * self.cols + coords[0]]

    def create_tiles(self, *args):
        self.tile_data = [
            {
                'startpoint': False,
                'endpoint': False,
                'block': False,
                'size': self.tile_size,
            }
            for _ in range(self.rows * self.cols)
        ]

    def update_pathfinding(self, *args):
        pass


class TileHighlight(Widget):
    index = NumericProperty(allownone=True)
    map = ObjectProperty()

    def on_index(self, _, index):
        if index is None:
            self.pos = 0, 0
            self.size = 0, 0
            return

        map = self.map
        self.size = map.tile_size
        x, y = index % map.cols, index // map.cols
        self.pos = map.tile_pos(x, y)


class MapGridLayout(RecycleGridLayout):
    map = ObjectProperty()

    def on_touch_down(self, touch):
        if 'button' not in touch.profile:
            return super().on_touch_down(touch)

        if touch.button.startswith('scroll'):
            scatter = self.scatter
            scale_factor = min(scatter.scale_max, max(
                scatter.scale_min,
                scatter.scale + (
                    .1 if touch.button.endswith('down') else -.1
                )
            )) / scatter.scale
            scatter.apply_transform(
                Matrix().scale(*(scale_factor for xyz in 'xyz')),
                anchor=Window.center,
            )
            return True

        map = self.map

        if touch.button in map.button_map:
            tile_coords = map.tile_coords(*touch.pos)

            if not tile_coords:
                return

            index = tile_coords[1] * map.cols + tile_coords[0]
            attribute = map.button_map[touch.button]
            tile_data = map.tile_data
            new_tile = tile_data[index].copy()

            if new_tile[attribute]:
                return

            current_index = getattr(map, attribute)

            if current_index is not None:
                tile_data[current_index][attribute] = False

            setattr(map, attribute, index)

            new_tile[attribute] = True
            tile_data[index] = new_tile

        return super().on_touch_down(touch)


class Tile(RecycleDataViewBehavior, FloatLayout):
    startpoint = BooleanProperty(False)
    endpoint = BooleanProperty(False)
    block = BooleanProperty(False)
    color = ColorProperty()

    index = NumericProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)


class PathFinding(App):
    pass


if __name__ == '__main__':
    PathFinding().run()
