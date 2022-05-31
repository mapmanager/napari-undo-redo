from copy import deepcopy

from napari.layers import Layer


class State:
    """
    Represents the state of a napari layer at a particular point in time
    """

    def __init__(self, layer: Layer) -> None:
        """
        creates a state representing the current snapshot of a napari layer.

        Args:
            layer: napari.layers.Layer
                (https://napari.org/api/napari.layers.Layer.html#napari.layers.Layer)
        """
        # we are doing a deepcopy because we don't want the state to be
        # modified whenever the layer is modified.
        # instead we are creating a state with a new layer everytime
        self.layer = deepcopy(layer)

    def get_layer(self) -> Layer:
        """
        returns the napari layer in this state
        """
        return self.layer
