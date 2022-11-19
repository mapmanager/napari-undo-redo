from typing import List

import numpy as np
from napari.layers import Layer

from napari_undo_redo._my_logger import logger
from napari_undo_redo.command.base import Command


class DeleteShapeCommand(Command):
    def __init__(
        self,
        layer: Layer,
        indices_of_deleted_shapes: List[int],
        deleted_shapes: List[np.ndarray],
        shape_types: List[str],
    ) -> None:
        """
        Initialize the DeleteShapeCommand instance

        Args:
            layer: napari layer for which we want to undo/redo add operation
            deleted_shapes: list of shapes that were deleted
            indices_of_deleted_shapes: indices of deleted shapes
        """
        super().__init__()
        self.layer = layer
        self.indices_of_deleted_shapes = indices_of_deleted_shapes
        self.deleted_shapes = deleted_shapes
        self.shape_types = shape_types

    def __eq__(self, __o: Command) -> bool:
        """
        If a command is not an DeleteShapeCommand or
        if the data in that command is not the
        same as the current DeleteShapeCommand object,
        then return False

        This method is used to prevent adding
        the same command to the undo/redo stacks

        Args:
            __o: Any command object
        """
        if not isinstance(__o, DeleteShapeCommand):
            return False

        # return (
        #     self.indices_of_added_shapes == __o.indices_of_added_shapes
        # ) and (np.array_equal(self.added_shapes, __o.added_shapes))
        return (
            self.indices_of_deleted_shapes == __o.indices_of_deleted_shapes
            and self.deleted_shapes == __o.deleted_shapes
            and self.shape_types == __o.shape_types
        )

    def undo(self):
        """
        For a DeleteShapeCommand, undo implements add
        This will involve adding the shape that was deleted before the undo
        The shapes are always added at the end, i.e. as the most recent shape
        """
        logger.info(
            f"Adding {len(self.indices_of_deleted_shapes)} shapes to the end"
        )
        logger.info(f"Before undo, layer shape type: {self.layer.shape_type}")
        self.layer.add(
            self.deleted_shapes,
            shape_type=self.shape_types,
        )
        logger.info(f"After undo, layer shape type: {self.layer.shape_type}")

    def redo(self):
        """
        redo should delete the shape and its corresponding shape type
        that was added back by the undo operation
        """
        logger.info(
            f"Deleting the last {len(self.indices_of_deleted_shapes)} shapes"
        )
        logger.info(f"Before redo, layer shape type: {self.layer.shape_type}")
        self.layer.data = self.layer.data[
            : -len(self.indices_of_deleted_shapes)
        ]

        # The following line also deletes data from self.layer.data,
        # causing double deletion
        # The line above also updates self.layer.shape_type
        # self.layer.shape_type = \
        # self.layer.shape_type[:-len(self.indices_of_deleted_shapes)]

        logger.info(f"After redo, layer shape type: {self.layer.shape_type}")
