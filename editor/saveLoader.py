import json
import pygame
import tkinter as tk
from tkinter import filedialog
from editor.utils import TileMap, Tools, Tile, Layer, CollisionRect

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
        layers_data = []
        for layer in level_design.dataManager.layers:
            layer_dict = {
                "opacity": layer.opacity,
                "tiles": []
            }
            for tile in layer.tiles:
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
            collision_dict = {
                "type": collision.type,
                "name": collision.name,
                "rect": [collision.rect.x, collision.rect.y, collision.rect.width, collision.rect.height],
                "color": list(collision.color)
            }
            collision_rects_data.append(collision_dict)

        # Sauvegarde des TileMap de la palette
        tilemaps_data = []
        for tilemap in level_design.tilePalette.Maps:
            tilemap_data = {
                "name": tilemap.name,
                "filepath": tilemap.filepath,
                "tileSize": tilemap.tileSize,
                "colorKey": list(tilemap.colorKey) if tilemap.colorKey else None,
                "zoom": tilemap.zoom,
                "panningOffset": tilemap.panningOffset
            }
            tilemaps_data.append(tilemap_data)

        data = {
            "layers": layers_data,
            "currentLayer": level_design.dataManager.currentLayer,
            "collisionRects": collision_rects_data,
            "currentTool": level_design.dataManager.currentTool.name,
            "viewport": {
                "panningOffset": level_design.viewport.panningOffset,
                "zoom": level_design.viewport.zoom
            },
            "tilePalette": {
                "currentTileMapIndex": level_design.tilePalette.currentTileMap,
                "tileMaps": tilemaps_data
            }
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

        print("✅ Chargement réussi !")
