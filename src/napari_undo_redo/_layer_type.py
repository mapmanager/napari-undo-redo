from enum import Enum

import napari


class LayerType(Enum):
    NONE = None
    POINTS = napari.layers.points.points.Points
    SHAPES = napari.layers.shapes.shapes.Shapes
