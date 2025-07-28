import copy
import json
from pathlib import Path
import re
import time
from editor.animations.animation import AnimationManager
from editor.core.history_manager import HistoryManager
from editor.core.utils import AnimatedTile, Layer, Light, LocationPoint,Tile,Tools,Axis,CollisionRect
import random
from typing import List
import pygame



class DataManager():
    def __init__(self,history : HistoryManager,settings,animation : AnimationManager):
        self.history=history
        self.layers=[Layer() for _ in range(9)]
        self.collisionRects: list[CollisionRect]=[]
        self.locationPoints: list[LocationPoint]=[]
        self.lights: list[Light]=[]
        self.currentLayer=0
        self.currentTiles: List[Tile]=[]
        self.currentTool: Tools = Tools.Draw
        self.selectionPalette=()
        self.selectionViewPort=()
        self.selectedElement: CollisionRect | LocationPoint | None=None
        self.lastAddedTileState = None
        self.lastAddTime = 0
        self.show_settings=False
        self.backgrounds: list[dict] = []
        self.settings=settings
        self.animation=animation
        self.load_backgrounds("./Assets/backgrounds.json")
        self.game_engine=None

    def load_backgrounds(self, json_path: str):
        try:
            data = json.load(Path(json_path).open(encoding="utf-8"))
            self.backgrounds = data.get("backgrounds", [])
            # trouver l’index du default
            default_name = data.get("default")
            self.settings.backgrounds=[]
            for i, bg in enumerate(self.backgrounds):
                self.settings.backgrounds.append(bg.get("name"))
                if bg.get("name") == default_name:
                    self.settings.parallax_index = i

        except Exception as e:
            print(f"Erreur de chargement des backgrounds: {e}")
            self.backgrounds = []
            self.settings.parallax_index = 0

    def get_current_background(self) -> dict | None:
        if not self.backgrounds:
            return None
        return self.backgrounds[self.settings.parallax_index]

    def bg_next(self):
        if not self.backgrounds:
            return
        self.settings.parallax_index = (self.settings.parallax_index + 1) % len(self.backgrounds)

    def bg_prev(self):
        if not self.backgrounds:
            return
        self.settings.parallax_index = (self.settings.parallax_index - 1) % len(self.backgrounds)

    def addLight(self, pos, radius,viewport):
        x,y=viewport.toMapCoords(pos)
        new_light= Light(
            x=x,
            y=y,
            radius=radius
        )
        self.lights.append(new_light)
        self.selectedElement=self.lights[-1]
        self.history.RegisterAddLight(self.lights[-1])

    def get_background_by_name(self, name: str) -> dict | None:
        for bg in self.backgrounds:
            if bg.get("name") == name:
                return bg
        return None


    def get_scaled_collision_rects(self,a) -> list[pygame.Rect]:
        """Les rectangles de collision en coordonnées monde."""
        return self.collisionRects

    def get_location_point_name(self):
        for location in self.locationPoints:
            yield location.name

    def get_spawn_point(self,viewport):
        map_offset,zoom=viewport.panningOffset,viewport.zoom
        for location_point in self.locationPoints:
            if location_point.name==self.settings.player_spawn_point:
                return (location_point.rect.x,location_point.rect.y)
                #return (int(map_offset[0] + location_point.rect.x * zoom),int(map_offset[1] + location_point.rect.y * zoom + 30))
        return (0,0)


    def ChangeSelectedCollisionRect(self,viewport,locationPointImage):
        self.selectedElement=None
        for rect in self.collisionRects:
            if rect.collidePoint(pygame.mouse.get_pos(),viewport.panningOffset,viewport.zoom):
                self.selectedElement=rect
        for light in self.lights:
            if light.collidePoint(pygame.mouse.get_pos(),viewport.panningOffset,viewport.zoom):
                self.selectedElement=light
        for point in self.locationPoints:
            if point.collidePoint(pygame.mouse.get_pos(),viewport.panningOffset,viewport.zoom,locationPointImage):
                self.selectedElement=point


    def getCenterSelectionViewport(self):
        if not self.currentTiles:
            return None, None
        
        if len(self.currentTiles) == 1:
            return self.currentTiles[0].x, self.currentTiles[0].y
        min_x = min(tile.x for tile in self.currentTiles)
        max_x = max(tile.x for tile in self.currentTiles)
        min_y = min(tile.y for tile in self.currentTiles)
        max_y = max(tile.y for tile in self.currentTiles)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        return center_x, center_y


    def flipCurrentTiles(self,axis : Axis):
        if len(self.currentTiles)==1:
            self.currentTiles[0].flip(axis)
        else:
            print("Impossible de flip une sélection")

    def RotateCurrentTiles(self):
        if not self.currentTiles:
            return
        if len(self.currentTiles) == 1:
            self.currentTiles[0].rotate(90)
            return
        min_x = min(tile.Originalx for tile in self.currentTiles)
        min_y = min(tile.Originaly for tile in self.currentTiles)
        max_x = max(tile.Originalx for tile in self.currentTiles)
        max_y = max(tile.Originaly for tile in self.currentTiles)
        width = max_x - min_x + 1
        height = max_y - min_y + 1

        TempTiles = []
        for y in range(height):
            for x in range(width):
                # Calcul de l'index pour accéder à self.currentTiles
                original_tile_index = (y * width + x)
                if original_tile_index < len(self.currentTiles):
                    # Création d'une nouvelle tuile en inversant les lignes et les colonnes
                    cp=self.currentTiles[original_tile_index]
                    NewTile = Tile(cp.TileMap,y,x,cp.Originalx,cp.Originaly,cp.rotation+90)
                    TempTiles.append(NewTile)

        self.currentTiles = TempTiles


    def ChangeCurrentTilesSelection(self, tilePalette):
        tileMap = tilePalette.GetCurrentTileMap()
        tileSize = tileMap.tileSize
        map_width = tileMap.image.get_width() // tileSize
        map_height = tileMap.image.get_height() // tileSize

        self.relativeStart = tilePalette.toGrid(self.selectionPalette[0],tileSize)
        self.relativeEnd = tilePalette.toGrid(self.selectionPalette[1],tileSize)

        # Déterminer les bornes de la sélection en tenant compte des limites de la tilemap
        x_min = max(0, min(self.relativeStart[0], self.relativeEnd[0]))
        y_min = max(0, min(self.relativeStart[1], self.relativeEnd[1]))
        x_max = min(map_width - 1, max(self.relativeStart[0], self.relativeEnd[0]))
        y_max = min(map_height - 1, max(self.relativeStart[1], self.relativeEnd[1]))

        # Stocker les tuiles sélectionnées
        self.currentTiles = []
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                tile = Tile(tileMap.name, 0, 0, x, y)
                self.currentTiles.append(tile)

        
    def RemoveCurrentTilesSelection(self, viewport):
        # calcul de la sélection en coordonnées grille
        self.relativeStart = viewport.toGrid(self.selectionViewPort[0])
        self.relativeEnd   = viewport.toGrid(self.selectionViewPort[1])
        x_min = min(self.relativeStart[0], self.relativeEnd[0])
        y_min = min(self.relativeStart[1], self.relativeEnd[1])
        x_max = max(self.relativeStart[0], self.relativeEnd[0])
        y_max = max(self.relativeStart[1], self.relativeEnd[1])
        Tiles=[]
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                Tiles.append((x,y))
        self.history.RegisterRemoveTiles(self.currentLayer,Tiles,self)
        for x,y in Tiles:
            self.RemoveTile(x,y,register=False)

    def FillCurrentTilesSelection(self, viewport):
        # calcul de la sélection
        self.relativeStart = viewport.toGrid(self.selectionViewPort[0])
        self.relativeEnd   = viewport.toGrid(self.selectionViewPort[1])
        x_min = min(self.relativeStart[0], self.relativeEnd[0])
        y_min = min(self.relativeStart[1], self.relativeEnd[1])
        x_max = max(self.relativeStart[0], self.relativeEnd[0])
        y_max = max(self.relativeStart[1], self.relativeEnd[1])

        # mode record ? on enregistre juste les AnimatedTile
        if getattr(self.animation.get_current_anim().timeline, "record", False):
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    new = copy.deepcopy(self.currentTiles[0])
                    new.x = x; new.y = y
                    anim_tile = AnimatedTile(
                        anim_id = self.animation.get_current_anim().name,
                        time    = 0.0,
                        tile    = new,
                        layer   = self.currentLayer
                    )
                    self.animation.get_current_anim().record(anim_tile, self)
            return

        # sinon, remplissage statique + historisation
        new_tiles = []; old_tiles = []
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                new = copy.deepcopy(self.currentTiles[0])
                new.x = x; new.y = y
                old = self.getCurrentLayer().addOrReplaceTile(new)
                if old != "":
                    new_tiles.append(new)
                    old_tiles.append(old)
        if new_tiles:
            self.history.RegisterAddTiles(self.currentLayer, new_tiles, old_tiles)


    def RandomCurrentTilesSelection(self, viewport):
        # calcul de la sélection
        self.relativeStart = viewport.toGrid(self.selectionViewPort[0])
        self.relativeEnd   = viewport.toGrid(self.selectionViewPort[1])
        x_min = min(self.relativeStart[0], self.relativeEnd[0])
        y_min = min(self.relativeStart[1], self.relativeEnd[1])
        x_max = max(self.relativeStart[0], self.relativeEnd[0])
        y_max = max(self.relativeStart[1], self.relativeEnd[1])

        # mode record ? on enregistre juste les AnimatedTile
        if getattr(self.animation.get_current_anim().timeline, "record", False):
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    new = copy.deepcopy(random.choice(self.currentTiles))
                    new.x = x; new.y = y
                    anim_tile = AnimatedTile(
                        anim_id = self.animation.get_current_anim().name,
                        time    = 0.0,
                        tile    = new,
                        layer   = self.currentLayer
                    )
                    self.animation.get_current_anim().record(anim_tile, self)
            return

        # sinon, remplissage aléatoire statique + historisation
        new_tiles = []; old_tiles = []
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                new = copy.deepcopy(random.choice(self.currentTiles))
                new.x = x; new.y = y
                old = self.getCurrentLayer().addOrReplaceTile(new)
                if old != "":
                    new_tiles.append(new)
                    old_tiles.append(old)
        if new_tiles:
            self.history.RegisterAddTiles(self.currentLayer, new_tiles, old_tiles)



    def UpdateCurrentTiles(self, viewport):
        if not self.currentTiles:
            return


        # Utiliser les coordonnées d'origine pour calculer la zone de la sélection sur la tilemap
        x_min = min(tile.Originalx for tile in self.currentTiles)
        y_min = min(tile.Originaly for tile in self.currentTiles)
        x_max = max(tile.Originalx for tile in self.currentTiles)
        y_max = max(tile.Originaly for tile in self.currentTiles)
        width = x_max - x_min + 1
        height = y_max - y_min + 1

        # Convertir la position de la souris en coordonnées de grille (pour centrer la sélection)
        mouse_x, mouse_y = viewport.toGrid(pygame.mouse.get_pos())
        offset_x = mouse_x - (width // 2)
        offset_y = mouse_y - (height // 2)

        # Pour la rotation, supposons ici qu'une rotation uniforme est appliquée à toute la sélection.
        # On récupère l'angle de rotation (en degrés) de la première tuile.
        rotation = self.currentTiles[0].rotation % 360

        new_tiles = []
        for tile in self.currentTiles:
            # Calculer la position relative dans la sélection d'après Originalx/Originaly
            rel_x = tile.Originalx - x_min
            rel_y = tile.Originaly - y_min

            # Appliquer la transformation de rotation sur la position relative
            if rotation == 90:
                new_rel_x = rel_y
                new_rel_y = (width - 1) - rel_x
            elif rotation == 180:
                new_rel_x = (width - 1) - rel_x
                new_rel_y = (height - 1) - rel_y
            elif rotation == 270:
                new_rel_x = (height - 1) - rel_y
                new_rel_y = rel_x
            else:
                new_rel_x = rel_x
                new_rel_y = rel_y

            # Placer la tuile sur la grille de la tilemap en ajoutant l'offset calculé
            new_tile = copy.deepcopy(tile)
            new_tile.x = offset_x + new_rel_x
            new_tile.y = offset_y + new_rel_y
            new_tiles.append(new_tile)
        self.currentTiles = new_tiles



    def AddCurrentTiles(self):
        if not self.currentTiles:
            return

        if getattr(self.animation.get_current_anim().timeline, "record", False):
            for tile in self.currentTiles:
                anim_tile = AnimatedTile(
                    anim_id = self.animation.get_current_anim().name,
                    time    = 0.0,
                    tile    = tile,
                    layer   = self.currentLayer
                )
                #self.getCurrentLayer().removeTile((tile.x, tile.y))
                self.animation.get_current_anim().record(anim_tile,self)
            return

        current_tile_state = frozenset(
            (tile.x, tile.y, tile.TileMap, tile.Originalx, tile.Originaly, tile.rotation, tile.flipHorizontal, tile.flipVertical)
            for tile in self.currentTiles
        )
        current_time = time.time()
        time_threshold = 0.1 
        if self.lastAddedTileState == current_tile_state and (current_time - self.lastAddTime < time_threshold):
            return

        self.lastAddTime = current_time
        self.lastAddedTileState = current_tile_state

        oldTiles = []
        newTiles = []
        for tile in self.currentTiles:
            oldTile = self.getCurrentLayer().addOrReplaceTile(tile)
            if oldTile != "":
                oldTiles.append(oldTile)
                newTiles.append(tile)
        self.history.RegisterAddTiles(self.currentLayer, newTiles, oldTiles)


    def getCurrentLayer(self) -> Layer:
        return self.layers[self.currentLayer]
    

    def AddTile(self, tile: Tile):
        if getattr(self.animation.get_current_anim().timeline, "record", False):
            anim_tile = AnimatedTile(
                anim_id = self.animation.get_current_anim().name,
                time    = 0.0,
                tile    = tile,
                layer   = self.currentLayer
            )
            #self.getCurrentLayer().removeTile((tile.x, tile.y))
            self.animation.get_current_anim().record(anim_tile,self)
        else:
            self.history.RegisterAddTiles(self.currentLayer, [tile])
            self.getCurrentLayer().addOrReplaceTile(tile)


    def RemoveTile(self, x, y,register=True):
        tl = self.animation.get_current_anim().timeline
        if getattr(tl, "record", False):
            dummy = Tile("", x, y,0,0)  
            kf = AnimatedTile(
                anim_id = self.animation.get_current_anim().name, 
                time    = tl.current,
                tile    = dummy,
                layer   = self.currentLayer
            )

            self.animation.get_current_anim().record(kf, self)
            return
        self.getCurrentLayer().removeTile((x, y))
        if register:
            self.history.RegisterRemoveTiles(self.currentLayer, [(x,y)], self)


    def setTool(self,tool: Tools,viewport):
        if self.selectionViewPort and not tool==Tools.Draw:
            if self.currentTiles:
                if tool==Tools.Fill:
                    self.FillCurrentTilesSelection(viewport)
                elif tool==Tools.Random:
                    self.RandomCurrentTilesSelection(viewport)
            if tool==Tools.Rubber:
                self.RemoveCurrentTilesSelection(viewport)
            elif tool==Tools.Selection:
                self.AddColisionRect(viewport)
        else:
            self.currentTool=tool

    def AddLocationPoint(self, viewport, image: pygame.Surface):
        x1, y1 = viewport.toMapCoords(pygame.mouse.get_pos())
        prefix = "point_"
        indices = []
        for lp in self.locationPoints:
            m = re.match(fr"^{prefix}(\d+)$", lp.name)
            if m:
                indices.append(int(m.group(1)))

        next_idx = max(indices) + 1 if indices else 0
        new_name = f"{prefix}{next_idx}"
        new_location = LocationPoint(
            type="Player",
            name=new_name,
            rect=pygame.Rect(x1, y1, image.get_width(), image.get_height()),
            color=(255, 0, 0)
        )

        self.history.RegisterAddElement(new_location)
        self.locationPoints.append(new_location)
        self.selectedElement = new_location


    def AddColisionRect(self, viewport):
        x1, y1 = viewport.toMapCoords(self.selectionViewPort[0])
        x2, y2 = viewport.toMapCoords(self.selectionViewPort[1])
        rect_x = int(min(x1, x2))
        rect_y = int(min(y1, y2))
        rect_width = int(abs(x2 - x1))
        rect_height = int(abs(y2 - y1))
        if rect_width < 5 or rect_height < 5:
            print("Rectangle trop petit, non ajouté.")
            return
        new_collision_rect = CollisionRect(
            type="collision",
            name=f"rect_{len(self.collisionRects)}",
            rect=pygame.Rect(rect_x, rect_y, rect_width, rect_height),
            color=(255, 0, 0)
        )
        self.history.RegisterAddElement(new_collision_rect)
        self.collisionRects.append(new_collision_rect)
        self.selectedElement=self.collisionRects[-1]


    def changeCurrentLayer(self,change: int):
        self.currentLayer = (self.currentLayer + change) % 9

    def EditColor(self,new_color):
        if self.show_settings:
            return
        if self.currentTool in [Tools.LocationPoint,Tools.Light]:
            self.currentTool=Tools.Draw
        self.currentTiles=[]
        self.selectedElement.color = new_color

    def toogle_settings_display(self):
        self.show_settings= not self.show_settings