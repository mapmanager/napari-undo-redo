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
from typing import Dict, List, Optional, Tuple

import numpy as np
from napari.layers import Layer
from napari.utils.events import Event
from napari.viewer import Viewer
from qtpy import QtWidgets

from napari_undo_redo.command import AddCommand, CommandManager

from ._my_logger import logger
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
        # self.layer_id = 0
        self.layer_id = ""
        self.layer_data = None
        # TODO: using layer name as key for now. Will change it to id once
        # https://github.com/napari/napari/issues/5229 is fixed.
        # self.command_managers: Dict[int:CommandManager] = {}
        self.command_managers: Dict[str:CommandManager] = {}
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
                # event = Event("init")
                # event._push_source(self.layer)
                # self.save_state(event)
                # self.save_state(Event("init", {"source": self.layer}))

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

        # self.layer_id = id(layer)
        self.layer_id = layer.name
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
        # TODO: find an event for any data change in napari viewer

        # first disconnect events from earlier layer if its not None
        if self.layer:
            # self.layer.events.data.disconnect(self.save_state)
            # self.layer.events.name.disconnect(self.save_state)
            # self.layer.events.symbol.disconnect(self.save_state)
            # self.layer.events.size.disconnect(self.save_state)
            self.layer.events.highlight.disconnect(
                self.slot_user_highlight_data
            )

        # set the global layer to the new layer and connect it to events
        self.layer = layer
        # if 'data' in vars(layer).keys():
        if layer.data.any():
            self.layer_data = layer.data
        # self.layer.events.data.connect(self.save_state)
        # self.layer.events.name.connect(self.save_state)
        # self.layer.events.symbol.connect(self.save_state)
        # self.layer.events.size.connect(self.save_state)
        self.layer.events.highlight.connect(self.slot_user_highlight_data)

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
        logger.info(vars(event))
        logger.info(event.source.name)

        if setsAreEqual(event.source.selected_data, self.layer_data):
            # no change
            return

        self.layer = event.source
        # self.layer_id = id(event.source)
        self.layer_id = event.source.name

        command_manager = self.command_managers.get(self.layer_id)
        if not command_manager:
            command_manager = CommandManager(self.layer)
            self.command_managers[self.layer_id] = command_manager
            logger.info(f"added command manager for layer id {self.layer_id}")

        if self.layer_data is None:
            self.layer_data = event.source.data
            logger.info("returning")
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
            self.layer_data = event.source.data

        elif len(event.source.data) < len(self.layer_data):
            # push delete command to undo stack
            # need to get the point's index and coordinates
            # self.layer_data - event.source.data ?
            logger.info("delete")
            self.layer_data = event.source.data

        else:
            # push move command to undo stack
            logger.info("move")


def _get_diff(
    layer1_data: np.ndarray, layer2_data: np.ndarray
) -> Tuple[List[int], np.ndarray]:
    # get the points which are in layer1 but not in layer2
    diff = np.setdiff1d(layer1_data, layer2_data)
    logger.info(diff)
    logger.info(diff.shape)
    logger.info(len(diff))

    """
    [
        [10, 10],
        [20, 30],
        [50, 100]
    ]
    """

    logger.info(np.where(layer1_data == diff))
    index = np.where(layer1_data == diff)[0]
    logger.info(f"Found index: {index}")
    indices = list(set(index.tolist()))

    logger.info(indices)
    logger.info(layer1_data)
    return (indices, diff)


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
