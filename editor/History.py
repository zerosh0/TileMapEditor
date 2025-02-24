from editor.utils import ActionType
import copy

class HistoryManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def Undo(self, data_manager):
        if not self.undo_stack:
            return
        action = self.undo_stack.pop()
        action_type, data = action

        if action_type == ActionType.AddTile:
            self._undo_add_tile(data, data_manager)
        elif action_type == ActionType.RemoveTile:
            self._undo_remove_tile(data, data_manager)
        elif action_type == ActionType.AddCollision:
            self._undo_add_collision(data, data_manager)
        elif action_type == ActionType.RemoveCollision:
            self._undo_remove_collision(data, data_manager)

        self.redo_stack.append(action)

    def Redo(self, data_manager):
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        action_type, data = action

        if action_type == ActionType.AddTile:
            self._redo_add_tile(data, data_manager)
        elif action_type == ActionType.RemoveTile:
            self._redo_remove_tile(data, data_manager)
        elif action_type == ActionType.AddCollision:
            self._redo_add_collision(data, data_manager)
        elif action_type == ActionType.RemoveCollision:
            self._redo_remove_collision(data, data_manager)

        self.undo_stack.append(action)

    # ----- Undo methods -----
    def _undo_add_tile(self, data, data_manager):
        layer_index, new_tiles, replaced_tiles = data
        current_tiles = data_manager.layers[layer_index].tiles
        data_manager.layers[layer_index].tiles = [
            t for t in current_tiles 
            if not any(t.x == nt.x and t.y == nt.y for nt in new_tiles)
        ]
        filtered_replaced_tiles = [tile for tile in replaced_tiles if tile is not None]
        data_manager.layers[layer_index].tiles.extend(filtered_replaced_tiles)

    def _undo_remove_tile(self, data, data_manager):
        layer_index, new_tiles, replaced_tiles = data
        filtered_replaced_tiles = [tile for tile in replaced_tiles if tile is not None]
        data_manager.layers[layer_index].tiles.extend(filtered_replaced_tiles)

    def _undo_add_collision(self, data, data_manager):
        data_manager.collisionRects = [
            c for c in data_manager.collisionRects 
            if c != data
        ]
        data_manager.selectedCollisionRect = None

    def _undo_remove_collision(self, data, data_manager):
        data_manager.collisionRects.append(data)

    # ----- Redo methods -----
    def _redo_add_tile(self, data, data_manager):
        layer_index, new_tiles, replaced_tiles = data
        current_tiles = data_manager.layers[layer_index].tiles
        data_manager.layers[layer_index].tiles = [
            t for t in current_tiles 
            if not any(t.x == nt.x and t.y == nt.y for nt in new_tiles)
        ]
        data_manager.layers[layer_index].tiles.extend(new_tiles)

    def _redo_remove_tile(self, data, data_manager):
        layer_index, new_tiles, replaced_tiles = data
        current_tiles = data_manager.layers[layer_index].tiles
        data_manager.layers[layer_index].tiles = [
            t for t in current_tiles
            if not any(t.x == rt.x and t.y == rt.y for rt in replaced_tiles)
        ]

    def _redo_add_collision(self, data, data_manager):
        data_manager.collisionRects.append(data)

    def _redo_remove_collision(self, data, data_manager):
        data_manager.collisionRects = [
            c for c in data_manager.collisionRects 
            if c != data
        ]

    # ----- Méthodes d'enregistrement -----
    def RegisterAddTiles(self, layer_index, new_tiles, replaced_tiles):
        self._register_action(
            ActionType.AddTile, 
            (layer_index, copy.deepcopy(new_tiles), copy.deepcopy(replaced_tiles))
        )

    def RegisterRemoveTiles(self, layer_index, tiles, data_manager):
        RemoveTiles = []
        for x, y in tiles:
            for tile in data_manager.layers[layer_index].tiles:
                if x == tile.x and y == tile.y:
                    RemoveTiles.append(tile)
        if RemoveTiles:
            self._register_action(
                ActionType.RemoveTile,
                (layer_index, [], copy.deepcopy(RemoveTiles))
            )

    def RegisterAddCollisions(self, collision):
        self._register_action(
            ActionType.AddCollision, 
            copy.deepcopy(collision)
        )

    def RegisterRemoveCollisions(self, collision):
        self._register_action(
            ActionType.RemoveCollision, 
            copy.deepcopy(collision)
        )

    def _register_action(self, action_type, data):
        self.undo_stack.append((action_type, data))
        self.redo_stack.clear()
