from typing import List

import numpy as np
from napari.layers import Layer

from napari_undo_redo.command.base import Command


class MoveCommand(Command):
    def __init__(
        self,
        layer: Layer,
        indices: List[int],
        prev_coordinates: np.ndarray,
        new_coordinates: np.ndarray,
    ) -> None:

        super().__init__()
        self.layer = layer
        self.prev_coordinates = prev_coordinates
        self.new_coordinates = new_coordinates
        self.indices = indices

    def __eq__(self, __o: Command) -> bool:
        if not isinstance(__o, MoveCommand):
            return False

        return (
            (self.indices == __o.indices)
            and (np.array_equal(self.prev_coordinates, __o.prev_coordinates))
            and (np.array_equal(self.new_coordinates, __o.new_coordinates))
        )

    def undo(self):
        """
        For undoing move, we need to set points to there previous coordinates
        using indices that changed
        """
        for i in range(len(self.indices)):
            self.layer.data[self.indices[i]] = self.prev_coordinates[i]

    def redo(self):
        for i in range(len(self.indices)):
            self.layer.data[self.indices[i]] = self.new_coordinates[i]
