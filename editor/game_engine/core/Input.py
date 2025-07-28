
import pygame


class InputHandler:
    def __init__(self, player):
        self.player = player
        self.pressed_keys = set()  # Stocke les touches pressées
        self.noCommandes=player.noInput
        self.input=player.Input
        self.disable=False
        # Commandes classiques
        self.commandes = {
            pygame.K_RIGHT: self.player.move_right,
            pygame.K_d: self.player.move_right,
            pygame.K_LEFT: self.player.move_left,
            pygame.K_q: self.player.move_left,
            pygame.K_SPACE: lambda: self.player.jump("flip_jump"),
            pygame.K_UP: lambda: self.player.jump("flip_jump"),
            pygame.K_DOWN: self.player.fly_down,
            pygame.K_s: self.player.fly_down,
            pygame.K_z: lambda: self.player.jump("slash_jump"),
            pygame.K_a: self.player.sword_slash,
            pygame.K_b: self.player.dash
        }

        # Commandes avancées (combinaisons)
        self.combos = {
            # (pygame.K_DOWN, pygame.K_a): self.player.special_attack
        }

    def handleInput(self, event):
        if event.type == pygame.KEYDOWN:
            self.pressed_keys.add(event.key)
        elif event.type == pygame.KEYUP:
            self.pressed_keys.discard(event.key)

    def update(self):
        if self.disable:
            self.noCommandes()
            self.input()
            return
        # Vérifie d'abord les combos (prioritaires)
        for keys_combo, action in self.combos.items():
            if all(k in self.pressed_keys for k in keys_combo):
                action()
                self.input()
                return

        keys = pygame.key.get_pressed()
        pressed=False
        for key, action in self.commandes.items():
            if keys[key]:
                pressed=True
                action()
                self.input()
        if not pressed:
            self.noCommandes()