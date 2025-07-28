import json
import random
import pygame
from editor.game_engine.components.AttackSystem import Attack
from editor.game_engine.components.HealthSystem import HealthManager
from editor.game_engine import config
from editor.game_engine.components.audio import AudioManager
from editor.game_engine.core.Input import InputHandler
from editor.game_engine.core.level import Level
from editor.game_engine.components.EntityMovement import EntityMovement
from editor.game_engine.components.Animations import AnimationManager
from editor.game_engine.components.Collisions import CollisionManager
from editor.game_engine.components.Physics import PhysicsObject

class Player():
    def __init__(self, sprite_sheet,colorkey,animations,level: Level,camera,clock,enemies,nm):
        self.direction = "right"
        self.nm=nm
        self.level=level
        self.level.draw_player=lambda s : self.draw(s)
        self.animation=AnimationManager(sprite_sheet,colorkey,"idle",clock,self)
        self.rect = pygame.Rect(0,0,1,1)
        self.load_config(animations)
        self.image = self.animation.getCurrentFrame()
        self.spawn_name=None
        self.rect.centerx,self.rect.bottom=level.get_location_by_name("spawn")
        self.camera=camera
        self.physics = PhysicsObject(self,clock, gravity=0.6, jump_strength=-10)
        self.collisions=CollisionManager(self.level,self)
        self.input_handler = InputHandler(self)
        self.movement=EntityMovement(self,clock)
        self.fly_speed=12
        self.attack=Attack(self,enemies,self.config)
        self.health_system=HealthManager(self,self.config)
        self.audio_manager = AudioManager(self)
        self.enemies=enemies
        self.already_attacked=False
        self.clock=clock
        self.fly_mode = False
        self.last_action_time = pygame.time.get_ticks()
        self.sleep_started = False
        self.sleep_anims = ["sleeping1", "sleeping2", "sleeping3"]
        self.next_sleep_time = None
        self.sleep_reps = 0
        self.max_sleeping1_reps = 3
        self.idle_threshold = 6000
        self.post_start_interval = 5000
        self.sleep_interval_min = 10000
        self.sleep_interval_max = 15000
        try:
            self.sleep_sound = pygame.mixer.Sound(
                "./editor/game_engine/Assets/sounds_effects/sleeping.mp3"
            )
        except Exception as e:
            print(f"Erreur chargement sleep sound : {e}")
            self.sleep_sound = None

    def reset_pos(self):
        if self.spawn_name:
            self.rect.centerx,self.rect.bottom=self.level.get_location_by_name(self.spawn_name)
            self.physics.__init__(self,self.clock, gravity=self.physics.gravity, jump_strength=self.physics.jump_strength)

    def update_location_by_name(self,name):
        self.spawn_name=name
        self.rect.centerx,self.rect.bottom=self.level.get_location_by_name(name)

    def load_config(self, path):
        try:
            with open(path, "r") as f:
                self.config = json.load(f)
                self.speed = self.config["base_params"]["speed"]
                self.health = self.config["base_params"]["health"]
                self.rect.width = self.config["collision"]["width"]
                self.rect.height = self.config["collision"]["height"]
                
        except Exception as e:
            raise Exception(f"Error loading player config {path}: {e}")
        self.animation.addAnimationsFromFile(path)

    def take_damage(self,amount):
        self.animation.start_flash_effect(
            color=(255, 0, 0),
            duration=150,
            alpha=250,
        )
        self.health_system.take_damage(amount)

    def dash(self):
        self.movement.dash()

    def move_right(self):
        self.ChangeDirection("right")
        if self.fly_mode:
            self.animation.setAnimation("fly_move")
            self.rect.x += int(self.fly_speed)
        else:
            self.animation.setAnimation("run")
            self.movement.move_right()
            

    def move_left(self):
        self.ChangeDirection("left")
        if self.fly_mode:
            self.animation.setAnimation("fly_move")
            self.rect.x -= int(self.fly_speed)
        else:
            self.animation.setAnimation("run")
            self.movement.move_left()
            

    def fly_down(self):
        if self.fly_mode:
            self.rect.y += int(self.fly_speed)


    def jump(self, animation_name):
        if self.fly_mode:
            self.rect.y -= int(self.fly_speed)
        else:
            self.physics.jump(animation_name)

    def sword_slash(self):
        self.attack.start_attack("sword")
    

    def reset_idle(self):
        self.last_action_time = pygame.time.get_ticks()
        if self.sleep_started:
            self.sleep_started = False
            self.next_sleep_time = None
            self.animation.setAnimation("idle")
            if self.sleep_sound:
                self.sleep_sound.stop()

    def Input(self):
        self.reset_idle()

    def noInput(self):
        if self.fly_mode:
            self.animation.setAnimation("fly_idle")
        elif not self.sleep_started:
            self.animation.setAnimation("idle")

    def sleeping_update(self):
        now = pygame.time.get_ticks()
        idle_time = now - self.last_action_time
        if not self.animation.current_animation in ["idle","start_sleep"]+self.sleep_anims:
            self.reset_idle()
        if not self.sleep_started and idle_time >= self.idle_threshold:
            self.sleep_started = True
            self.animation.forceSetAnimation("start_sleep")
            if self.sleep_sound:
                self.sleep_sound.play(loops=-1, fade_ms=300)
            start_anim = self.animation.getAnimation("start_sleep")
            dur = len(start_anim.frames) * start_anim.frameRate
            self.next_sleep_time = now + dur + self.post_start_interval
            self.sleep_reps = 0
            return

        if self.sleep_started:
            current = self.animation.current_animation
            anim = self.animation.getCurrentAnimation()
            last_frame = len(anim.frames) - 1

            if current == "start_sleep":
                if self.animation.current_frame < last_frame:
                    return
                self.animation.current_frame = last_frame
                self.animation.accumulated_time = 0

                if now >= self.next_sleep_time:
                    choix = random.choice(self.sleep_anims)
                    self.animation.forceSetAnimation(choix)
                    self.sleep_reps = 1 if choix == "sleeping1" else 0
                    self.next_sleep_time = None
                return

            if current in self.sleep_anims:
                if self.animation.current_frame < last_frame:
                    return

                if current == "sleeping1" and self.sleep_reps < self.max_sleeping1_reps:
                    self.animation.forceSetAnimation("sleeping1")
                    self.sleep_reps += 1
                    return

                self.animation.current_frame = last_frame
                self.animation.accumulated_time = 0
                if self.next_sleep_time is None:
                    delay = random.randint(self.sleep_interval_min, self.sleep_interval_max)
                    self.next_sleep_time = now + delay

                if now >= self.next_sleep_time:
                    choices = [a for a in self.sleep_anims if a != current]
                    choix = random.choice(choices)
                    self.animation.forceSetAnimation(choix)
                    self.sleep_reps = 1 if choix == "sleeping1" else 0
                    self.next_sleep_time = None
                return





    def toggle_fly(self):
        self.fly_mode = not self.fly_mode
        if self.fly_mode:
            self.physics.clear_forces()


    def update(self):
        self.input_handler.update()
        self.sleeping_update()
        self.animation.updateAnimation()
        self.collisions.update()
        self.physics.update()
        self.movement.update()
        self.attack.check_attack_hit()
        self.audio_manager.update_all()
        self.collisions.Process()
            

    def draw(self, surface):
        self.image = self.animation.getCurrentFrame()
        offset_x, offset_y = self.animation.getCurrentAnimation().frameOffset[self.animation.current_frame]
        display_rect = self.image.get_rect()
        display_rect.bottom = self.rect.bottom - offset_y
        display_rect.centerx = self.rect.centerx - offset_x
        surface.blit(self.image, self.camera.apply_rect(display_rect))
        self.health_system.draw(surface)
        if config.DEBUG_DISPLAY:
            original_debug_rect = self.rect.copy()
            original_debug_rect.x -= self.camera.camera_rect.x
            original_debug_rect.y -= self.camera.camera_rect.y
            pygame.draw.rect(surface, (0, 255, 0), display_rect, 1)
        if config.DEBUG_COLLISIONS:
            debug_rect = self.rect.copy()
            debug_rect.x -= self.camera.camera_rect.x
            debug_rect.y -= self.camera.camera_rect.y
            pygame.draw.rect(surface, (255, 0, 0), debug_rect, 1)
        self.attack.debug_draw(surface)

    def ChangeDirection(self, new_direction):
        if new_direction == "left" and self.direction == "right":
            self.animation.flipFrames()
            self.direction = new_direction
        if new_direction == "right" and self.direction == "left":
            self.animation.flipFrames()
            self.direction = new_direction
