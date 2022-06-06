from copy import deepcopy

from napari.layers import Layer, Points, Shapes


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
        # self.layer = deepcopy(layer) # Getting this error:
        # "NotImplementedError: object proxy must define __deepcopy__()"

        # Pickling layer to bytes as a workaround because deepcopy doesn't work
        # Doesn' work, getting this error:
        # "TypeError: cannot pickle 'generator' object"
        # self.layer = pickle.dumps(layer)

        if isinstance(layer, Points):
            print("creating points layer state")
            self.layer = Points(data=deepcopy(layer.data))
        elif isinstance(layer, Shapes):
            print("creating shapes layer state")
            self.layer = Shapes(data=deepcopy(layer.data))

    def get_layer(self) -> Layer:
        """
        returns the napari layer in this state
        """
        return self.layer
        # return pickle.loads(self.layer)
