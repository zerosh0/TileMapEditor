import pygame
from editor.game_engine.components.Raycast import Raycast
from editor.game_engine import config
from editor.game_engine.core.level import Level
from editor.game_engine.core.utils import AIState, Colors,log


from editor.game_engine.entities.players import Player


class AIBehavior:
    def __init__(self, entity: Player, player: Player, level : Level,screen):
        self.entity = entity
        self.player = player
        self.level = level
        self.screen=screen
        self.current_state = AIState.IDLE
        self.locationThreshold = 60
        self.obstacle_check_distance = 50
        self.LastHitBox=[]
        self.last_collided_rect=None
        self.OverPassThreshold=abs(self.entity.physics.jump_strength)*9
        self.blocked_timer = 0
        self.max_blocked_time = 300
        self.last_distance = float('inf')
        self.distanceToPlayer= float('inf')
        self.stuck_counter = 0
        self.max_stuck_count = 3
        self.detection_range=None
        

    def FacePlayer(self):
        direction=self.entity.rect.centerx-self.player.rect.centerx
        if direction>0:
            self.entity.ChangeDirection("left")
        else:
            self.entity.ChangeDirection("right")


    def MoveToLocation(self, target_pos):
        target_vec = pygame.math.Vector2(target_pos)
        current_pos = pygame.math.Vector2(self.entity.rect.center)
        direction = target_vec - current_pos
        distance = direction.length()
        
        if distance > self.locationThreshold:
            direction.normalize_ip()
            
            if self.is_stuck(distance):
                self.handle_blocked_state()
                return
            
            self.handle_movement(direction)
            self.last_distance = distance
        else:
            if self.entity.animation.current_animation=="move" and self.entity.animation.current_frame==0:
                self.entity.animation.setAnimation("idle")
            self.reset_blocked_state()

    def is_stuck(self, current_distance):
        distance_diff = abs(self.last_distance - current_distance)
        time_diff = pygame.time.get_ticks() - self.blocked_timer
        
        if distance_diff < 1.0 and not self.has_direct_line_of_sight():
            if time_diff > self.max_blocked_time:
                self.stuck_counter += 1
                return self.stuck_counter >= self.max_stuck_count
        elif self.has_direct_line_of_sight():
            self.reset_blocked_state()
        
        return False

    def handle_blocked_state(self):
        log("IA", self.entity, "Bloqué, arrêt du chase", Colors.CYAN, config.DEBUG_AI)
        self.entity.movement.velocity_x = 0
        self.entity.animation.setAnimation("idle")

    def reset_blocked_state(self):
        self.blocked_timer = pygame.time.get_ticks()
        self.stuck_counter = 0
        self.last_distance = float('inf')

    def has_reached_player(self):
        return self.distanceToPlayer<=self.locationThreshold+20

    def handle_movement(self, direction):
        front_rect, hitbox= self.entity.collisions.FrontCollide(
            self.level.get_scaled_rects(),
            self.entity.direction,
            self.obstacle_check_distance
        )
        self.LastHitBox.append(hitbox)
        if direction.x < -0.1:
                self.entity.move_left()
        elif direction.x > 0.1:
                self.entity.move_right()
        if front_rect:
            self.last_collided_rect=front_rect
            
            if front_rect and abs(self.entity.rect.bottom - front_rect.top) < self.OverPassThreshold:
                self.entity.physics.performJump()
                log("IA", self.entity, "Saut obstacle", Colors.CYAN, config.DEBUG_AI)


    def projectile_collide(self,attack):
        attack=attack["hitbox"]
        height,y,range=attack["height"],attack["y"],attack["range"]
        result, hitbox=self.entity.collisions.ProjectileCollide(self.entity.direction,height,y,range,self.player.rect)
        if attack["debug"]:
            self.LastHitBox.append(hitbox)
        return result

    def has_direct_line_of_sight(self):
        to_player = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.entity.rect.center)
        self.distanceToPlayer = to_player.length()
        
        if self.distanceToPlayer == 0:
            return True  # Déjà sur le joueur
        
        direction = to_player.normalize()
        
        vision_ray = Raycast(
            start=self.entity.rect.center,
            direction=direction,
            max_distance=self.distanceToPlayer,
            debug=config.DEBUG_AI
        )
        collision, _, _ = vision_ray.cast(self.level.get_scaled_rects())
        return collision is None


    def DrawDebug(self,surface):
        if config.DEBUG_AI:
            if self.last_collided_rect:
                self.LastHitBox.append(self.last_collided_rect)
            for hitbox in self.LastHitBox:
                screen_front_hitbox = pygame.Rect(
                    hitbox.x - self.entity.camera.camera_rect.x,
                    hitbox.y - self.entity.camera.camera_rect.y,
                    hitbox.width,
                    hitbox.height
                )
                
                debug_surface = pygame.Surface(screen_front_hitbox.size, pygame.SRCALPHA)
                debug_surface.fill((233, 193, 255, 50))
                surface.blit(debug_surface, screen_front_hitbox)
                pygame.draw.rect(surface,(233, 193, 255), screen_front_hitbox, 1)
            self.LastHitBox=[]
            self.DrawDebugVision()

    def DrawDebugVision(self):
        screen_start = (
                self.entity.rect.centerx - self.entity.camera.camera_rect.x,
                self.entity.rect.centery - self.entity.camera.camera_rect.y
            )
        screen_end = (
                self.player.rect.centerx - self.entity.camera.camera_rect.x,
                self.player.rect.centery - self.entity.camera.camera_rect.y
            )
        
        if config.DEBUG_AI:
                pygame.draw.line(self.screen, (159, 114, 255), screen_start, screen_end, 2)

    def update(self):
        self.FacePlayer()
        match self.current_state:
            case AIState.CHASE:
                self.chasePlayer()
            case AIState.IDLE:
                self.entity.animation.setAnimation("idle")
    
    def chasePlayer(self):
        target_pos = (self.player.rect.centerx, self.player.rect.centery)
        self.MoveToLocation(target_pos)