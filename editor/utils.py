
from dataclasses import dataclass, field
from enum import Enum
from typing import List

import pygame

class Colors():
    RED = "\033[91m"
    GREEN = "\033[92m" 
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

class Tools(Enum):
    Draw = 1
    Rubber = 2
    Fill = 3
    Random = 4
    Selection = 5
    LocationPoint = 6
    
class ActionType(Enum):
    AddTile = 1
    RemoveTile = 2
    AddCollision = 3
    RemoveCollision = 4

    

class Axis(Enum):
    Horizontal=0
    Vertical=1


@dataclass
class Tile:
    TileMap: str
    x: int
    y: int
    Originalx: int
    Originaly: int
    rotation: int = 0
    flipHorizontal: bool = False
    flipVertical: bool = False

    def rotate(self, angle: int):
        if self.TileMap:
            self.rotation = (self.rotation + angle) % 360

    def flip(self, axis: Axis):
        if self.TileMap:
            if axis == Axis.Horizontal:
                self.flipHorizontal = not self.flipHorizontal
            elif axis == Axis.Vertical:
                self.flipVertical = not self.flipVertical



@dataclass
class Layer:
    opacity: float = 1.0
    tiles: List[Tile] = field(default_factory=list)
        
    def addOrReplaceTile(self, tile):
        idx = next((i for i, t in enumerate(self.tiles) if t.x == tile.x and t.y == tile.y), None)
        
        if idx is not None:
            if self.tiles[idx] == tile:
                return ""
            replaced_tile = self.tiles[idx]
            self.tiles[idx] = tile
            return replaced_tile
        else:
            self.tiles.append(tile)
            return None



    def removeTile(self, pos):
        idx = next((i for i, t in enumerate(self.tiles) if t.x == pos[0] and t.y == pos[1]), None)
        if idx is not None:
            self.tiles.pop(idx)


@dataclass
class TileMap:
    name: str
    filepath: str
    tileSize: int
    image: pygame.surface.Surface
    colorKey: tuple | None
    zoomedImage: pygame.surface.Surface
    zoom: int = 1.0
    panningOffset: List[int] = field(default_factory=lambda: [0, 0])

    def GetTileImage(self,x,y):
        """Get tile image from relative position"""
        tile_col = int(x // self.tileSize)
        tile_row = int(y // self.tileSize)
        tile_rect = pygame.Rect(tile_col * self.tileSize, tile_row * self.tileSize, self.tileSize, self.tileSize)
        return self.image.subsurface(tile_rect).copy()
    



@dataclass
class CollisionRect:
    type: str
    name: str
    rect: pygame.Rect
    color: tuple = (148, 148, 148)

    def get_screen_rect(self, map_offset, zoom):
        """
        Convertit les coordonnées relatives du rectangle en coordonnées écran
        en appliquant le décalage (panning) et le zoom.
        """
        return pygame.Rect(
            int(map_offset[0] + self.rect.x * zoom),
            int(map_offset[1] + self.rect.y * zoom +30),
            int(self.rect.width * zoom),
            int(self.rect.height * zoom)
        )

    def collidePoint(self, point, map_offset, zoom):
        screen_rect = self.get_screen_rect(map_offset, zoom)
        return screen_rect.collidepoint(point)

    def draw(self, surface, map_offset, zoom, selected=False):
        screen_rect = self.get_screen_rect(map_offset, zoom)
        transparent_surface = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        fill_color = (*self.color, 100)
        transparent_surface.fill(fill_color)
        surface.blit(transparent_surface, (screen_rect.x, screen_rect.y))
        
        if selected:
            self.drawDottedBorder(surface, screen_rect, self.color, dot_radius=2, gap=4)

    def drawDottedBorder(self, surface, rect, color, dot_radius=2, gap=4):
        """
        Dessine des bords pointillés autour d'un rectangle.
        - dot_radius : rayon de chaque point
        - gap : espacement entre deux points
        """
        x = rect.left
        while x <= rect.right:
            pygame.draw.circle(surface, color, (x, rect.top), dot_radius)
            x += gap
        x = rect.left
        while x <= rect.right:
            pygame.draw.circle(surface, color, (x, rect.bottom), dot_radius)
            x += gap
        y = rect.top
        while y <= rect.bottom:
            pygame.draw.circle(surface, color, (rect.left, y), dot_radius)
            y += gap
        y = rect.top
        while y <= rect.bottom:
            pygame.draw.circle(surface, color, (rect.right, y), dot_radius)
            y += gap




@dataclass
class LocationPoint:
    type: str
    name: str
    image: pygame.Surface
    SelectedImage: pygame.Surface
    rect: pygame.Rect
    color: tuple = (148, 148, 148)

    def get_screen_rect(self, map_offset, zoom):
        """
        Convertit les coordonnées relatives en coordonnées écran,
        en appliquant le décalage (panning) et le zoom.
        """
        base_rect = pygame.Rect(
            int(map_offset[0] + self.rect.x * zoom),
            int(map_offset[1] + self.rect.y * zoom + 30),
            int(self.rect.width * zoom),
            int(self.rect.height * zoom)
        )

        scaled_width = int(self.image.get_width() * zoom)
        scaled_height = int(self.image.get_height() * zoom)
        return pygame.Rect(
            base_rect.centerx - scaled_width,
            base_rect.bottom - scaled_height * 2,
            scaled_width,
            scaled_height
        )


    def collidePoint(self, point, map_offset, zoom):
        screen_rect = self.get_screen_rect(map_offset, zoom)
        return screen_rect.collidepoint(point)

    def draw(self, surface, map_offset, zoom, selected=False):
        if selected:
            image = pygame.transform.scale(
                self.SelectedImage,
                (int(self.image.get_width() * zoom), int(self.image.get_height() * zoom))
            )
        else:
            image = pygame.transform.scale(
                self.image,
                (int(self.image.get_width() * zoom), int(self.image.get_height() * zoom))
            )


        image = image.copy()
        color_surface = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        color_surface.fill(self.color)
        image.blit(color_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        image.set_alpha(150)
        screen_rect = self.get_screen_rect(map_offset, zoom)
        surface.blit(image, screen_rect)


    
            
