

import pygame


class Checkbox:
    def __init__(self, rect, checked_image_path, unchecked_image_path, initial_state=False, action=None):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la zone du checkbox.
        :param checked_image_path: Chemin vers l'image affichée lorsque coché.
        :param unchecked_image_path: Chemin vers l'image affichée lorsque décoché.
        :param initial_state: État initial (bool).
        :param action: Fonction à appeler lors du changement d'état; appelée avec le nouvel état en argument.
        """
        self.rect = pygame.Rect(rect)
        self.checked_image = self._load_image(checked_image_path)
        self.unchecked_image = self._load_image(unchecked_image_path)
        self.state = initial_state
        self.action = action

    def _load_image(self, path):
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, (self.rect.width, self.rect.height))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                if self.action:
                    self.action(self.state)

    def draw(self, surface):
        if self.state:
            surface.blit(self.checked_image, self.rect)
        else:
            surface.blit(self.unchecked_image, self.rect)

