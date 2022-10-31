import numpy as np
from napari.layers import Layer

from napari_undo_redo._my_logger import logger
from napari_undo_redo.command.base import Command


class SymbolChangeCommand(Command):
    def __init__(
        self,
        layer: Layer,
        prev_symbol: str,
        new_symbol: str,
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
        self.prev_symbol = prev_symbol
        self.new_symbol = new_symbol

    def __eq__(self, __o: Command) -> bool:
        if not isinstance(__o, SymbolChangeCommand):
            return False

        return (np.array_equal(self.prev_symbol, __o.prev_symbol)) and (
            np.array_equal(self.new_symbol, __o.new_symbol)
        )

    def undo(self):
        """
        For undoing symbol change,
        we need to set a point's symbol to its previous symbol
        """
        logger.info(f"Before: {self.layer.symbol}")
        self.layer.symbol = self.prev_symbol
        logger.info(f"After: {self.layer.symbol}")
        # self.layer.refresh()

    def redo(self):
        logger.info(f"Before: {self.layer.symbol}")
        self.layer.symbol = self.new_symbol
        logger.info(f"After: {self.layer.symbol}")
        # self.layer.refresh()
