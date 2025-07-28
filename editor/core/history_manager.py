from editor.core.utils import ActionType, AnimatedTile, CollisionRect, Light
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
        elif action_type == ActionType.AddKeyframe:
            self._undo_add_keyframe(data, data_manager)
        elif action_type == ActionType.AddLight:
            self._undo_add_light(data, data_manager)
        elif action_type == ActionType.RemoveLight:
            self._undo_remove_light(data, data_manager)

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
        elif action_type == ActionType.AddKeyframe:
            self._redo_add_keyframe(data, data_manager)
        elif action_type == ActionType.AddLight:
            self._redo_add_light(data, data_manager)
        elif action_type == ActionType.RemoveLight:
            self._redo_remove_light(data, data_manager)

        self.undo_stack.append(action)

    # ----- Undo methods -----
    def _undo_add_keyframe(self, data, data_manager):
        anim_name, new_kf, replaced = data
        anim = data_manager.animation.animations[anim_name]
        tl = anim.timeline
        eps = 1e-2
        # remove added keyframe
        tl.keyframes = [kf for kf in tl.keyframes
                        if not (kf.anim_id == new_kf.anim_id and abs(kf.time - new_kf.time) < eps
                                and kf.tile.x == new_kf.tile.x and kf.tile.y == new_kf.tile.y
                                and kf.layer == new_kf.layer)]
        # restore replaced
        if replaced:
            tl.keyframes.append(replaced)

    def _undo_add_tile(self, data, data_manager):
        layer_index, new_tiles, replaced_tiles = data
        current_tiles = data_manager.layers[layer_index].tiles
        data_manager.layers[layer_index].tiles = [t for t in current_tiles
                                                  if not any(t.x == nt.x and t.y == nt.y for nt in new_tiles)]
        data_manager.layers[layer_index].tiles.extend([t for t in replaced_tiles if t])

    def _undo_remove_tile(self, data, data_manager):
        layer_index, _, replaced_tiles = data
        data_manager.layers[layer_index].tiles.extend([t for t in replaced_tiles if t])

    def _undo_add_collision(self, data, data_manager):
        if isinstance(data, CollisionRect):
            data_manager.collisionRects = [c for c in data_manager.collisionRects if c != data]
        else:
            data_manager.locationPoints = [c for c in data_manager.locationPoints if c.rect != data.rect]
        data_manager.selectedElement = None

    def _undo_remove_collision(self, data, data_manager):
        if isinstance(data, CollisionRect):
            data_manager.collisionRects.append(data)
        else:
            data_manager.locationPoints.append(data)

    def _undo_add_light(self, data, data_manager):
        data_manager.lights = [l for l in data_manager.lights if l != data]
        data_manager.selectedElement = None

    def _undo_remove_light(self, data, data_manager):
        data_manager.lights.append(data)

    # ----- Redo methods -----
    def _redo_add_tile(self, data, data_manager):
        layer_index, new_tiles, _ = data
        current = data_manager.layers[layer_index].tiles
        data_manager.layers[layer_index].tiles = [t for t in current if not any(t.x == nt.x and t.y == nt.y for nt in new_tiles)]
        data_manager.layers[layer_index].tiles.extend(new_tiles)

    def _redo_add_keyframe(self, data, data_manager):
        anim_name, new_kf, replaced = data
        anim = data_manager.animation.animations[anim_name]
        tl = anim.timeline
        eps = 1e-2
        if replaced:
            tl.keyframes = [kf for kf in tl.keyframes
                            if not (kf.anim_id == replaced.anim_id and abs(kf.time - replaced.time) < eps
                                    and kf.tile.x == replaced.tile.x and kf.tile.y == replaced.tile.y
                                    and kf.layer == replaced.layer)]
        tl.keyframes.append(copy.deepcopy(new_kf))

    def _redo_remove_tile(self, data, data_manager):
        layer_index, _, replaced_tiles = data
        current = data_manager.layers[layer_index].tiles
        data_manager.layers[layer_index].tiles = [t for t in current
                                                  if not any(t.x == rt.x and t.y == rt.y for rt in replaced_tiles)]

    def _redo_add_collision(self, data, data_manager):
        if isinstance(data, CollisionRect):
            data_manager.collisionRects.append(data)
        else:
            data_manager.locationPoints.append(data)

    def _redo_remove_collision(self, data, data_manager):
        if isinstance(data, CollisionRect):
            data_manager.collisionRects = [c for c in data_manager.collisionRects if c != data]
        else:
            data_manager.locationPoints = [c for c in data_manager.locationPoints if c.rect != data.rect]

    def _redo_add_light(self, data, data_manager):
        data_manager.lights.append(copy.deepcopy(data))

    def _redo_remove_light(self, data, data_manager):
        data_manager.lights = [l for l in data_manager.lights if l != data]

    # ----- Registration methods -----
    def RegisterAddTiles(self, layer_index, new_tiles, replaced_tiles):
        self._register_action(ActionType.AddTile,
                              (layer_index, copy.deepcopy(new_tiles), copy.deepcopy(replaced_tiles)))

    def RegisterRemoveTiles(self, layer_index, tiles, data_manager):
        removed = []
        for x, y in tiles:
            for tile in data_manager.layers[layer_index].tiles:
                if tile.x == x and tile.y == y:
                    removed.append(tile)
        if removed:
            self._register_action(ActionType.RemoveTile,
                                  (layer_index, [], copy.deepcopy(removed)))

    def RegisterAddKeyframe(self, animation_name: str, new_kf: AnimatedTile, anim):
        timeline = anim.timeline
        replaced = None
        eps = 1e-2
        for kf in timeline.keyframes:
            if (kf.anim_id == new_kf.anim_id and abs(kf.time - new_kf.time) < eps
                    and kf.tile.x == new_kf.tile.x and kf.tile.y == new_kf.tile.y
                    and kf.layer == new_kf.layer):
                replaced = copy.deepcopy(kf)
                break
        if replaced:
            timeline.keyframes = [kf for kf in timeline.keyframes
                                  if not (kf.anim_id == replaced.anim_id and abs(kf.time - replaced.time) < eps
                                          and kf.tile.x == replaced.tile.x and kf.tile.y == replaced.tile.y
                                          and kf.layer == replaced.layer)]
        timeline.keyframes.append(new_kf)
        self._register_action(ActionType.AddKeyframe,
                              (animation_name, copy.deepcopy(new_kf), replaced))


    def RegisterAddElement(self, collision):
        if isinstance(collision,CollisionRect):
            snapshot = collision.clone()
            self._register_action(ActionType.AddCollision, snapshot)
        else:
            self._register_action(ActionType.AddCollision, copy.deepcopy(collision))

    def	RegisterRemoveElement(self, collision):
        if isinstance(collision,CollisionRect):
            snapshot = collision.clone()
            self._register_action(ActionType.RemoveCollision, snapshot)
        else:
            self._register_action(ActionType.RemoveCollision, copy.deepcopy(collision))

    def RegisterAddLight(self, light: Light):
        self._register_action(ActionType.AddLight, copy.deepcopy(light))

    def RegisterRemoveLight(self, light: Light):
        self._register_action(ActionType.RemoveLight, copy.deepcopy(light))

    def _register_action(self, action_type, data):
        self.undo_stack.append((action_type, data))
        self.redo_stack.clear()
