"""
BUGS:
    1. when the plugin is loaded and a new layer is added,
    then napari fails at `self.layer.events.data.connect(self.save_state)`
    with the error "AttributeError: 'EmitterGroup' object has no attribute
    'data'" because the event has no attribute data. The event is of type
    'inserted'.
"""

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
from napari.layers import Layer
from napari.utils.events import Event
from napari.viewer import Viewer
from qtpy import QtWidgets

from ._my_logger import logger
from .command import AddCommand, CommandManager, DeleteCommand, MoveCommand
from .utils import setsAreEqual


class UndoRedoWidget(QtWidgets.QWidget):
    def __init__(self, viewer: Viewer, layer: Optional[Layer] = None) -> None:
        """
        Note that each layer has its command manager, which is why
        we are creating a dictionary of command managers
        which maps layerID to command manager instance.
        """
        super().__init__()

        warnings.filterwarnings(action="ignore", category=FutureWarning)

        self.viewer = viewer
        self.layer = None
        self.layer_id = 0
        self.layer_data = np.array([])
        # TODO: using layer name as key for now. Will change it to id once
        # https://github.com/napari/napari/issues/5229 is fixed.
        self.command_managers: Dict[int:CommandManager] = {}
        self.configure_gui()

        if layer:
            logger.info("layer found")
            logger.info(layer)
            self.layer = layer
            self._init_command_manager(layer)
            # when the widget is initalized,
            # we also want to save the state at which the layer currently is.
            # so we create an event of type "init" and trigger save_state
            # event = Event("init")
            # event._push_source(self.layer)  # _push_source sets event.source
            # self.save_state(event)
        else:
            logger.info("layer not found. Finding active layer")
            active_layer = self.find_active_layers()
            if active_layer:
                logger.info("active layer found")
                logger.info(active_layer)
                self.layer = active_layer
                self._init_command_manager(active_layer)

        # slots to detect a change in layer selection,
        # so that the undo widget can connect to the currently active layer
        self.viewer.layers.events.inserted.connect(self.slot_insert_layer)
        self.viewer.layers.events.removed.connect(self.slot_remove_layer)
        self.viewer.layers.selection.events.changed.connect(
            self.slot_select_layer
        )

    def _init_command_manager(self, layer: Layer):
        # # if 'data' in vars(layer).keys():
        # if layer.data:
        #     self.layer_data = layer.data
        self.layer_id = hash(layer)
        logger.info(
            "_init_command_manager: adding command manager for "
            + f"layer id {self.layer_id}"
        )
        self.command_managers[self.layer_id] = CommandManager(layer)
        self.connect_layer(self.layer)

    def undo(self):
        logger.info(f"undo called for layer id {self.layer_id}")
        command_manager = self.command_managers.get(self.layer_id)
        if not command_manager:
            logger.info(
                f"no command manager found for layer id {self.layer_id}"
            )
            return

        command_manager.undo()

    def redo(self):
        logger.info(f"redo called for layer id {self.layer_id}")
        command_manager = self.command_managers.get(self.layer_id)
        if not command_manager:
            logger.info(
                f"no command manager found for layer id {self.layer_id}"
            )
            return

        command_manager.redo()

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
        currently_selected_layer = self.viewer.layers.selection.active
        # currently_selected_layer = (
        #     self.viewer.layers.selection.active
        # )  # or self.viewer.layers.selected[0]
        if currently_selected_layer:
            return currently_selected_layer
        return None

    def connect_layer(self, layer: Layer) -> None:
        """
        Connect to one layer.

                Args:
                        layer: Layer (Layer to connect to.)
        """
        # first disconnect events from earlier layer if its not None
        if self.layer:
            # self.layer.events.data.disconnect(self.save_state)
            # self.layer.events.name.disconnect(self.save_state)
            # self.layer.events.symbol.disconnect(self.save_state)
            # self.layer.events.size.disconnect(self.save_state)
            # self.layer.events.highlight.disconnect(
            #     self.slot_user_highlight_data
            # )
            self.layer.events.data.disconnect(self.slot_user_highlight_data)
            # self.layer.events.select.disconnect(self.slot_user_select_data)

            self.layer_data = np.array([])

        # set the global layer to the new layer and connect it to events
        self.layer = layer
        if "data" in vars(layer).keys() and layer.data.any():
            self.layer_data = layer.data.copy()
        # self.layer.events.data.connect(self.save_state)
        # self.layer.events.name.connect(self.save_state)
        # self.layer.events.symbol.connect(self.save_state)
        # self.layer.events.size.connect(self.save_state)
        # self.layer.events.highlight.connect(self.slot_user_highlight_data)
        self.layer.events.data.connect(self.slot_user_highlight_data)
        # self.layer.events.select.connect(self.slot_user_select_data)

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
        # pprint(f"event: {vars(event)}")
        # pprint(f"event type: {event.type}")

        # newly_inserted_layer = event.source
        newly_inserted_layer = event.value
        if newly_inserted_layer:
            self.connect_layer(newly_inserted_layer)

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

    def slot_user_highlight_data(self, event: Event) -> None:
        # logger.info(vars(event))
        # logger.info(event.source.name)

        if setsAreEqual(event.source.selected_data, self.layer_data):
            # no change
            return

        self.layer = event.source
        self.layer_id = hash(event.source)

        command_manager = self.command_managers.get(self.layer_id)
        if not command_manager:
            command_manager = CommandManager(self.layer)
            self.command_managers[self.layer_id] = command_manager
            logger.info(f"added command manager for layer id {self.layer_id}")

        if command_manager.is_operation_in_progress():
            logger.info("undo/redo in progress. Ignoring event.")
            return

        if len(event.source.data) > len(self.layer_data):
            # push add command to undo stack
            # need to get the point's index and coordinates
            # event.source.data - self.layer_data ?
            logger.info("add")
            added_indices, added_points = _get_diff(
                event.source.data, self.layer_data
            )
            command = AddCommand(event.source, added_indices, added_points)
            command_manager.add_command_to_undo_stack(command)
            self.layer_data = event.source.data.copy()

        elif len(event.source.data) < len(self.layer_data):
            # push delete command to undo stack
            # need to get the point's index and coordinates
            # self.layer_data - event.source.data ?
            logger.info("delete")
            deleted_indices, deleted_points = _get_diff(
                self.layer_data, event.source.data.copy()
            )
            command = DeleteCommand(
                event.source, deleted_indices, deleted_points
            )
            command_manager.add_command_to_undo_stack(command)
            self.layer_data = event.source.data.copy()

        else:
            logger.info("move")
            changed_indices = list(event.source.selected_data)
            logger.info(changed_indices)
            previous_data = self.layer_data[changed_indices]
            new_data = event.source.data[changed_indices]
            logger.info(f"Previous: {previous_data}, New: {new_data}")

            if not np.array_equal(previous_data, new_data):
                logger.info("creating move command")
                command = MoveCommand(
                    event.source, changed_indices, previous_data, new_data
                )
                command_manager.add_command_to_undo_stack(command)
                self.layer_data = event.source.data.copy()


def _get_diff(
    layer1_data: np.ndarray, layer2_data: np.ndarray
) -> Tuple[List[int], np.ndarray]:
    # this assumes layer1_data is larger than layer2_data
    ptr1, ptr2 = 0, 0
    differing_indices = []
    diff_data = []

    while ptr1 < len(layer1_data) and ptr2 < len(layer2_data):
        diff = layer1_data[ptr1] - layer2_data[ptr2]
        if diff.any():  # if there is any difference between the two values
            differing_indices.append(ptr1)
            diff_data.append((layer1_data[ptr1]).tolist())
            ptr1 += 1
        else:  # the two values are equal, proceed
            ptr1 += 1
            ptr2 += 1

    while ptr1 < len(layer1_data):
        differing_indices.append(ptr1)
        diff_data.append((layer1_data[ptr1]).tolist())
        ptr1 += 1

    res = (differing_indices, np.array(diff_data))
    logger.info(res)
    return res


# # test simulation
# def run():
#     viewer = Viewer()

#     points_layer = viewer.add_points(
#         data=np.array([[0, 10, 10], [0, 20, 20], [0, 30, 30], [0, 40, 40]]),
#         ndim=3,
#         name="my points layer",
#         size=3,
#         face_color="red",
#         shown=True,
#         features={"f1": "a", "f2": 2},
#     )

#     plugin = UndoRedoWidget(viewer, points_layer)


#     napari.run()


# if __name__ == "__main__":
#     run()
