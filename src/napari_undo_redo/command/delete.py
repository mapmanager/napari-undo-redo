from typing import List

import numpy as np
from base import Command
from napari.layers import Layer


class DeleteCommand(Command):
    def __init__(
        self, layer: Layer, indices: List[int], data: np.ndarray
    ) -> None:
        super().__init__()
        self.layer = layer
        self.indices = indices
        self.data = data

    def __eq__(self, __o: Command) -> bool:
        if not isinstance(__o, DeleteCommand):
            return False

        return (self.indices == __o.indices) and (
            np.array_equal(self.data, __o.data)
        )

    def undo(self):
        """
        Undo of DeleteCommand should be an add operation
        """
        for i in range(len(self.indices)):
            self.layer.data = np.insert(
                self.layer.data, self.indices[i], self.data[i], 0
            )

    def redo(self):
        """
        For an DeleteCommand, redo implements delete
        This will involve removing the point that
        was added back because of the undo
        """
        # axis 0 for deleting row-wisefrom 2D array
        self.layer.data = np.delete(self.layer.data, self.indices, 0)
