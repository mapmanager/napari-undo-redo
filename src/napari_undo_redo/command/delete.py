from typing import List

import numpy as np
from napari.layers import Layer

from napari_undo_redo.command.base import Command


class DeleteCommand(Command):
    def __init__(
        self,
        layer: Layer,
        indices_of_deleted_points: List[int],
        deleted_points: np.ndarray,
    ) -> None:
        super().__init__()
        self.layer = layer
        self.indices_of_deleted_points = indices_of_deleted_points
        self.deleted_points = deleted_points

    def __eq__(self, __o: Command) -> bool:
        if not isinstance(__o, DeleteCommand):
            return False

        return (
            self.indices_of_deleted_points == __o.indices_of_deleted_points
        ) and (np.array_equal(self.deleted_points, __o.deleted_points))

    def undo(self):
        """
        Undo of DeleteCommand should be an add operation
        """
        for i in range(len(self.indices_of_deleted_points)):
            self.layer.data = np.insert(
                self.layer.data,
                self.indices_of_deleted_points[i],
                self.deleted_points[i],
                0,
            )

    def redo(self):
        """
        For an DeleteCommand, redo implements delete
        This will involve removing the point that
        was added back because of the undo
        """
        # axis 0 for deleting row-wisefrom 2D array
        self.layer.data = np.delete(
            self.layer.data, self.indices_of_deleted_points, 0
        )
