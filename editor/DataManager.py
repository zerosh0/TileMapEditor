import copy
from editor.utils import Layer,Tile,Tools,Axis,CollisionRect
import random
from typing import List
import pygame



class DataManager():
    def __init__(self):
        self.layers=[Layer() for _ in range(9)]
        self.collisionRects: list[CollisionRect]=[]
        self.currentLayer=0
        self.currentTiles: List[Tile]=[]
        self.currentTool: Tools = Tools.Draw
        self.selectionPalette=()
        self.selectionViewPort=()
        self.selectedCollisionRect: CollisionRect | None=None

    def ChangeSelectedCollisionRect(self,viewport):
        self.selectedCollisionRect=None
        for rect in self.collisionRects:
            if rect.collidePoint(pygame.mouse.get_pos(),viewport.panningOffset,viewport.zoom):
                self.selectedCollisionRect=rect


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
        self.relativeStart = viewport.toGrid(self.selectionViewPort[0])
        self.relativeEnd = viewport.toGrid(self.selectionViewPort[1])
        # Déterminer les bornes de la sélection
        x_min = min(self.relativeStart[0], self.relativeEnd[0])
        y_min = min(self.relativeStart[1], self.relativeEnd[1])
        x_max = max(self.relativeStart[0], self.relativeEnd[0])
        y_max = max(self.relativeStart[1], self.relativeEnd[1])

        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                self.getCurrentLayer().removeTile((x,y))

    def FillCurrentTilesSelection(self, viewport):
        self.relativeStart = viewport.toGrid(self.selectionViewPort[0])
        self.relativeEnd = viewport.toGrid(self.selectionViewPort[1])
        # Déterminer les bornes de la sélection
        x_min = min(self.relativeStart[0], self.relativeEnd[0])
        y_min = min(self.relativeStart[1], self.relativeEnd[1])
        x_max = max(self.relativeStart[0], self.relativeEnd[0])
        y_max = max(self.relativeStart[1], self.relativeEnd[1])

        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                NewTile = copy.deepcopy(self.currentTiles[0])
                NewTile.x = x
                NewTile.y = y
                self.getCurrentLayer().addOrReplaceTile(NewTile)

    def RandomCurrentTilesSelection(self, viewport):
        self.relativeStart = viewport.toGrid(self.selectionViewPort[0])
        self.relativeEnd = viewport.toGrid(self.selectionViewPort[1])
        # Déterminer les bornes de la sélection
        x_min = min(self.relativeStart[0], self.relativeEnd[0])
        y_min = min(self.relativeStart[1], self.relativeEnd[1])
        x_max = max(self.relativeStart[0], self.relativeEnd[0])
        y_max = max(self.relativeStart[1], self.relativeEnd[1])

        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                NewTile = copy.deepcopy(random.choice(self.currentTiles))
                NewTile.x = x
                NewTile.y = y
                self.getCurrentLayer().addOrReplaceTile(NewTile)


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
        for tile in self.currentTiles:
            self.getCurrentLayer().addOrReplaceTile(tile)

    def getCurrentLayer(self) -> Layer:
        return self.layers[self.currentLayer]
    
    def AddTile(self,tile: Tile):
        self.getCurrentLayer().addOrReplaceTile(tile)

    def RemoveTile(self,x,y):
        self.getCurrentLayer().removeTile(x,y)

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

        self.collisionRects.append(new_collision_rect)
        self.selectedCollisionRect=self.collisionRects[-1]


    def changeCurrentLayer(self,change: int):
        self.currentLayer = (self.currentLayer + change) % 9

