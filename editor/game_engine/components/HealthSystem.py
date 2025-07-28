
import pygame
from editor.game_engine import config
from editor.game_engine.core.utils import Colors, log
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from editor.game_engine.entities.players import Player

class HealthManager:
    def __init__(self, entity: 'Player', config):
        self.entity = entity
        self.max_health = config["base_params"]["health"]
        self.health = self.max_health
        if config["base_params"].get("heal_amount"):
            self.heal_cooldown = config["base_params"]["heal_cooldown"]
            self.heal_threshold = config["base_params"]["heal_threshold"]
            self.heal_amount = config["base_params"]["heal_amount"]
        self.last_heal_time = 0

        full_heart = pygame.image.load("./editor/game_engine/Assets/images/heart_full.png").convert_alpha()
        half_heart = pygame.image.load("./editor/game_engine/Assets/images/heart_half.png").convert_alpha()
        empty_heart = pygame.image.load("./editor/game_engine/Assets/images/heart_empty.png").convert_alpha()
        heart_scale=0.09

        # Redimensionne les images de cœur
        self.heart_images = {
            'full': pygame.transform.scale(full_heart, (full_heart.get_width()*heart_scale, full_heart.get_height()*heart_scale)),
            'half': pygame.transform.scale(half_heart, (half_heart.get_width()*heart_scale, half_heart.get_height()*heart_scale)),
            'empty': pygame.transform.scale(empty_heart, (empty_heart.get_width()*heart_scale, empty_heart.get_height()*heart_scale)),
        }

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.entity.animation.setAnimation("hurt")
        log("Health", self.entity, f"Took damage, current health: {self.health}", Colors.CYAN, config.DEBUG_HEALTH)
        return self.health <= 0

    def update(self):
        if self.entity.animation.current_animation=="hurt" and self.entity.animation.animation_count>0:
            self.entity.animation.setAnimation("idle")
        if self.entity.animation.current_animation=="heal" and self.entity.animation.animation_count>0 and \
                not self.health < self.heal_threshold * self.max_health:
            self.entity.animation.setAnimation("idle")


    def can_heal(self):
        return (
            self.health < self.heal_threshold * self.max_health and 
            pygame.time.get_ticks() - self.last_heal_time > self.heal_cooldown and
            not self.entity.animation.current_animation == "move"
        )
    
    def heal_with_amount(self,heal_amount):
        self.health = min(self.health + heal_amount, self.max_health)
        if self.entity.animation.getAnimation("heal"):
            self.entity.animation.setAnimation("heal")

    def heal(self):
        self.health = min(self.health + self.heal_amount, self.max_health)
        self.last_heal_time = pygame.time.get_ticks()
        self.entity.animation.setAnimation("heal")
        log("Health", self.entity, f"Is healing, current health: {self.health}", Colors.CYAN, config.DEBUG_HEALTH)

    
    def draw(self, surface):
        health_per_heart = 50
        max_hearts = int(self.max_health / health_per_heart)
        current_health = self.health
        full_heart = self.heart_images['full']
        half_heart = self.heart_images['half']
        empty_heart = self.heart_images['empty']
        heart_width = full_heart.get_width()-5
        
        for i in range(max_hearts):
            heart_x = surface.get_width()-200 + i * heart_width
            if current_health >= health_per_heart:
                image = full_heart
                current_health -= health_per_heart
            elif current_health >= health_per_heart / 2:
                image = half_heart
                current_health = 0
            else:
                image = empty_heart
            surface.blit(image, (heart_x, 10))

    def draw_health_bar(self, surface,display_name=False,bar_width=150,bar_height=6,offset_y=20):
        
        health_percent = self.health / self.max_health
        bar_x = self.entity.rect.x + (self.entity.rect.width - bar_width) / 2 -self.entity.camera.camera_rect.x
        bar_y = self.entity.rect.y - offset_y - bar_height - self.entity.camera.camera_rect.y
        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0, 200, 0), (bar_x, bar_y, bar_width * health_percent, bar_height))
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), 1)
        if display_name:
            entity_name = self.entity.__class__.__name__
            font = pygame.font.Font(None, 25)
            text_surface = font.render(entity_name, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.centerx = bar_x + bar_width / 2
            text_rect.bottom = bar_y - 2
            surface.blit(text_surface, text_rect)
