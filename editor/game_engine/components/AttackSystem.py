import itertools
from typing import List, Dict, Any
from typing import TYPE_CHECKING

import pygame
from editor.game_engine.core.utils import predefined_colors
if TYPE_CHECKING:
    from editor.game_engine.entities.players import Player

class Attack:
    def __init__(self, entity: List['Player'], enemies: List['Player'], config: Dict[str, Any],no_attack_animations: List[str]=[]):
        self.entity: 'Player' = entity
        self.enemies: List['Player'] = enemies
        self.attacks: Dict[str, Any] = config["attacks"]
        self.current_attack: Dict[str, Any] = None
        self.already_attacked: bool = False
        self.attack_hitbox: List[Any] = []
        self.no_attack_animations=no_attack_animations

    def check_attack_hit(self):
        if self.current_attack and self.entity.animation.current_frame == self.current_attack["hit_frame"]:
            if not self.already_attacked and self.entity.animation.current_animation==self.current_attack["animation"]:
                self.apply_attack_effect()
                self.already_attacked = True
        elif self.entity.animation.current_frame == 0:
            self.already_attacked = False

    def apply_attack_effect(self) -> None:
        hitbox=self.current_attack["hitbox"]
        height = hitbox["height"]
        y = hitbox["y"]
        range_ = hitbox["range"]

        for enemy in self.enemies:
            result, hitbox_rect = self.entity.collisions.ProjectileCollide(
                self.entity.direction, height, y, range_, enemy.rect
            )
            if hitbox.get("debug") and not hitbox_rect in self.attack_hitbox:
                self.attack_hitbox.append(hitbox_rect)
            if result:
                enemy.take_damage(self.current_attack["damage"])

    def can_attack(self, attack_name: str) -> bool:
        attack = self.attacks.get(attack_name)
        if not attack or self.entity.animation.current_animation in self.no_attack_animations:
            return False
        hitbox=attack["hitbox"]
        height = hitbox["height"]
        y = hitbox["y"]
        range_ = hitbox["range"]

        for enemy in self.enemies:
            result, hitbox_rect = self.entity.collisions.ProjectileCollide(
                self.entity.direction, height, y, range_, enemy.rect
            )
            if hitbox.get("debug") and not hitbox_rect in self.attack_hitbox:
                self.attack_hitbox.append(hitbox_rect)
            if result:
                return True
        return False

    def start_attack(self, attack_name: str) -> None:
        self.current_attack = self.attacks.get(attack_name)
        if self.current_attack:
            self.entity.animation.setAnimation(self.current_attack["animation"])

    def debug_draw(self,surface):
        color_iterator = itertools.cycle(predefined_colors())
        for hitbox in self.attack_hitbox:
            hitbox_color = next(color_iterator)
            screen_front_hitbox = pygame.Rect(
                hitbox.x - self.entity.camera.camera_rect.x,
                hitbox.y - self.entity.camera.camera_rect.y,
                hitbox.width,
                hitbox.height
            )
            
            debug_surface = pygame.Surface(screen_front_hitbox.size, pygame.SRCALPHA)
            debug_surface.fill((*hitbox_color, 50))
            surface.blit(debug_surface, screen_front_hitbox)
            pygame.draw.rect(surface,hitbox_color, screen_front_hitbox, 1)
        if self.current_attack and self.entity.animation.current_frame==0:
            self.attack_hitbox=[]