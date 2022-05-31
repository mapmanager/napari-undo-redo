from caretaker import CareTaker
from napari.layers import Layer
from originator import Originator


class UndoPlugin:
    def __init__(self, layer: Layer) -> None:
        self.layer = layer
        self.originator = Originator(layer)
        self.caretaker = CareTaker()
        self.savedStates = 0
        self.currentStateIdx = -1

    def save_state(self, layer: Layer) -> None:
        """
        1. Save the current layer snapshot in the originator
        2. Convert this snapshot into State
        3. Ask the caretaker to store this State in its list of states
        4. Increment the number of savedStates by 1
        5. Increment current state Idx to make it point to most recent state
        """
        self.originator.set_layer(layer)
        state = self.originator.store_in_state()
        self.caretaker.add_state(state)
        self.savedStates += 1
        self.currentStateIdx += 1

    def undo(self) -> Layer:
        """
        0. Cannot undo at currentStateIdx 0 since that is the initial state
        1. Decrement the currentStateIdx to the previous index
            (since that state will become the most recent state after undo)
        2. Get the state at that index
        3. Get the layer at that state
        4. return the layer
        """
        if self.currentStateIdx >= 1:
            self.currentStateIdx -= 1
            previous_state = self.caretaker.get_state(self.currentStateIdx)
            layer_at_previous_state = self.originator.restore_from_state(
                previous_state
            )
            self.layer = layer_at_previous_state
            return layer_at_previous_state
        else:
            # disable the undo button
            print("undo not allowed")
            return None

    def redo(self) -> Layer:
        """
        0. Cannot redo if currentStateIdx is at the last index
            -> because we are already at the most recent state
        1. Increment the currentStateIdx to the next index
            (since that state will become the most recent state after redo)
        2. Get the state at that index
        3. Get the layer at that state
        4. return the layer
        """
        if (
            self.savedStates - 1
        ) > self.currentStateIdx:  # revisit this condition to allow redo
            self.currentStateIdx += 1
            next_state = self.caretaker.get_state(self.currentStateIdx)
            layer_at_next_state = self.originator.restore_from_state(
                next_state
            )
            self.layer = layer_at_next_state
            return layer_at_next_state
        else:
            # disable the redo button
            print("redo not available")
            return None
