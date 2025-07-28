import math
import random
import time
from typing import Generator, List, Tuple
import pygame
from editor.game_engine.core.utils import TileMap as CoreTileMap, CollisionRect as CoreCollisionRect, LocationPoint as CoreLocationPoint
from editor.game_engine.config import STANDARD_TILE_SIZE, BACKGROUND_COLOR


class Level:
    def __init__(self,
                 layers: List,
                 collision_rects: List[CoreCollisionRect],
                 lights: List, 
                 location_points: List[CoreLocationPoint],
                 tile_palette,
                 backgrounds: List[dict],
                 animation_manager=None,
                 offset_x: int = 0,
                 offset_y: int = 0,
                 standard_tile_size: int = STANDARD_TILE_SIZE,
                 performance_monitor=None):
        self.performance_monitor = performance_monitor
        self.layers            = layers
        self.collision_rects   = collision_rects
        self.location_points   = location_points
        self.lights            = lights
        self.tile_palette      = tile_palette
        self.background_def = backgrounds
        self.animation_manager = animation_manager
        self.offset_x          = offset_x
        self.offset_y          = offset_y
        self.standard_tile_size = standard_tile_size
        self.shadow_alpha=255
        self.tile_maps         = {}
        self.tile_sizes        = {}
        self.background_layers = []
        self.tile_transform_cache = {}
        self.tile_alpha_cache     = {}
        self._parallax_layers = []
        self._prepare_background()
        self.init_lightning()
        self.load_tile_maps()
        self.scaled_collision_rects = self.get_scaled_collision_rects()
        self._transition_duration = 0.0
        self._transition_timer    = 0.0
        self._bg_target                 = None
        self._bg_current                = None
        self._parallax_layers_current   = []    
        self.draw_player = lambda s : None
        self.player_z_index = 8

    def reset_text(self):
        for rect in self.collision_rects:
            rect.text=None

    @classmethod
    def from_data_manager(cls, data_manager,tile_palette, performance_monitor=None,animation_manager=None):
        """
        Construit un Level directement à partir d'une instance de DataManager,
        sans passer par un JSON.
        """
        return cls(
            layers           = data_manager.layers.copy(),
            collision_rects  = data_manager.collisionRects.copy(),
            lights           = data_manager.lights.copy(),
            location_points  = data_manager.locationPoints.copy(),
            tile_palette     = tile_palette,
            backgrounds      = data_manager.get_current_background().copy(),
            offset_x         = 0,
            offset_y         = 0,
            standard_tile_size = data_manager.settings.tile_size if hasattr(data_manager.settings, 'tile_size') else STANDARD_TILE_SIZE,
            performance_monitor = performance_monitor,
            animation_manager = data_manager.animation
        )

    def start_background_transition(self, new_bg, duration):
        self._bg_current              = self.background_def.copy()
        self._parallax_layers_current = self._parallax_layers.copy()
        self._bg_target               = new_bg.copy()
        self._transition_duration     = max(duration, 0.001)
        self._transition_timer        = 0.0
        self.background_def = self._bg_target
        self._prepare_background()


    def update_transition(self, dt: float):
        if self._bg_target is None:
            return
        self._transition_timer += dt
        if self._transition_timer >= self._transition_duration:
            self._bg_target = None


    def init_lightning(self):
        for i, light in enumerate(self.lights):
            first_size = next(iter(self.tile_sizes.values()), 16)
            scale = self.standard_tile_size / first_size
            self.lights[i] = {
                "pos": (
                    int(light.x * scale) + self.offset_x,
                    int(light.y * scale) + self.offset_y
                ),
                "base_radius": light.radius,
                "base_color": light.color,
                "start_time": time.time() + random.random() * 10,
                "radius_var": getattr(light, "radius_var", 3),
                "blink": getattr(light, "blink", False),
                "visible": light.visible
            }

    def load_tile_maps(self):
        for tm in self.tile_palette.Maps:
            self.tile_maps[tm.name] = tm
            self.tile_sizes[tm.name] = tm.tileSize

    def _prepare_background(self):
        """
        Pré-charge les images si le bg est de type 'image'.
        Pour 'color', on ne fait rien.
        """
        self._parallax_layers.clear()
        bg = self.background_def

        if not bg:
            return

        if bg.get("type") == "image":
            for layer_info in bg.get("layers", []):
                img = pygame.image.load(layer_info["path"]).convert_alpha()
                self._parallax_layers.append({
                    "image": img,
                    "parallax": layer_info["parallax"],
                    "last_screen_size": None,
                    "scaled_image": None,
                    "scaled_size": None
                })

    def get_scaled_rects(self) -> List[pygame.Rect]:
        return [crect.rect for crect in self.get_scaled_collision_rects()]

    def get_scaled_collision_rects(self) -> List[CoreCollisionRect]:
        scaled = []
        first = next(iter(self.tile_sizes.values()), 16)
        scale = self.standard_tile_size / first
        for rd in self.collision_rects:
            r = rd.rect
            rect = pygame.Rect(
                int(r.x * scale) + self.offset_x,
                int(r.y * scale) + self.offset_y,
                int(r.width * scale),
                int(r.height * scale)
            )
            scaled.append(CoreCollisionRect(rd.type, rd.name, rect, rd.color,rd.graph,rd.collide,rd.text,rd.font_size,rd.text_color,rd.bubble_speed,rd.bubble_duration,rd.padding,rd.bubble_start_time))
        return scaled

    def get_locations_by_type(self, type) -> Generator:
        first = next(iter(self.tile_sizes.values()), 16)
        scale = self.standard_tile_size / first
        for loc in self.location_points:
            if loc.type == type:
                yield (loc.rect.x * scale + self.offset_x,
                       loc.rect.y * scale + self.offset_y)

    def get_location_by_name(self, name) -> tuple:
        first = next(iter(self.tile_sizes.values()), 16)
        scale = self.standard_tile_size / first
        for loc in self.location_points:
            if loc.name == name:
                return (loc.rect.x * scale + self.offset_x,
                        loc.rect.y * scale + self.offset_y)
        return (800,204)

    def get_location_point_by_name(self, name) -> CoreLocationPoint:
        for loc in self.location_points:
            if loc.name == name:
                return loc

    def get_visible_tiles(self, layer, camera):
        cam = camera.camera_rect
        cam_r = cam.x + cam.width
        cam_b = cam.y + cam.height
        ts = self.standard_tile_size

        for td in layer.tiles:
            if not hasattr(td, "world_x"):
                td.world_x = td.x * ts + self.offset_x
                td.world_y = td.y * ts + self.offset_y
            wx, wy = td.world_x, td.world_y
            if wx + ts < cam.x or wx > cam_r or wy + ts < cam.y or wy > cam_b:
                continue
            yield td, wx, wy

    def get_transformed_tile(self, tilemap: CoreTileMap, td):
        key = (
            tilemap.name,
            td.Originalx, td.Originaly,
            td.flipHorizontal, td.flipVertical,
            td.rotation,
            self.standard_tile_size
        )
        if key in self.tile_transform_cache:
            return self.tile_transform_cache[key]
        try:
            img = tilemap.get_tile(td.Originalx, td.Originaly, self.standard_tile_size)
        except:
            return None
        if td.flipHorizontal:
            img = pygame.transform.flip(img, True, False)
        if td.flipVertical:
            img = pygame.transform.flip(img, False, True)
        if td.rotation:
            img = pygame.transform.rotate(img, td.rotation)
        self.tile_transform_cache[key] = img
        return img

    def draw_background(self, screen, camera):
        """Fondu (cross-fade) entre _bg_current et _bg_target / ou dessin normal si pas de transition."""
        sw, sh = screen.get_size()

        # pas de transition en cours → dessin normal
        if self._bg_target is None:
            if self.background_def.get("type") == "image":
                self._draw_parallax(self._parallax_layers, screen, camera, alpha=255)
            else:
                screen.fill(tuple(self.background_def.get("color", BACKGROUND_COLOR)))
            return

        # on est en transition
        t = min(max(self._transition_timer / self._transition_duration, 0.0), 1.0)
        alpha_new = int(255 * t)
        alpha_old = 255 - alpha_new

        # 1) dessiner l'ancien background (snapshot) avec alpha_old
        if self._bg_current.get("type") == "image":
            # ses layers ont été snapshotés en `_parallax_layers_current`
            self._draw_parallax(self._parallax_layers_current, screen, camera, alpha=alpha_old)
        else:
            # couleur → surface pleine
            surf = pygame.Surface((sw, sh), flags=pygame.SRCALPHA)
            color = tuple(self._bg_current.get("color", BACKGROUND_COLOR))
            surf.fill((*color, alpha_old))
            screen.blit(surf, (0, 0))

        # 2) dessiner le nouveau background avec alpha_new
        if self._bg_target.get("type") == "image":
            self._draw_parallax(self._parallax_layers, screen, camera, alpha=alpha_new)
        else:
            surf = pygame.Surface((sw, sh), flags=pygame.SRCALPHA)
            color = tuple(self._bg_target.get("color", BACKGROUND_COLOR))
            surf.fill((*color, alpha_new))
            screen.blit(surf, (0, 0))


    def _draw_parallax(self, layers, screen, camera, alpha):
        sw, sh = screen.get_size()
        base_off_x, base_off_y = camera.apply_point(0, 0)

        for layer in layers:
            orig = layer["image"]
            par  = layer["parallax"]
            if layer.get("scaled_size") is None or layer["scaled_size"][1] != sh:
                ow, oh = orig.get_size()
                scale = sh / oh
                nw = int(ow * scale)
                layer["scaled_image"] = pygame.transform.scale(orig, (nw, sh))
                layer["scaled_size"]  = (nw, sh)

            img = layer["scaled_image"]
            nw, nh = layer["scaled_size"]
            img.set_alpha(alpha)
            off_x = int(-base_off_x * par) % nw
            off_y = 0
            x = -off_x
            while x < sw:
                screen.blit(img, (x, off_y))
                x += nw




    def draw(self, screen, camera,clock):
        self.drawn=False
        self.update_transition(clock.get_time() / 1000.0)
        self.draw_background(screen, camera)
        # — Tiles —
        anim_states = {}
        if self.animation_manager is not None:
            anim_states = self.animation_manager.get_current_states()

        for layer_idx, layer in enumerate(self.layers):
            opacity = int(layer.opacity * 255)

            # — 1) Tuiles statiques —
            for td, wx, wy in self.get_visible_tiles(layer, camera):
                tm = self.tile_maps.get(td.TileMap)
                if not tm:
                    continue
                if opacity != 255:
                    key_a = (
                        tm.name,
                        td.Originalx, td.Originaly,
                        td.flipHorizontal, td.flipVertical,
                        td.rotation,
                        self.standard_tile_size,
                        opacity
                    )
                    if key_a in self.tile_alpha_cache:
                        tile_img = self.tile_alpha_cache[key_a]
                    else:
                        base = self.get_transformed_tile(tm, td)
                        if base is None:
                            continue
                        tile_img = base.copy()
                        tile_img.set_alpha(opacity)
                        self.tile_alpha_cache[key_a] = tile_img
                else:
                    tile_img = self.get_transformed_tile(tm, td)
                    if tile_img is None:
                        continue

                px, py = camera.apply_point(wx, wy)
                screen.blit(tile_img, (px, py))

            # — 2) Tuiles animées pour ce même calque —
            if self.animation_manager is not None:
                for anim_name, anim_data in anim_states.items():
                    # anim_data est dict[anim_id -> frame_dict]
                    for anim_id, frame_dict in anim_data.items():
                        # frame_dict est dict[(x,y,layer) -> AnimatedTile]
                        for (x, y, lay), anim_tile in frame_dict.items():
                            if lay != layer_idx:
                                continue
                            if anim_tile.tile.TileMap == "":
                                continue

                            tm = self.tile_maps.get(anim_tile.tile.TileMap)
                            if not tm:
                                continue
                            key_a = (
                                tm.name,
                                anim_tile.tile.Originalx, anim_tile.tile.Originaly,
                                anim_tile.tile.flipHorizontal, anim_tile.tile.flipVertical,
                                anim_tile.tile.rotation,
                                self.standard_tile_size,
                                opacity
                            )
                            if key_a in self.tile_alpha_cache:
                                tile_img = self.tile_alpha_cache[key_a]
                            else:
                                base = tm.get_tile(
                                    anim_tile.tile.Originalx,
                                    anim_tile.tile.Originaly,
                                    self.standard_tile_size
                                )
                                img = base
                                if anim_tile.tile.flipHorizontal:
                                    img = pygame.transform.flip(img, True, False)
                                if anim_tile.tile.flipVertical:
                                    img = pygame.transform.flip(img, False, True)
                                if anim_tile.tile.rotation:
                                    img = pygame.transform.rotate(img, anim_tile.tile.rotation)
                                img.set_alpha(opacity)
                                tile_img = img
                                self.tile_alpha_cache[key_a] = tile_img

                            wx = anim_tile.tile.x * self.standard_tile_size + self.offset_x
                            wy = anim_tile.tile.y * self.standard_tile_size + self.offset_y
                            px, py = camera.apply_point(wx, wy)
                            screen.blit(tile_img, (px, py))
            if layer_idx==self.player_z_index:
                self.draw_player(screen)
                self.drawn=True
        if not self.drawn:
            self.draw_player(screen)




        # — Debug collisions —
        from editor.game_engine import config
        
        for crect in self.get_scaled_collision_rects():
            if config.DEBUG_COLLISIONS:
                pygame.draw.rect(screen,
                                crect.color,
                                camera.apply_rect(crect.rect),
                                2)
            if getattr(crect, 'text', None):
                now = time.time()
                # … dans la boucle sur crect …
                if crect.text is not None:

                    # 1) Calculer le delta
                    dt = now - crect.bubble_start_time
                    # 2) Gérer la durée d’affichage
                    if crect.bubble_duration >= 0 and dt > crect.bubble_duration:
                        continue  # on n’affiche plus du tout

                    # 3) Calculer combien de caractères révéler
                    if crect.bubble_speed <= 0:
                        display_text = crect.text
                    else:
                        n_chars = int(dt * crect.bubble_speed)
                        display_text = crect.text[:n_chars]

                    # 4) Rendu avec retour à la ligne
                    font    = pygame.font.Font(None, crect.font_size)
                    inner_w = crect.rect.width - 2 * crect.padding
                    text_surfs = self.render_wrapped_text(
                        display_text, font, crect.text_color, inner_w
                    )

                    # 5) Blit ligne par ligne
                    base_x, base_y = crect.rect.topleft
                    for idx, surf in enumerate(text_surfs):
                        y = base_y + crect.padding + idx * font.get_linesize()
                        x = base_x + crect.padding
                        screen.blit(surf, camera.apply_point(x, y))


    def render_wrapped_text(self,text: str,
                            font: pygame.font.Font,
                            color: Tuple[int,int,int],
                            max_width: int) -> list[pygame.Surface]:

        words = text.split(' ')
        lines = []
        current = []
        for word in words:
            test = ' '.join(current + [word])
            if font.size(test)[0] <= max_width:
                current.append(word)
            else:
                lines.append(' '.join(current))
                current = [word]
        if current:
            lines.append(' '.join(current))

        return [font.render(line, True, color) for line in lines]

    def draw_lights(self, camera, screen):
        """
        Dessine les effets de lumière (avec occlusion) en adaptant
        le rayon des lumières à la taille de tuile courante.
        """
        # Calcul du factor d'échelle entre la taille standard et la première tile size
        first_size = next(iter(self.tile_sizes.values()), self.standard_tile_size)
        scale = self.standard_tile_size / first_size

        # Création du masque sombre semi-transparent
        light_mask = pygame.Surface(screen.get_size(), flags=pygame.SRCALPHA)
        light_mask.fill((0, 0, 0, self.shadow_alpha))

        now = time.time()
        for lt in self.lights:
            if not lt["visible"]:
                continue
            cx, cy = lt["pos"]
            bx, by = camera.apply_point(cx, cy)

            # Rayon de base mis à l'échelle
            base_r = lt["base_radius"] * scale
            radius_var = lt.get("radius_var", 3) * scale

            if lt["blink"]:
                # Effet de clignotement
                phase = (now - lt["start_time"]) * 2
                flick = base_r + math.sin(phase) * radius_var + (random.random() - 0.5) * 5
                for r in range(int(flick), 0, -1):
                    f = 1 - (r / flick)
                    col = tuple(int(c * f) for c in lt["base_color"])
                    a = int((1 - f) * self.shadow_alpha)
                    pygame.draw.circle(light_mask, (*col, a), (bx, by), r)
            else:
                # Lumière fixe
                for r in range(int(base_r), 0, -1):
                    f = 1 - (r / base_r)
                    col = tuple(int(c * f) for c in lt["base_color"])
                    a = int((1 - f) * self.shadow_alpha)
                    pygame.draw.circle(light_mask, (*col, a), (bx, by), r)

        # On applique le masque sur l'écran
        screen.blit(light_mask, (0, 0))

