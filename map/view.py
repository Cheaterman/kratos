from kivy.core.window import Window
from kivy.graphics import Color, InstructionGroup, Line
from kivy.graphics.transformation import Matrix
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ListProperty,
    ObjectProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget


class MapView(FloatLayout):
    map = ObjectProperty()
    """The Map object that will be drawn."""

    scatter = ObjectProperty()
    """Internal scatter object, handles visual translation and scaling.

    Useful to transform coordinates from screen space to world space, eg.
    map.scatter.to_widget(*pos), or to draw widgets on the map.
    """

    tile_size = (50, 50)
    """Size in pixels to render each tile at.

    (currently arbitrary - should be based on actual tilemap resolution)
    """

    grid = BooleanProperty(False)
    """Whether or not to draw tile boundaries on map as a grid.

    Defaults to False.
    """

    _tile_data = ListProperty()
    """Internal tile data, should be accessed through get/set_tile_at().

    This is fed directly into RecycleView.data for rendering.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._grid_instructions = None

    def on_map(self, _, map):
        """Creates tile data according to assigned map."""
        self._tile_data = [
            {
                'color': (0, 0, 0, 0),
                'size': self.tile_size,
            }
            for _ in range(map.rows * map.cols)
        ]
        if self._grid_instructions:
            # Discard pre-computed results
            self._grid_instructions = None

    def _build_grid(self):
        """Creates grid draw instructions according to current map."""
        map = self.map
        tile_size = self.tile_size
        grid_instructions = InstructionGroup()
        grid_instructions.add(Color())

        for x in range(0, map.cols * tile_size[0] + 1, tile_size[0]):
            grid_instructions.add(Line(points=(
                x + .5, .5, x + .5, map.rows * tile_size[1] + .5
            )))

        for y in range(0, map.rows * tile_size[1] + 1, tile_size[1]):
            grid_instructions.add(Line(points=(
                .5, y + .5, map.cols * tile_size[0] + .5, y + .5
            )))

        self._grid_instructions = grid_instructions

    def on_grid(self, _, grid):
        """Adds and removes grid draw instructions to/from internal scatter.

        Will create grid draw instructions if required.
        """
        canvas = self.scatter.canvas

        if grid:
            if not self._grid_instructions:
                self._build_grid()

            canvas.add(self._grid_instructions)

        elif self._grid_instructions:
            canvas.remove(self._grid_instructions)

    def tile_coords(self, x, y):
        """Returns tile coordinates for tile under pixel (x, y).

        Returns None if (x, y) isn't inside the map.
        """
        x, y = int(x), int(y)
        map = self.map
        cols, rows = map.cols, map.rows
        max_x, max_y = (
            cols * self.tile_size[0],
            rows * self.tile_size[1],
        )

        if not (
            0 < x < max_x
        ) or not (
            0 < y < max_y
        ):
            return None

        col = int(x / max_x * cols)
        row = int((max_y - y - 1) / max_y * rows)
        return col, row

    def tile_pos(self, x, y):
        """Returns bottom-left pixel position for tile at (x, y).

        Returns None if (x, y) isn't inside the map.
        """
        map = self.map
        cols, rows = map.cols, map.rows

        if not (
            0 <= x < cols
        ) or not (
            0 <= y < rows
        ):
            return None

        max_x, max_y = (
            cols * self.tile_size[0],
            rows * self.tile_size[1],
        )

        return (
            x * max_x / cols,
            max_y - (y + 1)  # y coord from top, pos from bottom
            * max_y / rows,
        )

    def get_tile_at(self, tile_index):
        """Returns tile data for tile at index tile_index.

        Raises IndexError if tile_index isn't inside the map.
        """
        if not (0 <= tile_index < len(self._tile_data)):
            raise IndexError(f'Tile index {tile_index} is outside of map')

        return self._tile_data[tile_index]

    def set_tile_at(self, tile_index, **kwargs):
        """Update tile data for tile at index tile_index with kwargs.

        Raises IndexError if tile_index isn't inside the map.
        """
        if not (0 <= tile_index < len(self._tile_data)):
            raise IndexError(f'Tile index {tile_index} is outside of map')

        tile = self._tile_data[tile_index].copy()
        tile.update(kwargs)
        self._tile_data[tile_index] = tile

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


Builder.load_file('map/view.kv')
