from editor.game_engine.core.level import Level
from editor.game_engine.entities.Enemy import Enemy


class Frogger(Enemy):
    def __init__(self, clock, camera, level : Level,player,screen,enemies_list):
        super().__init__(
            position=level.get_location_by_name("Frogger"),
            config_path="./editor/game_engine/Assets/ennemisData/frogger.json",
            initial_spritesheet="./editor/game_engine/Assets/images/Frogger/frogger_idle.png",
            colorkey=(0, 0, 0),
            clock=clock,
            camera=camera,
            level=level,
            player=player,
            screen=screen,
            enemies_list=enemies_list,
        )
        self.physics.jump_strength=-7

    def update(self):
        super().update()
        self.AI.chasePlayer()
        self.AI.FacePlayer()
        self.health_logic()
        self.attack_logic()
        

        
    def attack_logic(self):
        if self.AI.has_reached_player():
            if self.attack.can_attack("tongue"):
                self.attack.start_attack("tongue")
            elif self.attack.can_attack("spit"):
                self.attack.start_attack("spit")
        self.attack.check_attack_hit()

    def health_logic(self):
        if self.health_system.can_heal():
            self.health_system.heal()
        if self.health_system.health<=0:
            self.destroy()

    def take_damage(self,amount):
        self.health_system.take_damage(amount)