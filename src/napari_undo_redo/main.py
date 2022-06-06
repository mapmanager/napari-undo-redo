import napari
import numpy as np

from .plugin import UndoPlugin

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

plugin = UndoPlugin(points_layer)
plugin.save_state(points_layer)
print(f"initial:\n{points_layer.data}\n")

# simulate adding point
points_layer.data = np.array(
    [[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40], [0, 50, 50]]
)
plugin.save_state(points_layer)

# undo
print(f"after adding point:\n{points_layer.data}\n")
layer_after_undo = plugin.undo()
points_layer = layer_after_undo
print(f"after undo:\n{points_layer.data}\n")

# redo
layer_after_redo = plugin.redo()
points_layer = layer_after_redo
print(f"after redo:\n{points_layer.data}\n")

napari.run()
