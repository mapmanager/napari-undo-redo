from collections import deque

from napari.layers import Layer

from napari_undo_redo.command.base import Command
from napari_undo_redo.command.points.add import AddPointCommand
from napari_undo_redo.command.points.delete import DeletePointCommand
from napari_undo_redo.command.points.move import MovePointCommand

# from _my_logger import logger


class CommandManager:
    """
    It has internal stacks that keeps track of our commands for our:
    1. undo functionality
    2. redo functionality
    """

    def __init__(self, layer: Layer = None) -> None:
        """
        Initialize the undo and redo stacks for a napari layer
        """
        self.layer = layer
        self._in_progress = False
        self.undo_stack = deque()
        self.redo_stack = deque()

    def set_layer(self, layer: Layer) -> None:
        self.layer = layer

    def add_command_to_undo_stack(self, cmd: Command) -> None:
        # compare and if unequal then append
        if not self.undo_stack or cmd != self.undo_stack[-1]:
            self.undo_stack.append(cmd)
        else:
            print("Cannot add same commands to undo stack...")

    def is_operation_in_progress(self) -> bool:
        return self._in_progress

    def undo(self) -> None:
        if self.undo_stack:
            self._in_progress = True
            cmd = self.undo_stack.pop()
            self.redo_stack.append(cmd)
            cmd.undo()
            self._in_progress = False

    def redo(self) -> None:
        if self.redo_stack:
            self._in_progress = True
            cmd = self.redo_stack.pop()
            self.undo_stack.append(cmd)
            cmd.redo()
            self._in_progress = False


def main():
    import napari
    import numpy as np

    viewer = napari.Viewer()
    points_layer = viewer.add_points(
        data=np.array([[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40]]),
        ndim=3,
        name="my points layer",
        size=3,
        face_color="red",
        shown=True,
        features={"f1": "a", "f2": 2},
    )
    # print(f"layer id: {id(points_layer)}")
    print(f"layer id: {points_layer.name}")
    manager = CommandManager(points_layer)
    print(f"Points initially:\n{points_layer.data}")

    # add point
    print("Testing Add Command Undo-Redo....")
    points_layer.data = np.array(
        [[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40], [0, 50, 50]]
    )
    addPoint = AddPointCommand(points_layer, [4], np.array([[0, 50, 50]]))
    manager.add_command_to_undo_stack(addPoint)
    print(f"Points after adding a point:\n{points_layer.data}")

    manager.undo()
    print(f"Points after undo:\n{points_layer.data}")

    manager.redo()
    print(f"Points after redo:\n{points_layer.data}")

    # delete point
    print("Testing Delete Command Undo-Redo....")
    # points_layer.data = np.array(
    #     [[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40]]
    # )
    # delPoint = DeletePointCommand(points_layer, [4], np.array([[0, 50, 50]]))

    points_layer.data = np.array(
        [[0, 10, 10], [0, 20, 20], [0, 40, 40], [0, 50, 50]]
    )
    delPoint = DeletePointCommand(points_layer, [2], np.array([[0, 30, 30]]))

    manager.add_command_to_undo_stack(delPoint)
    print(f"Points after delete a point:\n{points_layer.data}")

    manager.undo()
    print(f"Points after undo:\n{points_layer.data}")

    manager.redo()
    print(f"Points after redo:\n{points_layer.data}")

    # move point
    print("Testing Move Command Undo-Redo....")
    points_layer.data = np.array(
        [[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40], [0, 60, 60]]
    )
    movePoint = MovePointCommand(
        points_layer, [4], np.array([[0, 50, 50]]), np.array([[0, 60, 60]])
    )
    manager.add_command_to_undo_stack(movePoint)
    print(f"Points after moving a point:\n{points_layer.data}")

    manager.undo()
    print(f"Points after undo:\n{points_layer.data}")

    manager.redo()
    print(f"Points after redo:\n{points_layer.data}")


if __name__ == "__main__":
    main()
