from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior


Config.remove_option('input', '%(name)s')
Config.set('input', 'mouse', 'mouse,disable_multitouch')


class Map(FloatLayout):
    cols = NumericProperty()
    rows = NumericProperty()

    tile_data = ListProperty()
    tile_container = ObjectProperty()

    startpoint = NumericProperty(-1)
    endpoint = NumericProperty(-1)

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

    def create_tiles(self, *args):
        self.tile_data = tile_data = [
            {
                'index': index,
                'startpoint': False,
                'endpoint': False,
                'block': False,
                'map': self,
            }
            for index in range(self.rows * self.cols)
        ]

        if self.tile_container:
            self.tile_container.clear_widgets()

            for data in tile_data:
                self.tile_container.add_widget(Tile(**data))

    def update_tiles(self, *args):
        data_length = len(self.tile_data)

        for index, data in enumerate(self.tile_data):
            target = self.tile_container.children[data_length - index - 1]

            for attribute, value in data.items():
                setattr(
                    target,
                    attribute,
                    value
                )

    def update_pathfinding(self, *args):
        pass


class MapGridLayout(GridLayout):
    map = ObjectProperty()

    def handle_touch(self, index, touch):
        if 'button' in touch.profile:
            data = self.map.tile_data

            for button, attribute in self.map.button_map.items():
                if(
                    touch.button == button
                    and not data[index][attribute]
                ):
                    current_point = getattr(self.map, attribute)

                    if current_point != -1:
                        data[current_point][attribute] = False
                        
                    setattr(self.map, attribute, index)

                    data[index][attribute] = True

                    self.map.update_tiles()

                    # XXX: Should be enabled but prevents scatter interaction
                    #return True

    def on_touch_down(self, touch):
        if(
            'button' in touch.profile
            and touch.button.startswith('scroll')
        ):
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

        return super().on_touch_down(touch)


class Tile(RecycleDataViewBehavior, FloatLayout):
    map = ObjectProperty()

    index = NumericProperty()
    startpoint = BooleanProperty(False)
    endpoint = BooleanProperty(False)
    block = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return self.parent.handle_touch(self.index, touch)


class PathFinding(App):
    pass


if __name__ == '__main__':
    PathFinding().run()
