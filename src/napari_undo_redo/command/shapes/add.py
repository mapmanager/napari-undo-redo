from typing import List

import numpy as np
from napari.layers import Layer

from napari_undo_redo.command.base import Command


class AddShapeCommand(Command):
    def __init__(
        self,
        layer: Layer,
        indices_of_added_shapes: List[int],
        added_shapes: List[np.ndarray],
        shape_types: List[str],
    ) -> None:
        """
        Initialize the AddPointCommand instance

        Args:
            layer: napari layer for which we want to undo/redo add operation
            data: list of points that we're added
            indices: indices of added points
        """
        super().__init__()
        self.layer = layer
        self.indices_of_added_shapes = indices_of_added_shapes
        self.added_shapes = added_shapes
        self.shape_types = shape_types

    def __eq__(self, __o: Command) -> bool:
        """
        If a command is not an AddShapeCommand or
        if the data in that command is not the
        same as the current AddShapeCommand object,
        then return False

        This method is used to prevent adding
        the same command to the undo/redo stacks

        Args:
            __o: Any command object
        """
        if not isinstance(__o, AddShapeCommand):
            return False

        # return (
        #     self.indices_of_added_shapes == __o.indices_of_added_shapes
        # ) and (np.array_equal(self.added_shapes, __o.added_shapes))
        return (
            self.indices_of_added_shapes == __o.indices_of_added_shapes
            and self.added_shapes == __o.added_shapes
            and self.shape_types == __o.shape_types
        )

    def undo(self):
        """
        For an Add command, undo implements delete
        This will involve removing the shape that was added before the undo
        """
        # axis 0 for deleting row-wisefrom 2D array
        # print(self.indices_of_added_shapes)
        self.layer.data = np.delete(
            self.layer.data, self.indices_of_added_shapes, 0
        )

        # self.layer.shape_type = np.delete(
        #     self.layer.shape_type, self.indices_of_added_shapes, 0
        # )

    def redo(self):
        """
        redo should simply add data
        """
        self.layer.add(
            self.added_shapes,
            shape_type=self.shape_types,
        )

        """
        for i in range(len(self.indices_of_added_shapes)):
            pprint(f"self.added_shapes[i]: {self.added_shapes[i]}")
            pprint(f"self.shape_types[i]: {self.shape_types[i]}")


            if len(self.layer.data) == 0:
                # Note: this does not work because numpy cannot add array of
                # shape (4,2) to an empty list.
                # self.layer.data.insert(0, self.added_shapes[i])

                # So we set layer data to be an empty numpy array
                # of shape (4,2)
                self.layer.data = [np.empty((4,2), float)]

            if len(self.layer.shape_type) == 0:
                self.layer.shape_type = [self.shape_types[0]]

            index = self.indices_of_added_shapes[i]
            self.layer.data = np.insert(
                self.layer.data,
                index,
                self.added_shapes[i],
                0
            ).tolist()

            self.layer.shape_type[index] = self.shape_types[i]
        """
