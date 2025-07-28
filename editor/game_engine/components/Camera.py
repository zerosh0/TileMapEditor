import pygame
import random
from editor.game_engine import config

class Camera:
    def __init__(self, width, height, smooth_speed=0.1):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.smooth_speed = smooth_speed

        # Variables pour le screen shake
        self.shake_duration = 0       # Combien de frames ça va trembler
        self.shake_intensity = 0      # Intensité du tremblement (pixels max)
        self.shake_offset = pygame.Vector2(0, 0)  # Décalage temporaire de la caméra


    def shake(self, duration, intensity):
        """Lance un screen shake pour une certaine durée et intensité."""
        self.shake_duration = duration
        self.shake_intensity = intensity


    def update(self, target_rect, screen, clock):
        if config.AUTO_UPDATE_CAMERA:
            self.camera_rect.width = screen.get_width()
            self.camera_rect.height = screen.get_height()

        dt = clock.get_time() / 17
        target_x = target_rect.centerx - self.camera_rect.width // 2
        target_y = target_rect.centery - self.camera_rect.height // 2

        dx = target_x - self.camera_rect.x
        dy = target_y - self.camera_rect.y

        threshold = 2

        if abs(dx) < threshold:
            self.camera_rect.x = target_x
        else:
            self.camera_rect.x += int(dx * self.smooth_speed * dt)

        if abs(dy) < threshold:
            self.camera_rect.y = target_y
        else:
            self.camera_rect.y += int(dy * self.smooth_speed * dt)

        # Screen shake
        if self.shake_duration > 0:
            self.shake_offset.x = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_offset.y = random.randint(-self.shake_intensity, self.shake_intensity)
            self.shake_duration -= 1
        else:
            self.shake_offset.xy = (0, 0)

    def apply_rect(self, rect):
        dx = -self.camera_rect.x + int(self.shake_offset.x)
        dy = -self.camera_rect.y + int(self.shake_offset.y)
        return rect.move(dx, dy)

    def apply_point(self, x, y):
        dx = -self.camera_rect.x + int(self.shake_offset.x)
        dy = -self.camera_rect.y + int(self.shake_offset.y)
        return x + dx, y + dy

