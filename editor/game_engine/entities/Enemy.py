import json
import pygame
from editor.game_engine.components.AI import AIBehavior
from editor.game_engine.components.Animations import AnimationManager
from editor.game_engine.components.AttackSystem import Attack
from editor.game_engine.components.Collisions import CollisionManager
from editor.game_engine.components.EntityMovement import EntityMovement
from editor.game_engine.components.HealthSystem import HealthManager
from editor.game_engine.components.Physics import PhysicsObject
from editor.game_engine import config

class Enemy:
    def __init__(self, position, config_path, initial_spritesheet, colorkey, clock, camera, level,player,screen,enemies_list):
        super().__init__()
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.direction = "right"
        self.clock = clock
        self.camera = camera
        self.level = level
        self.animation = AnimationManager(initial_spritesheet, colorkey, "idle", clock)
        
        

        self.load_config(config_path,position)
        self.physics = PhysicsObject(self, clock,jump_strength=-12)
        self.collisions = CollisionManager(level, self)
        self.movement = EntityMovement(self, clock)
        self.AI = AIBehavior(self,player,level,screen)
        self.AI.detection_range = self.config["base_params"]["detection_range"]
        self.AI.locationThreshold=self.config["base_params"]["attack_range"]
        self.attack=Attack(self,[player],self.config,["move","hurt","heal"])
        self.health_system=HealthManager(self,self.config)
        self.enemies_list=enemies_list

    def destroy(self):
        self.enemies_list.remove(self)

    def load_config(self, path,position):
        try:
            with open(path, "r") as f:
                self.config = json.load(f)
                
                self.speed = self.config["base_params"]["speed"]
                self.health_system = self.config["base_params"]["health"]

                self.rect.width = self.config["collision"]["width"]
                self.rect.height = self.config["collision"]["height"]
                self.rect.centerx=position[0]
                self.rect.bottom=position[1]
                self.animation.addAutoAnimationsFromFile(
                    path, 
                    scale=self.config["base_params"].get("scale", 1.0)
                )
                
        except Exception as e:
            raise Exception(f"Error loading enemy config {path}: {e}")

    def move_right(self):
        self.animation.setAnimation("move")
        self.movement.move_right()
        self.ChangeDirection("right")

    def move_left(self):
        self.animation.setAnimation("move")
        self.movement.move_left()
        self.ChangeDirection("left")


    def update(self):
        self.animation.updateAnimation()
        self.collisions.Process()
        self.physics.update()
        self.movement.update()
        self.health_system.update()

    def draw(self, surface):
        self.health_system.draw_health_bar(surface)
        image = self.animation.getCurrentFrame()
        offset_x, offset_y = self.animation.getCurrentAnimation().frameOffset[self.animation.current_frame]
        display_rect = image.get_rect()
        display_rect.bottom = self.rect.bottom - offset_y
        display_rect.centerx = self.rect.centerx - offset_x
        surface.blit(self.image, self.camera.apply_rect(display_rect))
        if config.DEBUG_COLLISIONS:
            debug_rect = self.rect.copy()
            debug_rect.x -= self.camera.camera_rect.x
            debug_rect.y -= self.camera.camera_rect.y
            pygame.draw.rect(surface, (255, 0, 0), debug_rect, 1)
        if config.DEBUG_DISPLAY:
            original_debug_rect = self.rect.copy()
            original_debug_rect.x -= self.camera.camera_rect.x
            original_debug_rect.y -= self.camera.camera_rect.y
            pygame.draw.rect(surface, (0, 255, 0), display_rect, 1)
        self.AI.DrawDebug(surface)
        self.attack.debug_draw(surface)

    
    def ChangeDirection(self, new_direction):
        if new_direction == "left" and self.direction == "right":
            self.animation.flipFrames()
            self.direction = new_direction
        if new_direction == "right" and self.direction == "left":
            self.animation.flipFrames()
            self.direction = new_direction

    @property
    def image(self):
        return self.animation.getCurrentFrame()



    