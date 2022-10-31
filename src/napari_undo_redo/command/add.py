from typing import List

import numpy as np
from napari.layers import Layer

from napari_undo_redo.command.base import Command


class AddCommand(Command):
    def __init__(
        self,
        layer: Layer,
        indices_of_added_points: List[int],
        added_points: np.ndarray,
    ) -> None:
        """
        Initialize the AddCommand instance

        Args:
            layer: napari layer for which we want to undo/redo add operation
            data: list of points that we're added
            indices: indices of added points
        """
        super().__init__()
        self.layer = layer
        self.indices_of_added_points = indices_of_added_points
        self.added_points = added_points

    def __eq__(self, __o: Command) -> bool:
        """
        If a command is not an AddCommand or
        if the data in that command is not the
        same as the current AddCommand object,
        then return False

        This method is used to prevent adding
        the same command to the undo/redo stacks

        Args:
            __o: Any command object
        """
        if not isinstance(__o, AddCommand):
            return False

        return (
            self.indices_of_added_points == __o.indices_of_added_points
        ) and (np.array_equal(self.added_points, __o.added_points))

    def undo(self):
        """
        For an Add command, undo implements delete
        This will involve removing the point that was added before the undo
        """
        # axis 0 for deleting row-wisefrom 2D array
        # print(self.indices_of_added_points)
        self.layer.data = np.delete(
            self.layer.data, self.indices_of_added_points, 0
        )

    def redo(self):
        """
        redo should simply add data
        """
        for i in range(len(self.indices_of_added_points)):
            self.layer.data = np.insert(
                self.layer.data,
                self.indices_of_added_points[i],
                self.added_points[i],
                0,
            )
