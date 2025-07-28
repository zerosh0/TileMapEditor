import json
import os
import sys
from typing import Dict
import uuid
import pygame
from editor.blueprint_editor.blueprints.b_logic import SequenceNode
from editor.blueprint_editor.node import NODE_REGISTRY, Node
from editor.blueprint_editor.system import BlueprintEditor
from editor.ui.FileDialog import FileDialog
from editor.core.utils import AnimatedTile, Colors, Light, LocationPoint, TileMap, Tools, Tile, Layer, CollisionRect
from dataclasses import is_dataclass

class SaveLoadManager:
    def __init__(self, screen, nm, theme=None):
        self.screen = screen
        self.nm     = nm
        self.theme  = theme
        self.running=True

    def _run_dialog(self,mode="open", default_name=""):
        # crée ta FileDialog
        self._result = None
        self.running = True
        dlg = FileDialog(
            (100,100,600,400),
            self.nm,
            mode=mode,
            icon_dir="./Assets/ui/icones/fileDialog/",
            on_confirm=lambda p: setattr(self, '_result', p),
            on_cancel=lambda : setattr(self, 'running', False),
            default_save_name=default_name
        )
        # boucle modale : tourne jusqu’à ce que _result soit défini
        clock = pygame.time.Clock()
        background = self.screen.copy()
        while self.running:
            dt = clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                else:
                    dlg.handle_event(e)
            self.screen.blit(background, (0, 0))
            dlg.update_animation(dt)
            self.nm.update(dt)
            dlg.draw(self.screen)
            self.nm.draw(self.screen)
            pygame.display.flip()
            # dès qu’on a un résultat (path ou None), on sort
            if self._result is not None:
                self.running = False
        return self._result




    def save(self,level_design,file_path=None):
        # Sauvegarde des layers et de leurs tiles
        corrupted_data=False
        layers_data = []
        for layer in level_design.dataManager.layers:
            if not (is_dataclass(layer) and isinstance(layer, Layer)): 
                print(f"{Colors.RED}Données corrompues (TileMap){Colors.RESET}")
                level_design.nm.notify('error', 'Erreur', 'Données corrompues (TileMap)')
                corrupted_data=True
                continue
            layer_dict = {
                "opacity": layer.opacity,
                "tiles": []
            }
            for tile in layer.tiles:
                if not (is_dataclass(tile) and isinstance(tile, Tile)): 
                    print(f"{Colors.RED}Données corrompues (Tile){Colors.RESET}")
                    level_design.nm.notify('error', 'Erreur', 'Données corrompues (Tile)')
                    corrupted_data=True
                    continue
                tile_dict = {
                    "TileMap": tile.TileMap,
                    "x": tile.x,
                    "y": tile.y,
                    "Originalx": tile.Originalx,
                    "Originaly": tile.Originaly,
                    "rotation": tile.rotation,
                    "flipHorizontal": tile.flipHorizontal,
                    "flipVertical": tile.flipVertical
                }
                layer_dict["tiles"].append(tile_dict)
            layers_data.append(layer_dict)

        # Sauvegarde des rectangles de collision
        collision_rects_data = []
        for collision in level_design.dataManager.collisionRects:
            if not (is_dataclass(collision) and isinstance(collision, CollisionRect)): 
                print(f"{Colors.RED}Données corrompues (Collision Rect){Colors.RESET}")
                level_design.nm.notify('error', 'Erreur', 'Données corrompues (Collision Rect)')
                corrupted_data=True
                continue
            collision_dict = {
                "type": collision.type,
                "name": collision.name,
                "rect": [collision.rect.x, collision.rect.y, collision.rect.width, collision.rect.height],
                "color": list(collision.color),
                "id": collision.id
            }
            collision_rects_data.append(collision_dict)

         # Sauvegarde des points de localisation
        location_point_data = []
        for point in level_design.dataManager.locationPoints:
            if not (is_dataclass(point) and isinstance(point, LocationPoint)): 
                print(f"{Colors.RED}Données corrompues (Location Point){Colors.RESET}")
                level_design.nm.notify('error', 'Erreur', 'Données corrompues (Location Point)')
                corrupted_data=True
                continue
            location_dict = {
                "type": point.type,
                "name": point.name,
                "rect": [point.rect.x, point.rect.y, point.rect.width, point.rect.height],
                "color": list(point.color)
            }
            location_point_data.append(location_dict)
        # Sauvegarde des lumières
        light_data = []
        for light in level_design.dataManager.lights:
            if not (is_dataclass(light) and isinstance(light, Light)): 
                print(f"{Colors.RED}Données corrompues (Light){Colors.RESET}")
                level_design.nm.notify('error', 'Erreur', 'Données corrompues (Light)')
                corrupted_data=True
                continue
            light_dict = {
                "x": light.x,
                "y": light.y,
                "radius": light.radius,
                "color": list(light.color),
                "blink": light.blink
                
            }
            light_data.append(light_dict)

        # Sauvegarde des TileMap de la palette
        tilemaps_data = []
        for tilemap in level_design.tilePalette.Maps:
            if not (is_dataclass(tilemap) and isinstance(tilemap, TileMap)): 
                print(f"{Colors.RED}Données corrompues (TileMap){Colors.RESET}")
                level_design.nm.notify('error', 'Erreur', 'Données corrompues (TileMap)')
                corrupted_data=True
                continue
            tilemap_data = {
                "name": tilemap.name,
                "filepath": tilemap.filepath,
                "tileSize": tilemap.tileSize,
                "colorKey": list(tilemap.colorKey) if tilemap.colorKey else None,
                "zoom": tilemap.zoom,
                "panningOffset": tilemap.panningOffset
            }
            tilemaps_data.append(tilemap_data)

        settings = {
            "backgroundIndex": level_design.settings.parallax_index,
            "globalIllumination": level_design.settings.global_illum,
            "start_mode": level_design.settings.start_mode,
            "showLights": level_design.settings.display_lights,
            "showCollisions": level_design.settings.show_collisions,
            "showLocationPoints": level_design.settings.show_location_points,
            "playerSpawnPoint": level_design.settings.player_spawn_point
        }
        animations_data = []
        for name, anim in level_design.animations.animations.items():
            kfs = []
            for kf in anim.timeline.keyframes:
                kfs.append({
                    "tile_map":   kf.tile.TileMap,
                    "x":          kf.tile.x,
                    "y":          kf.tile.y,
                    "layer":      kf.layer,
                    "time":       kf.time,
                    "Originalx":          kf.tile.Originalx,
                    "Originaly":          kf.tile.Originaly,
                    "rotation":   kf.tile.rotation,
                    "flipH":      kf.tile.flipHorizontal,
                    "flipV":      kf.tile.flipVertical,
                })
            animations_data.append({
                "name":      name,
                "end":       anim.timeline.end,
                "speed":     anim.speed,
                "loop": anim.timeline.loop,
                "play": anim.timeline.playing,
                "keyframes": kfs
            })

        if level_design.dataManager.currentTool == None:
            level_design.dataManager.currentTool=Tools.Draw

        data = {
            "layers": layers_data,
            "animations": animations_data,
            "currentLayer": level_design.dataManager.currentLayer,
            "collisionRects": collision_rects_data,
            "locationPoint":location_point_data,
            "lights":light_data,
            "currentTool": level_design.dataManager.currentTool.name,
            "viewport": {
                "panningOffset": level_design.viewport.panningOffset,
                "zoom": level_design.viewport.zoom
            },
            "tilePalette": {
                "currentTileMapIndex": level_design.tilePalette.currentTileMap,
                "tileMaps": tilemaps_data
            },
            "settings": settings,
            "levelGraph": None
        }

        if not file_path:
            file_path = self._run_dialog(mode="save")
            if not file_path:
                print("Sauvegarde annulée.")
                level_design.nm.notify('info', 'Information', 'Sauvegarde annulée !',duration=1.0)
                return
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

        # dérivation du chemin de graph :
        lg_dir = os.path.dirname(file_path)
        level_name = os.path.splitext(os.path.basename(file_path))[0]
        graph_fp = os.path.join(lg_dir, f"{level_name}_graph.lvg")
        data["levelGraph"] = graph_fp

        try:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            graph_data = {"graphs": []}
            for rect in level_design.dataManager.collisionRects:
                if rect.graph:
                    be: BlueprintEditor = rect.graph
                    nodes_ser = []
                    conns_ser = []
                    # nœuds
                    for n in be.nodes:
                        label = next(
                            (key for key,(cls,_) in NODE_REGISTRY.items() if cls is type(n)),
                            type(n).__name__   # fallback si jamais introuvable
                        )
                        nodes_ser.append({
                            "rect_id": rect.id,
                            "node_id": n.title + "_" + str(n.x) + "_" + str(n.y),
                            "label": label,
                            "pos": [n.x, n.y],
                            "properties": n.properties,
                        })
                    # connexions
                    for out_p, in_p in be.connections:
                        conns_ser.append({
                            "rect_id": rect.id,
                            "out_node": out_p.node.title + "_" + str(out_p.node.x) + "_" + str(out_p.node.y),
                            "out_pin": out_p.name,
                            "in_node": in_p.node.title + "_" + str(in_p.node.x) + "_" + str(in_p.node.y),
                            "in_pin": in_p.name,
                        })
                    graph_data["graphs"].append({
                        "rect_id": rect.id,
                        "nodes": nodes_ser,
                        "connections": conns_ser,
                    })
            # écriture du fichier de graph
            with open(graph_fp, "w") as gf:
                json.dump(graph_data, gf, indent=4)
            print(f"✅ Sauvegarde graph → {file_path}, {graph_fp}")
            print("✅ Sauvegarde réussie !")
            level_design.nm.notify('success', 'Success', 'Sauvegarde réussie !',duration=1.0)
            level_design.settings.path=file_path
        except Exception as e:
            print("Erreur lors de la sauvegarde :", e)
            level_design.nm.notify('error', 'Erreur', "Erreur lors de la sauvegarde (voir la console)")
        if corrupted_data:
            print(f"{Colors.YELLOW}⚠️ Certaines données étaient corrompues et n'ont pas été sauvegardées.{Colors.RESET}")
            level_design.nm.notify('warning', 'Attention', "Certaines données étaient corrompues et n'ont pas été sauvegardées.",duration=1.0)
            



    def open(self,level_design):
        file_path = self._run_dialog()
        if not file_path:
            print("Chargement annulé.")
            level_design.nm.notify('info', 'Information', 'Chargement annulé.',duration=1.0)
            return
        return file_path
    

    def load(self,level_design,file_path=None,init=False):
        if not file_path:
            file_path = self._run_dialog()
            if not file_path:
                print("Chargement annulé.")
                level_design.nm.notify('info', 'Information', 'Chargement annulé.',duration=1.0)
                return

        try:
            with open(file_path, "r") as file:
                data = json.load(file)
        except Exception as e:
            print("Erreur lors du chargement :", e)
            level_design.nm.notify('error', 'Erreur', 'Erreur lors du chargement (voir la console).',duration=1.0)
            return


        level_design.clear_cache()
        # Reconstruction des layers et de leurs tiles
        layers = []
        for layer_data in data["layers"]:
            tiles = []
            for tile_data in layer_data.get("tiles", []):
                tile = Tile(
                    TileMap=tile_data["TileMap"],
                    x=tile_data["x"],
                    y=tile_data["y"],
                    Originalx=tile_data["Originalx"],
                    Originaly=tile_data["Originaly"],
                    rotation=tile_data["rotation"],
                    flipHorizontal=tile_data["flipHorizontal"],
                    flipVertical=tile_data["flipVertical"]
                )
                tiles.append(tile)
            layer = Layer(opacity=layer_data.get("opacity", 1.0), tiles=tiles)
            layers.append(layer)
        level_design.dataManager.layers = layers

        level_design.dataManager.currentLayer = data["currentLayer"]

        # Reconstruction des CollisionRect
        collision_rects = []
        for collision_dict in data["collisionRects"]:
            collision = CollisionRect(
                type=collision_dict["type"],
                name=collision_dict["name"],
                rect=pygame.Rect(*collision_dict["rect"]),
                color=tuple(collision_dict["color"]),
                id=collision_dict.get("id", str(uuid.uuid4()))
            )
            collision_rects.append(collision)
        level_design.dataManager.collisionRects = collision_rects

        # Reconstruction des LocationPoint
        locationPoints = []
        if data.get("locationPoint"):
            for point in data["locationPoint"]:
                location = LocationPoint(
                    type=point["type"],
                    name=point["name"],
                    rect=pygame.Rect(*point["rect"]),
                    color=tuple(point["color"])
                )
                locationPoints.append(location)
            level_design.dataManager.locationPoints = locationPoints

        lights = []
        if data.get("lights"):
            for light in data["lights"]:
                new_light = Light(
                    x=light["x"],
                    y=light["y"],
                    radius=light["radius"],
                    color=tuple(light["color"]),
                    blink=light["blink"]
                )
                lights.append(new_light)
            level_design.dataManager.lights = lights
        level_design.dataManager.currentTool = Tools[data["currentTool"]]

        level_design.viewport.panningOffset = data["viewport"]["panningOffset"]
        level_design.viewport.zoom = data["viewport"]["zoom"]

        # Reconstruction de la TilePalette et de ses TileMap
        tile_palette_data = data["tilePalette"]
        level_design.tilePalette.currentTileMap = tile_palette_data["currentTileMapIndex"]

        tilemaps = []
        for tm_data in tile_palette_data.get("tileMaps", []):
            image = pygame.image.load(tm_data["filepath"]).convert_alpha()
            if tm_data["colorKey"]:
                image.set_colorkey(tuple(tm_data["colorKey"]))
            tilemap = TileMap(
                name=tm_data["name"],
                filepath=tm_data["filepath"],
                tileSize=tm_data["tileSize"],
                image=image,
                colorKey=tm_data["colorKey"],
                zoomedImage=image,
                zoom=tm_data["zoom"],
                panningOffset=tm_data["panningOffset"]
            )
            tilemaps.append(tilemap)
        level_design.tilePalette.Maps = tilemaps
        level_design.DrawManager.updateLayerText(data["currentLayer"])
        settings = data.get("settings", {})

        bg_idx = settings.get("backgroundIndex")
        if bg_idx is not None:
            level_design.settings.parallax_index = bg_idx
        gi = settings.get("globalIllumination")
        if gi is not None:
            level_design.settings.global_illum = gi
            level_design.DrawManager.shadow_alpha = int(gi * 255)

        spawnPoint = settings.get("playerSpawnPoint")
        if spawnPoint is not None:
            level_design.settings.player_spawn_point=spawnPoint

            
        lights = settings.get("showLights")
        coll  = settings.get("showCollisions")
        locs  = settings.get("showLocationPoints")
        if lights is not None:   level_design.settings.display_lights = lights
        if coll is not None:     level_design.settings.show_collisions = coll
        if locs is not None:     level_design.settings.show_location_points = locs


        level_design.animations.animations.clear()
        level_design.animations.current_name = None
        level_design.animations.anim_menu.text = "Aucune"
        level_design.animations.anim_menu.text_surf = level_design.animations.button_font.render(
            "Aucune", True, level_design.animations.anim_menu.text_color
        )


        for anim_data in data.get("animations", []):
            name = anim_data["name"]
            end  = float(anim_data["end"])

            level_design.animations.create(name, end,on_load=True)
            anim = level_design.animations.animations[name]


            anim.speed            = float(anim_data.get("speed", 1.0))
            anim.timeline.loop    = bool(anim_data.get("loop", False))
            anim.timeline.playing = bool(anim_data.get("play", False))

            if anim.timeline.playing and anim.timeline.current >= anim.timeline.end:
                anim.timeline.current = anim.timeline.start


            for kf in anim_data.get("keyframes", []):

                tile = Tile(
                    TileMap        = kf["tile_map"],
                    x              = kf["x"],
                    y              = kf["y"],
                    Originalx      = kf["Originalx"],
                    Originaly      = kf["Originaly"],
                    rotation       = kf["rotation"],
                    flipHorizontal = kf["flipH"],
                    flipVertical   = kf["flipV"]
                )
                anim_tile = AnimatedTile(
                    anim_id = name,
                    tile    = tile,
                    layer   = kf["layer"],
                    time = kf["time"]
                )
                anim_tile.time = float(kf["time"])
                anim.timeline.add_keyframe(anim_tile)

            anim.timeline.compute_scale()

        if (level_design.animations.current_name is None
                and level_design.animations.animations):
            first_name = next(iter(level_design.animations.animations))
            level_design.animations.set_current(first_name)
        elif not level_design.animations.animations:
            level_design.animations.create("animation_1",2.0)
            level_design.animations.get_current_anim().timeline.active=False

        level_design.settings.path=file_path
        raw_graph_fp = data.get("levelGraph")
        graph_fp = None
        if raw_graph_fp:
            if os.path.isabs(raw_graph_fp) and os.path.isfile(raw_graph_fp):
                graph_fp = raw_graph_fp
            else:
                base_dir = os.path.dirname(file_path)
                rel = os.path.join(base_dir,os.path.basename(raw_graph_fp))
                if os.path.isfile(rel):
                    graph_fp = rel

        if graph_fp:
            with open(graph_fp, "r") as gf:
                graph_data = json.load(gf)
            # pour chaqueCollisionRect, on cherche son graph
            for graph in graph_data.get("graphs", []):
                rect_id = graph["rect_id"]
                # retrouver l'objet CollisionRect chargé
                rect_obj = next((r for r in level_design.dataManager.collisionRects 
                                if r.id == rect_id), None)
                if not rect_obj:
                    continue
                # créer un BlueprintEditor lié à ce rect
                be = BlueprintEditor(level_design)
                # recréer les nodes
                id2node: Dict[str, Node] = {}
                for nd in graph["nodes"]:
                    label = nd.get("label")
                    if label not in NODE_REGISTRY:
                        print(f"⚠️ Noeud \"{label}\" inconnu dans le registry !")
                        continue

                    cls = NODE_REGISTRY[label][0]
                    # Instanciation
                    n = cls(tuple(nd["pos"]), be, properties=nd.get("properties", {}))
                    be.add_node(n)
                    id2node[nd["node_id"]] = n

                    # **IMPORTANT** : recréer les pins exec pour SequenceNode **ici**, juste après la création
                    if isinstance(n, SequenceNode):
                        # Collecte tous les out_pin qu'on doit recréer pour ce node
                        out_pins = {
                            c["out_pin"]
                            for c in graph["connections"]
                            if c["out_node"] == nd["node_id"] and c["out_pin"].startswith("out")
                        }
                        # Extrait les indices numériques
                        indices = [int(name[3:]) for name in out_pins]
                        max_idx = max(indices) if indices else -1

                        # Appelle _add_exec_pin() autant de fois que nécessaire
                        for _ in range(max_idx + 1):
                            n._add_exec_pin()

                # 2) Reconstruction des connexions
                for c in graph["connections"]:
                    out_n = id2node.get(c["out_node"])
                    in_n  = id2node.get(c["in_node"])
                    if not (out_n and in_n):
                        continue

                    try:
                        out_pin = next(p for p in out_n.outputs if p.name == c["out_pin"])
                        in_pin  = next(p for p in in_n.inputs  if p.name == c["in_pin"])
                    except StopIteration:
                        print(f"⚠️ Impossible de reconnecter "
                            f"{c['out_node']}.{c['out_pin']} → "
                            f"{c['in_node']}.{c['in_pin']}")
                        continue

                    out_pin.connect(in_pin)
                    be.connections.append((out_pin, in_pin))
                # rattacher le graph recréé au rect
                rect_obj.graph = be
        elif graph_fp is not None:
            print(f"⚠️ Pas de fichier graph trouvé à {graph_fp}")
            level_design.nm.notify('warning', 'Attention', f"Pas de fichier graph trouvé à {graph_fp}",duration=1.5)
        elif raw_graph_fp!=None:
            print(f"⚠️ Pas de fichier graph trouvé (abs. ou relatif) : {raw_graph_fp}")
            level_design.nm.notify(
                'warning', 'Attention',
                f"Pas de fichier graph trouvé : {raw_graph_fp}", duration=1.5
            )
        print("✅ Chargement réussi !")
        level_design.DrawManager.last_bg_index = None
        level_design.settings.load_settings()
        level_design.DrawManager.settings=level_design.settings
        level_design.nm.notify('success', 'Success', 'Chargement réussi !',duration=1)
        if not init:
            level_design.level_loaded=True
        
