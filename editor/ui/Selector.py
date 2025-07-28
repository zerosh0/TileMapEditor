import pygame
import sys
import os

from editor.ui.Font import FontManager

class TextSelector:
    def __init__(self, rect, options,
                 arrow_left, arrow_right,
                 font=None,
                 text_color=(200,200,200),
                 bg_color=(41,41,41),
                 border_color=(62,62,62),
                 border_radius=3,
                 on_change=None,
                 default_index=0):
        """
        rect            : tuple ou pygame.Rect définissant la zone totale (flèches + texte)
        options         : liste de chaînes à faire défiler
        arrow_left      : chemin vers l'image flèche gauche ou pygame.Surface
        arrow_right     : chemin vers l'image flèche droite ou pygame.Surface
        font            : pygame.font.Font (par défaut taille 18)
        text_color      : couleur du texte
        bg_color        : couleur de fond
        border_color    : couleur de la bordure
        border_radius   : rayon des angles arrondis
        on_change       : callback(option_str) appelé à chaque changement
        default_index   : index initialement sélectionné
        """
        self.rect = pygame.Rect(rect)
        self.options = options
        self.index = default_index if 0 <= default_index < len(options) else 0
        self.on_change = on_change

        self.font_manager = FontManager()
        self.font = font or self.font_manager.get(size=18)
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_radius = border_radius

        # Charger / recevoir les surfaces d'arrow
        self.arrow_left = self._load_and_scale_arrow(arrow_left)
        self.arrow_right = self._load_and_scale_arrow(arrow_right)

        # définir les zones cliquables
        aw, ah = self.arrow_left.get_size()
        self.arrow_rect_left = pygame.Rect(self.rect.x + 2,
                                           self.rect.y + (self.rect.h - ah)//2,
                                           aw, ah)
        self.arrow_rect_right = pygame.Rect(self.rect.right - aw - 2,
                                            self.rect.y + (self.rect.h - ah)//2,
                                            aw, ah)

        self.arrow_left_surf  = self._load_and_scale_arrow(arrow_left)
        self.arrow_right_surf = self._load_and_scale_arrow(arrow_right)
        self.arrow_size = self.arrow_left_surf.get_size()

    def _load_and_scale_arrow(self, src):
        """ Charge l'image si besoin et la redimensionne pour rentrer dans la hauteur du widget. """
        # obtenir une surface
        if isinstance(src, str):
            if not os.path.isfile(src):
                raise FileNotFoundError(f"Image non trouvée : {src}")
            surf = pygame.image.load(src).convert_alpha()
        elif isinstance(src, pygame.Surface):
            surf = src.convert_alpha()
        else:
            raise ValueError("arrow_left/right doit être un chemin ou pygame.Surface")
        # scale : hauteur = hauteur du widget - 4 px, garder le ratio
        target_h = self.rect.h - 4
        w, h = surf.get_size()
        scale = target_h / h
        new_size = (int(w*scale), target_h)
        return pygame.transform.smoothscale(surf, new_size)

    @property
    def selected(self):
        return self.options[self.index]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.arrow_rect_left.collidepoint(event.pos):
                self.index = (self.index - 1) % len(self.options)
                if self.on_change: self.on_change(self.index)
            elif self.arrow_rect_right.collidepoint(event.pos):
                self.index = (self.index + 1) % len(self.options)
                if self.on_change: self.on_change(self.index)

    def draw(self, surf):
        # Fond + bordure
        pygame.draw.rect(surf, self.bg_color,  self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surf, self.border_color, self.rect, width=1, border_radius=self.border_radius)

        # Recalcul des rects centrés verticalement
        aw, ah = self.arrow_size
        ax_left  = self.rect.x - self.rect.width/4
        ay       = self.rect.y + (self.rect.h - ah) // 2
        ax_right = self.rect.right - aw + self.rect.width/4
        self.arrow_rect_left  = pygame.Rect(ax_left,  ay, aw, ah)
        self.arrow_rect_right = pygame.Rect(ax_right, ay, aw, ah)

        # Blit des flèches
        surf.blit(self.arrow_left_surf,  self.arrow_rect_left.topleft)
        surf.blit(self.arrow_right_surf, self.arrow_rect_right.topleft)

        # Texte centré
        text_surf = self.font.render(self.selected, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surf.blit(text_surf, text_rect)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((500, 120))
    clock = pygame.time.Clock()



    options = ["Page 1", "Page 2", "Page 3", "Page 4"]
    def on_change(value):
        print("Sélection :", value)


    selector = TextSelector(
        rect=(100, 40, 300, 40),
        options=options,
        arrow_left="./Assets/ui/icones/arrow_left.png",
        arrow_right="./Assets/ui/icones/arrow_right.png",
        default_index=0,
        on_change=on_change
    )

    # Appel initial
    on_change(selector.selected)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            selector.handle_event(event)

        screen.fill((30,30,30))
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()
