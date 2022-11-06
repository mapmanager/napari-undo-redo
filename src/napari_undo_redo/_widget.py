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

import napari
import numpy as np
from napari.layers import Layer
from napari.utils.events import Event
from napari.viewer import Viewer
from qtpy import QtWidgets

from ._layer_type import LayerType
from ._my_logger import logger
from .command import (
    AddPointCommand,
    CommandManager,
    DeletePointCommand,
    FaceColorChangeCommand,
    MovePointCommand,
    SymbolChangeCommand,
)
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
        self.layer_symbol = ""
        self.layer_face_color = np.array([])
        self.layer_type = LayerType.NONE

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

    def _get_command_manager(self, layer: Layer) -> CommandManager:
        self.layer = layer
        self.layer_id = hash(layer)

        command_manager = self.command_managers.get(self.layer_id)
        if not command_manager:
            command_manager = CommandManager(self.layer)
            self.command_managers[self.layer_id] = command_manager
            logger.info(f"added command manager for layer id {self.layer_id}")

        return command_manager

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
            if self.layer_type == LayerType.POINTS:
                # self.layer.events.name.disconnect(self.save_state)
                self.layer.events.symbol.disconnect(
                    self.slot_points_symbol_change
                )
                self.layer.events.size.disconnect(self.slot_points_size_change)
                self.layer.events.data.disconnect(self.slot_points_data_change)
                # self.layer.events.current_face_color.disconnect(
                #     self.slot_points_face_color_change
                # )
                self.layer._face.events.current_color.disconnect(
                    self.slot_points_face_color_change
                )

                self.layer_data = np.array([])
                self.layer_symbol = ""
                self.layer_face_color = np.array([])

        # set the global layer to the new layer and connect it to events
        self.layer = layer
        self._set_layer_type(layer)
        self.layer_id = hash(layer)

        if self.layer_type == LayerType.POINTS:
            self.layer_symbol = self.layer.symbol
            self.layer_face_color = self.layer._face.current_color
            if "data" in vars(layer).keys() and layer.data.any():
                self.layer_data = layer.data.copy()

            # self.layer.events.name.connect(self.save_state)
            self.layer.events.symbol.connect(self.slot_points_symbol_change)
            self.layer.events.size.connect(self.slot_points_size_change)
            self.layer.events.data.connect(self.slot_points_data_change)
            # self.layer.events.current_face_color.connect(self.slot_points_face_color_change)
            self.layer._face.events.current_color.connect(
                self.slot_points_face_color_change
            )

    # Slots start here:

    def slot_select_layer(self, event: Event) -> None:
        """Respond to layer selection in viewer.

        Args:
            event (Event): event.type == 'changed'
        """
        currently_selected_layer = self.find_active_layers()
        if currently_selected_layer and currently_selected_layer != self.layer:
            logger.info(f"New layer selected: {currently_selected_layer}")
            logger.info(f"New layer id: {hash(currently_selected_layer)}")
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

    def slot_points_data_change(self, event: Event) -> None:
        # logger.info(vars(event))
        # logger.info(event.source.name)

        if setsAreEqual(event.source.selected_data, self.layer_data):
            # no change
            return

        command_manager = self._get_command_manager(event.source)

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
            command = AddPointCommand(
                event.source, added_indices, added_points
            )
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
            command = DeletePointCommand(
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
                command = MovePointCommand(
                    event.source, changed_indices, previous_data, new_data
                )
                command_manager.add_command_to_undo_stack(command)
                self.layer_data = event.source.data.copy()

    def slot_points_symbol_change(self, event: Event) -> None:
        command_manager = self._get_command_manager(event.source)

        if command_manager.is_operation_in_progress():
            logger.info("undo/redo in progress. Ignoring event.")
            return

        logger.info(f"prev layer symbol: {self.layer_symbol}")
        logger.info(f"new layer symbol: {event.source.symbol}")
        command = SymbolChangeCommand(
            event.source, self.layer_symbol, event.source.symbol
        )
        command_manager.add_command_to_undo_stack(command)
        self.layer_symbol = event.source.symbol

    def slot_points_size_change(self, event: Event) -> None:
        logger.info(event)

    def slot_points_face_color_change(self, event: Event) -> None:
        """
        The colors attribute in event.source is a 2D array containing
        the colors of all points in the layer before the change in color
        of any point or points
        """
        current_active_layer = self.find_active_layers()
        if not current_active_layer:
            logger.warning("No current active layer found")
            return

        indices_changed = list(current_active_layer._selected_data)
        logger.info(f"Indices changed: {indices_changed}")
        if not indices_changed:
            logger.warning("No changed indices found")
            return

        all_old_colors = event.source.colors
        logger.info(
            f"All old Colors: {all_old_colors}"
        )  # colors of all the points in the layer as a 2D layer

        changed_old_colors = np.array(all_old_colors[indices_changed[0]])
        for index in indices_changed[1:]:
            changed_old_colors = np.vstack(
                [changed_old_colors, all_old_colors[index]]
            )
        logger.info(f"Changed old colors: {changed_old_colors}")

        new_color = event.source.current_color
        logger.info(f"New Color: {new_color}")

        command_manager = self._get_command_manager(current_active_layer)
        if command_manager.is_operation_in_progress():
            logger.info("undo/redo in progress. Ignoring event.")
            return

        logger.info(f"self.layer_face_color: {self.layer_face_color}")
        command = FaceColorChangeCommand(
            current_active_layer,
            self.layer_face_color,
            indices_changed,
            changed_old_colors,
            new_color,
        )
        command_manager.add_command_to_undo_stack(command)

        self.layer_face_color = self.layer._face.current_color

    def _set_layer_type(self, layer: Layer):
        if isinstance(layer, napari.layers.points.points.Points):
            self.layer_type = LayerType.POINTS
        elif isinstance(layer, napari.layers.shapes.shapes.Shapes):
            self.layer_type = LayerType.SHAPES

        logger.info(f"Set layer type to {self.layer_type}")


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
