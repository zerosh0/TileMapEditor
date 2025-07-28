from enum import Enum
from typing import Optional, Tuple
import pygame
from dataclasses import dataclass

from editor.blueprint_editor.system import BlueprintEditor


class AIState(Enum):
    IDLE = 1
    PATROL = 2
    CHASE = 3
    ATTACK = 4
    FLEE = 5


@dataclass
class TileMap:
    name: str
    image: pygame.Surface
    tile_size: int

    def get_tile(self, original_x, original_y, standard_tile_size):
        x, y = original_x * self.tile_size, original_y * self.tile_size
        tile_image = self.image.subsurface(pygame.Rect(x, y, self.tile_size, self.tile_size))


        if self.tile_size != standard_tile_size:
            tile_image = pygame.transform.scale(tile_image, (standard_tile_size, standard_tile_size))

        return tile_image


@dataclass
class CollisionRect:
    type: str
    name: str
    rect: pygame.Rect
    color: tuple
    graph: BlueprintEditor | None = None
    collide: bool = False
    text: Optional[str] = None
    font_size: int = 14
    text_color: Tuple[int, int, int] = (255, 255, 255)
    bubble_speed: float = 0.0
    bubble_duration: float = -1.0
    padding: int = 4
    bubble_start_time: int = 0

    
@dataclass
class LocationPoint:
    type: str
    name: str
    x: int
    y: int
    color: tuple

def predefined_colors():
    return [
        (150, 255, 255),  # Cyan doux
        (200, 200, 255),  # Bleu clair
        (255, 230, 230),  # Rose pâle
        (180, 180, 255),   # Bleu très pâle
        (150, 100, 255),  # Violet léger
        (255, 182, 193),  # Rose léger
    ]

class Colors(Enum):
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

def cprint(text, color: Colors = Colors.WHITE):
    print(f"{color.value}{text}{Colors.RESET.value}")

def log(label: str, obj, message: str, color: Colors = Colors.CYAN, debug_flag: bool = True):
    if not debug_flag:
        return
    class_name = obj.__class__.__name__
    cprint(f"[{label}] {class_name} {message}", color)
