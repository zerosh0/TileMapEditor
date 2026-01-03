import pygame
import random

class ParticleEmitter:
    def __init__(self, x, y, name="vfx_0"):
        self.name = name
        self.x, self.y = x, y
        self.color = [255, 255, 255]
        
        self.rate = 10
        self.lifetime = 2.0
        self.speed = 100
        self.spread = 45
        self.gravity = 9.8
        self.size = 4
        self.active = True

    def get_screen_pos(self, panning_offset, zoom):
        cx = int(panning_offset[0] + self.x * zoom)
        cy = int(panning_offset[1] + self.y * zoom)
        return cx, cy

    def draw_icon(self, screen, panning_offset, zoom, is_selected):
        cx, cy = self.get_screen_pos(panning_offset, zoom)
        color = (255, 200, 0) if is_selected else (200, 200, 200)
        pygame.draw.polygon(screen, color, [
            (cx, cy - 8), (cx + 8, cy), (cx, cy + 8), (cx - 8, cy)
        ], 0 if is_selected else 2)

    def collidePoint(self, mouse_pos, panning_offset, zoom):
        cx, cy = self.get_screen_pos(panning_offset, zoom)
        return pygame.Rect(cx-10, cy-10, 20, 20).collidepoint(mouse_pos)