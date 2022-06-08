from typing import List

import numpy as np
from base import Command
from napari.layers import Layer


class AddCommand(Command):
    def __init__(
        self, layer: Layer, indices: List[int], data: np.ndarray
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
        self.indices = indices
        self.data = data

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

        return (self.indices == __o.indices) and (
            np.array_equal(self.data, __o.data)
        )

    def undo(self):
        """
        For an Add command, undo implements delete
        This will involve removing the point that was added before the undo
        """
        # axis 0 for deleting row-wisefrom 2D array
        print(self.indices)
        self.layer.data = np.delete(self.layer.data, self.indices, 0)

    def redo(self):
        """
        redo should simply add data
        """
        for i in range(len(self.indices)):
            self.layer.data = np.insert(
                self.layer.data, self.indices[i], self.data[i], 0
            )
