from .state import State


class CareTaker:
    """
    It is a collection of states.
    Each time an operation(add, delete, move) is done in a napari layer, the
    caretaker saves the current state of the layer.
    """

    def __init__(self) -> None:
        """
        initializes CareTaker with an empty list of states
        states: List[State]
        """
        self.states = []

    def add_state(self, state: State) -> None:
        """
        add the current state of the napari layer

        Args:
            state: State
        """
        self.states.append(state)

    def get_state(self, index: int) -> State:
        """
        return the state at a given index

        Args:
            index: int
        """
        return self.states[index]
