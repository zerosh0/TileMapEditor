import json
import pygame
import tkinter as tk
from tkinter import filedialog
from editor.utils import Colors, Light, LocationPoint, TileMap, Tools, Tile, Layer, CollisionRect
from dataclasses import is_dataclass

class SaveLoadManager:
    @staticmethod
    def choose_save_file():
        root = tk.Tk()
        root.withdraw()  # Masquer la fenêtre principale
        filename = filedialog.asksaveasfilename(
            title="Enregistrer le niveau",
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json")]
        )
        return filename

    @staticmethod
    def choose_load_file():
        root = tk.Tk()
        root.withdraw()  # Masquer la fenêtre principale
        filename = filedialog.askopenfilename(
            title="Ouvrir le niveau",
            filetypes=[("Fichiers JSON", "*.json")]
        )
        return filename
    
    
    @staticmethod
    def choose_TileMap():
        root = tk.Tk()
        root.withdraw()  # Masquer la fenêtre principale
        filename = filedialog.askopenfilename(
            title="Ouvrir le niveau",
        )
        return filename

    @staticmethod
    def save(level_design,file_path=None):
        # Sauvegarde des layers et de leurs tiles
        corrupted_data=False
        layers_data = []
        for layer in level_design.dataManager.layers:
            if not (is_dataclass(layer) and isinstance(layer, Layer)): 
                print(f"{Colors.RED}Données corrompues (TileMap){Colors.RESET}")
                corrupted_data=True
                continue
            layer_dict = {
                "opacity": layer.opacity,
                "tiles": []
            }
            for tile in layer.tiles:
                if not (is_dataclass(tile) and isinstance(tile, Tile)): 
                    print(f"{Colors.RED}Données corrompues (Tile){Colors.RESET}")
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
                corrupted_data=True
                continue
            collision_dict = {
                "type": collision.type,
                "name": collision.name,
                "rect": [collision.rect.x, collision.rect.y, collision.rect.width, collision.rect.height],
                "color": list(collision.color)
            }
            collision_rects_data.append(collision_dict)

         # Sauvegarde des points de localisation
        location_point_data = []
        for point in level_design.dataManager.locationPoints:
            if not (is_dataclass(point) and isinstance(point, LocationPoint)): 
                print(f"{Colors.RED}Données corrompues (Location Point){Colors.RESET}")
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
            "backgroundIndex": level_design.dataManager.current_bg_index,
            "globalIllumination": level_design.DrawManager.slider_gi.value,
            "updateSchedule": level_design.DrawManager.current_schedule,
            "showLights": level_design.DrawManager.chk_states[0],
            "showCollisions": level_design.DrawManager.chk_states[1],
            "showLocationPoints": level_design.DrawManager.chk_states[2]
        }

        data = {
            "layers": layers_data,
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
            "settings": settings
        }
        if not file_path:
            file_path = SaveLoadManager.choose_save_file()
            if not file_path:
                print("Sauvegarde annulée.")
                return

        try:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            print("✅ Sauvegarde réussie !")
        except Exception as e:
            print("Erreur lors de la sauvegarde :", e)
        if corrupted_data:
            print(f"{Colors.YELLOW}⚠️ Certaines données étaient corrompues et n'ont pas été sauvegardées.{Colors.RESET}")



    @staticmethod
    def open(level_design):
        file_path = SaveLoadManager.choose_TileMap()
        if not file_path:
            print("Chargement annulé.")
            return
        return file_path
    
    @staticmethod
    def load(level_design):
        file_path = SaveLoadManager.choose_load_file()
        if not file_path:
            print("Chargement annulé.")
            return

        try:
            with open(file_path, "r") as file:
                data = json.load(file)
        except Exception as e:
            print("Erreur lors du chargement :", e)
            return



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
                color=tuple(collision_dict["color"])
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
            level_design.dataManager.current_bg_index = bg_idx
        gi = settings.get("globalIllumination")
        if gi is not None:
            level_design.DrawManager.slider_gi.value = gi
            level_design.DrawManager.shadow_alpha = int(gi * 255)

        upd = settings.get("updateSchedule")
        if upd is not None:
            level_design.DrawManager.current_schedule = upd

        lights = settings.get("showLights")
        coll  = settings.get("showCollisions")
        locs  = settings.get("showLocationPoints")
        if lights is not None:   level_design.DrawManager.chk_states[0] = lights
        if coll is not None:     level_design.DrawManager.chk_states[1] = coll
        if locs is not None:     level_design.DrawManager.chk_states[2] = locs

        level_design.DrawManager.last_bg_index = None
        print("✅ Chargement réussi !")
