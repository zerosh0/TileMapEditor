
import pygame

from editor.ui.ColorPicker import ColorPicker



class ColorButton:
    def __init__(self, rect, initial_color, action=None):
        self.rect = pygame.Rect(rect)
        self.color = initial_color
        self.action = action
        self.is_hovered = False

        self._saved_color = initial_color
        self.picker_visible = False
        self.picker = None

    def handle_event(self, event):
        # Si le picker est ouvert, on lui délègue tous les events
        if self.picker_visible and self.picker:
            self.picker.handle_event(event)
            # **LIVE UPDATE** au passage
            self.color = self.picker.current_color
            return

        # Sinon on gère l'hover et l'ouverture
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.open_picker()

    def open_picker(self):
        self._saved_color = self.color
        self.picker_visible = True

        # Positionner à droite du bouton (+10px)
        px = self.rect.right + 10
        py = self.rect.y
        picker_rect = (px, py, 220, 330)

        def confirm(new_color):
            self.picker_visible = False
            if self.action:
                self.action(self.color)

        def cancel():
            # revert à la couleur d'origine
            self.color = self._saved_color
            self.picker_visible = False

        self.picker = ColorPicker(
            picker_rect,
            initial_color=self.color,
            on_confirm=confirm,
            on_cancel=cancel
        )

    def draw(self, surface):
        if self.picker_visible and self.picker:
            self.color = self.picker.current_color

        # Dessin du bouton
        pygame.draw.rect(surface, self.color, self.rect, border_radius=3)
        if self.is_hovered:
            pygame.draw.rect(surface, (255,255,255),
                             self.rect, width=2, border_radius=3)

        # Puis dessin du picker par-dessus
        if self.picker_visible and self.picker:
            self.picker.draw(surface)

    def __init__(self, rect, initial_color, action=None):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la zone du bouton.
        :param initial_color: Couleur initiale du bouton (tuple RGB).
        :param action: Fonction à appeler lors d'un clic validé.
        """
        self.rect = pygame.Rect(rect)
        self.color = initial_color
        self.action = action
        self.is_hovered = False

        # Pour la preview / revert
        self._saved_color = initial_color
        self.picker_visible = False
        self.picker = None

    def handle_event(self, event):
        """Gère les événements souris et délègue au picker si visible."""
        if self.picker_visible and self.picker:
            self.picker.handle_event(event)
        else:
            if event.type == pygame.MOUSEMOTION:
                self.is_hovered = self.rect.collidepoint(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hovered:
                    self.open_picker()

    def open_picker(self):
        """Ouvre le ColorPicker à droite du bouton."""
        self._saved_color = self.color
        self.picker_visible = True

        px = self.rect.right - 200
        py = self.rect.y-165
        picker_rect = (px, py, 220, 330)

        def confirm(new_color):
            self.picker_visible = False

        def cancel():
            self.color = self._saved_color
            self.action(self.color)
            self.picker_visible = False

        self.picker = ColorPicker(
            picker_rect,
            initial_color=self.color,
            on_confirm=confirm,
            on_cancel=cancel
        )


    def draw(self, surface):
        """Dessine le bouton et le picker s'il est visible."""
        # Bouton
        if self.picker_visible and self.picker:
            self.color = self.picker.current_color
            self.action(self.color)
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        if self.is_hovered:
            pygame.draw.rect(surface, (255,255,255), self.rect, width=2, border_radius=5)

        # Picker
        if self.picker_visible and self.picker:
            self.picker.draw(surface)

