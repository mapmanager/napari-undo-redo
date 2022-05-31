from napari.layers import Layer
from state import State


class Originator:
    """
    - Creates state of the current napari layer
    - Saves the current state of the layer
    """

    # def __init__(self) -> None:
    #     self.layer = None
    def __init__(self, layer: Layer) -> None:
        self.layer = layer

    def set_layer(self, layer: Layer) -> None:
        self.layer = layer

    def store_in_state(self) -> State:
        return State(self.layer)

    def restore_from_state(self, state: State) -> Layer:
        self.layer = state.get_layer()
        return self.layer
