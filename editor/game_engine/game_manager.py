
import pygame
import sys
from editor.core.settings import SettingsManager
from editor.game_engine.components.Camera import Camera
from editor.game_engine import config
from editor.game_engine.core.level import Level
from editor.game_engine.entities.ennemis.frogger import Frogger
from editor.game_engine.entities.players import Player



class Game:
    def __init__(self, screen,dataManager,TilePalette,clock,animation_manager,nm):
        self.running = False
        self.clock = clock
        self.level = Level.from_data_manager(dataManager,TilePalette,animation_manager=animation_manager)
        self.camera = Camera(screen.get_width(), screen.get_height(), smooth_speed=0.1)
        self.enemies = []
        self.player = Player(config.SPRITESHEET_PATH, config.SPRITESHEET_COLORKEY, config.ANIMATION_PATH, 
                             self.level, self.camera, self.clock,self.enemies,nm)
        self.screen = screen
        # frogger = Frogger(
        #     clock=self.clock,
        #     camera=self.camera,
        #     level=self.level,
        #     player=self.player,
        #     screen=self.screen,
        #     enemies_list=self.enemies
        # )
        
        # self.enemies.append(frogger)
        self._applied_settings = {
            'gravity':     self.player.physics.gravity,
            'jump_force':  self.player.physics.jump_strength,
            'max_speed':   self.player.movement.max_speed,
            'player_speed':self.player.speed,
            'global_illum': 1,
            'can_fly': False
        }

    def handle_events(self,event):
        if not self.running:
            return
        if event.type == pygame.QUIT:
            self.running = False
            self.quit_game()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.VIDEORESIZE:
            w, h = event.w, event.h
            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            self.camera.viewport_size = (w, h)
            self.light_mask = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        self.player.input_handler.handleInput(event)


    def update_settings(self,settings: SettingsManager):
        if settings.can_fly != self._applied_settings['can_fly']:
            self.player.fly_mode = settings.can_fly
            self._applied_settings['can_fly'] = settings.can_fly


        if settings.gravity != self._applied_settings['gravity']:
            self.player.physics.gravity = settings.gravity
            self._applied_settings['gravity'] = settings.gravity

        if settings.jump_force != self._applied_settings['jump_force']:
            self.player.physics.jump_strength = settings.jump_force
            self._applied_settings['jump_force'] = settings.jump_force

        new_max = settings.player_speed * 2
        if new_max != self._applied_settings['max_speed']:
            self.player.movement.max_speed = new_max
            self._applied_settings['max_speed'] = new_max

        if settings.player_speed != self._applied_settings['player_speed']:
            self.player.speed = settings.player_speed
            self._applied_settings['player_speed'] = settings.player_speed

        if settings.global_illum != self._applied_settings['global_illum']:
            self.level.shadow_alpha=settings.global_illum*255
            self._applied_settings['global_illum'] = settings.global_illum

    def update(self, settings : SettingsManager):
        if not self.running:
            return
        self.tick_execute()
        self.player.update()
        self.update_settings(settings)
        for ennemi in self.enemies:
            ennemi.update()
        self.camera.update(self.player.rect, self.screen,self.clock)

    def tick_execute(self):
        for collision_rect in self.level.collision_rects:
            if collision_rect.graph is not None:
                collision_rect.graph.process_delayed_tasks()
                tick=collision_rect.graph.events.get("on_tick")
                if tick:
                    collision_rect.graph.run_logic_from_event(tick)


    def draw(self,screen):
        if not self.running:
            return
        self.screen=screen
        self.level.draw(self.screen, self.camera,self.clock)
        for ennemi in self.enemies:
            ennemi.draw(self.screen)
        # self.player.draw(self.screen)
        self.level.draw_lights(self.camera,self.screen)
        pygame.display.flip()



    def run(self):
        while self.running:
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)
        self.quit_game()

    def quit_game(self):
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode(config.SCREEN_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption(config.WINDOW_NAME)
    Game(screen).run()
