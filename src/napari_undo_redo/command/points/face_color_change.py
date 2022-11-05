from typing import List

import numpy as np
from napari.layers import Layer

from napari_undo_redo._my_logger import logger
from napari_undo_redo.command.base import Command


class FaceColorChangeCommand(Command):
    def __init__(
        self,
        layer: Layer,
        prev_face_color: np.array,
        indices: List[int],
        prev_colors: np.array,
        new_color: np.array,
    ) -> None:

        super().__init__()
        self.layer = layer
        self.prev_face_color = prev_face_color
        self.indices = indices
        self.prev_colors = prev_colors
        self.new_color = new_color

    def __eq__(self, __o: Command) -> bool:
        if not isinstance(__o, FaceColorChangeCommand):
            return False

        return (
            (self.indices == __o.indices)
            and (np.array_equal(self.prev_face_color, __o.prev_face_color))
            and (np.array_equal(self.prev_colors, __o.prev_colors))
            and (np.array_equal(self.new_color, __o.new_color))
        )

    def undo(self):
        """
        For undoing move, we need to set points to their previous coordinates
        using indices that changed
        """
        layer_colors = self.layer._face.colors
        j = 0
        for i in self.indices:
            logger.info(f"changing color for point at index: {i}")
            layer_colors[i] = self.prev_colors[j]
            j += 1
        self.layer._face.current_color = self.prev_face_color
        self.layer.refresh()

    def redo(self):
        layer_colors = self.layer._face.colors
        for i in self.indices:
            layer_colors[i] = self.new_color
        self.layer._face.current_color = self.new_color
        self.layer.refresh()
