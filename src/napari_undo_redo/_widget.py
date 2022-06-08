"""
BUGS:
    1. when the plugin is loaded and a new layer is added,
    then napari fails at `self.layer.events.data.connect(self.save_state)`
    with the error "AttributeError: 'EmitterGroup' object has no attribute
    'data'" because the event has no attribute data. The event is of type
    'inserted'.
"""

import warnings
from pprint import pprint
from typing import Dict, Optional

import napari
import numpy as np
from napari.layers import Layer
from napari.utils.events import Event
from napari.viewer import Viewer
from qtpy import QtWidgets

from ._my_logger import logger
from .command import CommandManager


class UndoRedoWidget(QtWidgets.QWidget):
    def __init__(self, viewer: Viewer, layer: Optional[Layer] = None) -> None:
        super().__init__()

        warnings.filterwarnings(action="ignore", category=FutureWarning)

        self.viewer = viewer
        self.layer = None
        self.command_managers: Dict[int:CommandManager] = {}
        # self.originator = Originator()
        # self.caretaker = CareTaker()
        # self.savedStates = 0
        # self.currentStateIdx = -1

        self.configure_gui()

        if layer:
            print("inside if")
            self.layer = layer
            self.command_managers[id(self.layer)] = CommandManager(layer)
            self.connect_layer(self.layer)

            # when the widget is initalized,
            # we also want to save the state at which the layer currently is.
            # so we create an event of type "init" and trigger save_state
            event = Event("init")
            event._push_source(self.layer)  # _push_source sets event.source
            self.save_state(event)
        else:
            print("inside else")
            active_layer = self.find_active_layers()
            if active_layer:
                print("inside else if")
                self.layer = active_layer
                self.connect_layer(self.layer)
                event = Event("init")
                event._push_source(self.layer)
                self.save_state(event)
                # self.save_state(Event("init", {"source": self.layer}))

        # slots to detect a change in layer selection,
        # so that the undo widget can connect to the currently active layer
        self.viewer.layers.events.inserted.connect(self.slot_insert_layer)
        self.viewer.layers.events.removed.connect(self.slot_remove_layer)
        self.viewer.layers.selection.events.changed.connect(
            self.slot_select_layer
        )

    # actual undo functionality:

    def save_state(self, event: Event) -> None:
        """
        Save the current state of the napari layer.
        This is called whenever any change happens in a layer.

        Args:
            layer: napari.layers.Layer

        What it's doing:
        0. If the layer's state has changed, only then do the following:
        1. Save the current layer snapshot in the originator
        2. Convert this snapshot into State
        3. Ask the caretaker to store this State in its list of states
        4. Increment the number of savedStates by 1
        5. Increment current state Idx to make it point to most recent state
        """
        if event.type != "init" and not event.source:
            # ignore event without source
            return

        if not self._has_state_changed(event):
            # this check is important because
            # there's no need to save state if no change has occured
            return

        print("save_state")
        pprint(event)
        layer = event.source
        # command_manager = self.command_managers.get(id(layer))
        # command_manager.add_command_to_undo_stack()
        print(f"layer: {layer}")
        print(f"type(layer): {type(layer)}")
        self.originator.set_layer(layer)
        state = self.originator.store_in_state()
        self.caretaker.add_state(state)
        self.savedStates += 1
        self.currentStateIdx += 1
        print(f"currentStateIdx: {self.currentStateIdx}")

    def _has_state_changed(self, event: Event) -> bool:
        """
        Checks if the layer's state has changed

        Args:
            event: Event

        What it's doing:
        0. If its the initial state then return true
        to store the layer's initial state
        1. Use currentStateIdx to get the last stored
        state (existing state) from the caretaker
        2. Use originator to restore layer information
        from the last stored state
        3. check if layer information of current event
        is different from last stored state
        4. if yes, return true because state has changed
        """
        if event.type == "init":
            return True

        existing_state = self.caretaker.get_state(self.currentStateIdx)
        existing_data = self.originator.restore_from_state(existing_state).data
        print(f"type(existing_data): {type(existing_data)}")
        changed = not np.array_equal(event.source.data, existing_data)
        print(f"type(changed): {type(changed)}")
        print(f"changed: {changed}")
        return changed

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
            print(f"currentStateIdx: {self.currentStateIdx}")
            previous_state = self.caretaker.get_state(self.currentStateIdx)
            layer_at_previous_state = self.originator.restore_from_state(
                previous_state
            )
            self.layer = layer_at_previous_state
            active_layer = self.find_active_layers()
            active_layer.data = self.layer.data
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
            print(f"currentStateIdx: {self.currentStateIdx}")
            next_state = self.caretaker.get_state(self.currentStateIdx)
            layer_at_next_state = self.originator.restore_from_state(
                next_state
            )
            self.layer = layer_at_next_state
            active_layer = self.find_active_layers()
            active_layer.data = self.layer.data
            return layer_at_next_state
        else:
            # disable the redo button
            print("redo not available")
            return None

    # widget related functions:
    def configure_gui(self) -> None:
        """
        Configure a QHBoxLayout to hold the undo and redo buttons.
        """
        layout = QtWidgets.QHBoxLayout()
        undo_button = QtWidgets.QPushButton("Undo")
        undo_button.clicked.connect(self.undo)
        layout.addWidget(undo_button)

        redo_button = QtWidgets.QPushButton("Redo")
        redo_button.clicked.connect(self.redo)
        layout.addWidget(redo_button)

        self.setLayout(layout)

    def find_active_layers(self) -> Optional[Layer]:
        """
        Find pre-existing selected layer.
        """
        currently_selected_layer = (
            self.viewer.layers.selection.active
        )  # or self.viewer.layers.selected[0]
        if currently_selected_layer:
            return currently_selected_layer
        return None

    def connect_layer(self, layer: Layer) -> None:
        """
        Connect to one layer.

                Args:
                        layer: Layer (Layer to connect to.)
        """
        # TODO: find an event for any data change in napari viewer

        # first disconnect events from earlier layer if its not None
        if self.layer:
            self.layer.events.data.disconnect(self.save_state)
            # self.layer.events.name.disconnect(self.save_state)
            # self.layer.events.symbol.disconnect(self.save_state)
            # self.layer.events.size.disconnect(self.save_state)
            # self.layer.events.highlight.disconnect(self.save_state)

        # set the global layer to the new layer and connect it to events
        self.layer = layer
        self.layer.events.data.connect(self.save_state)
        # self.layer.events.name.connect(self.save_state)
        # self.layer.events.symbol.connect(self.save_state)
        # self.layer.events.size.connect(self.save_state)
        # self.layer.events.highlight.connect(self.save_state)

    # Slots start here:

    def slot_select_layer(self, event: Event) -> None:
        """Respond to layer selection in viewer.

        Args:
            event (Event): event.type == 'changed'
        """
        currently_selected_layer = self.find_active_layers()
        if currently_selected_layer and currently_selected_layer != self.layer:
            self.connect_layer(currently_selected_layer)

    def slot_insert_layer(self, event: Event) -> None:
        """
        Respond to new layer in viewer.

        Args:
            event (Event): event.type == 'inserted'
        """
        logger.info(
            f'New layer "{event.source}" was inserted at index {event.index}'
        )
        pprint(f"event: {vars(event)}")
        pprint(f"event type: {event.type}")

        newly_inserted_layer = event.source
        if newly_inserted_layer:
            # self.connect_layer(newly_inserted_layer)
            pass

    def slot_remove_layer(self, event: Event) -> None:
        """
        Respond to layer delete in viewer.

        Args:
            event (Event): event.type == 'removed'
        """
        logger.info(f'Removed layer "{event.source}"')
        currently_selected_layer = self.find_active_layers()
        if currently_selected_layer and currently_selected_layer != self.layer:
            self.connect_layer(currently_selected_layer)


# test simulation
def run():
    viewer = Viewer()

    points_layer = viewer.add_points(
        data=np.array([[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40]]),
        ndim=3,
        name="my points layer",
        size=3,
        face_color="red",
        shown=True,
        features={"f1": "a", "f2": 2},
    )

    plugin = UndoRedoWidget(viewer, points_layer)
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


if __name__ == "__main__":
    run()
