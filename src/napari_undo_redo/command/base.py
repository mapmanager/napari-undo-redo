"""
# TODO:
needs to be more granular in the future,
to support different layers like Points, Shapes
eg: Having AddShapeCommand, DeleteShapeCommand...
"""

from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass
