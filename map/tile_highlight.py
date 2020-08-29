from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.widget import Widget


class TileHighlight(Widget):
    def __init__(self, map=None, **kwargs):
        """Highlights the map tile under mouse cursor if any.

        Will attach to provided map argument (a MapView) if present.
        """

        super().__init__(**kwargs)
        self.map = None

        if map:
            self.attach_to(map)

        Window.bind(mouse_pos=self.update)

    def attach_to(self, map):
        """Attach this TileHighlight to a MapView.

        Adds TileHighlight to the MapView scatter children.
        Sets self.map to the map argument.
        Raises AttributeError if called when self.map is already set.
        """
        if self.map:
            raise AttributeError(
                'TileHighlight can only be attached to a single map'
            )

        map.scatter.add_widget(self)
        self.map = map

    def detach_from(self):
        """Detaches this TileHighlight from its MapView.

        Removes TileHighlight from the MapView scatter children.
        Sets self.map to None.
        Raises AttributeError if called when self.map is not set.
        """
        if not self.map:
            raise AttributeError(
                'TileHighlight can only be detached if already attached'
            )

        self.map.scatter.remove_widget(self)
        self.map = None

    def update(self, window, pos):
        """Updates TileHighlight pos/size following mouse position.

        Hides TileHighlight if pos is outside of map.
        Does nothing if TileHighlight is not attached to a map.
        """
        if not self.map:
            return

        map = self.map
        scatter = map.scatter
        pos = scatter.to_widget(*pos)
        tile_coords = map.tile_coords(*pos)

        if not tile_coords:
            self.pos = (0, 0)
            self.size = (0, 0)
            return

        self.pos = map.tile_pos(*tile_coords)
        self.size = map.tile_size


Builder.load_file('map/tile_highlight.kv')
