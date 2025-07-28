
from dataclasses import dataclass, field
from enum import Enum
import math
import random
import time
from typing import List, Optional, Tuple, Union
import uuid
import webbrowser

import pygame

from editor.blueprint_editor.system import BlueprintEditor

class Colors():
    RED = "\033[91m"
    GREEN = "\033[92m" 
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

class Tools(Enum):
    Draw = "draw"
    Rubber = "rubber"
    Fill = "fill"
    Random = "random"
    Selection = "selection"
    LocationPoint = "location_point"
    Light = "light"
    
class ActionType(Enum):
    AddTile = 1
    RemoveTile = 2
    AddCollision = 3
    RemoveCollision = 4
    AddKeyframe = 5
    RemoveKeyframe = 6
    AddLight = 7
    RemoveLight = 8
    

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
class AnimatedTile:
    anim_id: Union[str, int]
    time: float
    tile: Tile
    layer: int 

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
    
    def get_tile(self, original_x, original_y, standard_tile_size):
        x, y = original_x * self.tileSize, original_y * self.tileSize
        try:
            tile_image = self.image.subsurface(pygame.Rect(x, y, self.tileSize, self.tileSize))
        except:
            print(f"Erreur de tuile  original pos {original_x,original_y,self.name}")

        if self.tileSize != standard_tile_size:
            try:
                tile_image = pygame.transform.scale(tile_image, (standard_tile_size, standard_tile_size))
            except:
                print(f"Bad tile, original pos: ({original_x},{original_y},{self.name})")
                return None
        return tile_image


@dataclass
class CollisionRect:
    type: str
    name: str
    rect: pygame.Rect
    color: tuple = (148, 148, 148)
    graph: BlueprintEditor | None = None
    collide: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: Optional[str] = None
    font_size: int = 14
    text_color: Tuple[int,int,int] = (255,255,255)
    bubble_speed: float = 0.0
    bubble_duration: float = -1.0
    padding: int = 4
    bubble_start_time: int = 0

    def clone(self) -> "CollisionRect":
        return CollisionRect(
            type=self.type,
            name=self.name,
            rect=self.rect.copy(),
            color=self.color,
            graph=self.graph,
            collide=self.collide,
            id=self.id,
            text=self.text,
            font_size=self.font_size,
            text_color=self.text_color,
            padding=self.padding
        )

    
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
class Light:
    x: float
    y: float
    radius: int
    color: tuple = (255, 180, 80)
    blink: bool = False
    radius_var: int = 3
    start_time = time.time() + random.random()*10
    visible: bool = True

    def get_screen_pos(self, map_offset, zoom):
        return (
            int(map_offset[0] + self.x * zoom),
            int(map_offset[1] + self.y * zoom + 30)
        )

    def collidePoint(self, point: tuple[int,int], map_offset, zoom) -> bool:
        cx, cy = self.get_screen_pos(map_offset, zoom)
        dx = point[0] - cx
        dy = point[1] - cy
        return dx*dx + dy*dy <= (self.radius * zoom)**2

    def draw(self, surface, light_mask, base_alpha, map_offset, zoom, selected):
        cx = int(map_offset[0] + self.x * zoom)
        cy = int(map_offset[1] + self.y * zoom)
        radius_px = int(self.radius * zoom)

        if self.blink:
            now = time.time()
            phase = (now - self.start_time) * 2
            flick_r = radius_px + math.sin(phase) * self.radius_var + (random.random() - 0.5) * 5
            for r in range(int(flick_r), 0, -1):
                f = 1 - (r / flick_r)
                col = (
                    int(self.color[0] * f),
                    int(self.color[1] * f),
                    int(self.color[2] * f),
                )
                a = int((1 - f) * base_alpha)
                pygame.draw.circle(light_mask, (*col, a), (cx, cy), r)

        else:
            for r in range(radius_px, 0, -1):
                f = 1 - (r / radius_px)
                col = (
                    int(self.color[0] * f),
                    int(self.color[1] * f),
                    int(self.color[2] * f)
                ) 
                local_a = int(base_alpha * (1 - f))
                pygame.draw.circle(light_mask, (*col, local_a), (cx, cy), r)

        if selected:
            pygame.draw.circle(surface, (43, 255, 255), (cx, cy+30), radius_px, width=2)
        elif base_alpha<70:
                pygame.draw.circle(surface, self.color, (cx, cy+30), radius_px,width=2)

        



@dataclass
class LocationPoint:
    type: str
    name: str
    rect: pygame.Rect
    color: tuple = (148, 148, 148)

    def get_screen_rect(self, map_offset, zoom,image):
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

        scaled_width = int(image.get_width() * zoom)
        scaled_height = int(image.get_height() * zoom)
        return pygame.Rect(
            base_rect.centerx - scaled_width,
            base_rect.bottom - scaled_height * 2,
            scaled_width,
            scaled_height
        )


    def collidePoint(self, point, map_offset, zoom,image):
        screen_rect = self.get_screen_rect(map_offset, zoom,image)
        return screen_rect.collidepoint(point)

    def draw(self, surface, map_offset, zoom, Oimage):
        image = pygame.transform.scale(
            Oimage,
            (int(Oimage.get_width() * zoom), int(Oimage.get_height() * zoom))
        )

        image = image.copy()
        color_surface = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        color_surface.fill(self.color)
        image.blit(color_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        image.set_alpha(150)
        screen_rect = self.get_screen_rect(map_offset, zoom,Oimage)
        surface.blit(image, screen_rect)


    
        
def open_github():
    webbrowser.open_new_tab("https://github.com/zerosh0/TileMapEditor/")