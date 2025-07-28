
import pygame


class Slider:
    def __init__(self, rect, min_value=0, max_value=100, initial_value=None, 
                 bar_color=(100, 100, 100), progress_color=(0, 150, 255), 
                 handle_color=(255, 255, 255), border_color=(0, 0, 0)):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la barre du slider.
        :param min_value: Valeur minimale du slider.
        :param max_value: Valeur maximale du slider.
        :param initial_value: Valeur initiale du slider (par défaut au milieu).
        :param bar_color: Couleur de fond de la barre.
        :param progress_color: Couleur de la progression.
        :param handle_color: Couleur du curseur.
        :param border_color: Couleur du contour du curseur.
        """
        self.rect = pygame.Rect(rect)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value if initial_value is not None else (min_value + max_value) / 2
        self.on_change=None
        self.bar_color = bar_color
        self.progress_color = progress_color
        self.handle_color = handle_color
        self.border_color = border_color  # Contour du curseur

        self.handle_radius = self.rect.height // 2.5  # Curseur plus petit
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._handle_rect().collidepoint(event.pos):
                self.dragging = True
                
            elif self.rect.collidepoint(event.pos):
                self._update_value(event.pos[0])
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])

    def _handle_rect(self):
        """ Retourne un rectangle représentant le curseur du slider. """
        x = self._value_to_pos(self.value)
        return pygame.Rect(x - self.handle_radius, self.rect.centery - self.handle_radius, 
                           self.handle_radius * 2.5, self.handle_radius * 2.5)

    def _value_to_pos(self, value):
        """ Convertit une valeur en position X sur la barre. """
        return self.rect.x + (value - self.min_value) / (self.max_value - self.min_value) * (self.rect.width - self.handle_radius * 2) + self.handle_radius

    def _pos_to_value(self, x):
        """ Convertit une position X sur la barre en valeur du slider. """
        relative_x = max(self.rect.x + self.handle_radius, min(x, self.rect.right - self.handle_radius))
        return self.min_value + (relative_x - (self.rect.x + self.handle_radius)) / (self.rect.width - self.handle_radius * 2) * (self.max_value - self.min_value)

    def _update_value(self, x):
        """ Met à jour la valeur du slider en fonction de la position X de la souris. """
        self.value = self._pos_to_value(x)
        if self.on_change:
            self.on_change(self.value)

    def draw(self, surface):
        """ Dessine le slider sur la surface donnée avec un curseur bien centré. """
        # Dessiner la barre de fond
        pygame.draw.rect(surface, self.bar_color, self.rect, border_radius=int(self.handle_radius))

        # Dessiner la barre de progression
        progress_rect = pygame.Rect(self.rect.x, self.rect.y, 
                                    self._value_to_pos(self.value) - self.rect.x, self.rect.height)
        pygame.draw.rect(surface, self.progress_color, progress_rect, border_radius=int(self.handle_radius))

        # Position du curseur
        handle_x = int(self._value_to_pos(self.value))
        handle_y = self.rect.centery
        handle_pos = (handle_x, handle_y)
        try:
            pygame.draw.aacircle(surface, self.handle_color, handle_pos, int(self.handle_radius + 1))
        except:
            pygame.draw.circle(surface, self.handle_color, handle_pos, int(self.handle_radius+2))


