
import pygame

from editor.ui.Font import FontManager


class Button:
    def __init__(self, rect, text, action, font=None,
                 bg_color=(100, 100, 100), text_color=(255, 255, 255),
                 hover_color=None,size=36,border_radius=-1):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la zone du bouton.
        :param text: Texte affiché sur le bouton.
        :param action: Fonction à appeler lors d'un clic sur le bouton.
        :param font: Objet pygame.font.Font pour le rendu du texte (utilise la police par défaut si None).
        :param bg_color: Couleur de fond du bouton.
        :param text_color: Couleur du texte.
        :param hover_color: Couleur de fond lorsque le bouton est survolé. Si None, une teinte plus claire de bg_color est utilisée.
        """
        self.rect = pygame.Rect(rect)
        self.border_radius=border_radius
        self.text = text
        self.action = action
        self.font_manager = FontManager()
        self.font = font if font else self.font_manager.get(size=size)
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color if hover_color else (
            min(bg_color[0] + 40, 255),
            min(bg_color[1] + 40, 255),
            min(bg_color[2] + 40, 255)
        )
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:  # clic gauche
                self.action()

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect,border_radius=self.border_radius)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
