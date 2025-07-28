import pygame


class ImageButton:
    def __init__(self, rect, image_path, action, hover_image_path=None, tint_color=None):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la zone du bouton.
        :param image_path: Chemin vers l'image affichée par défaut sur le bouton.
        :param action: Fonction à appeler lors d'un clic sur le bouton.
        :param hover_image_path: Chemin vers l'image affichée lorsque le bouton est survolé.
                                 Si None, une version assombrie de l'image sera générée automatiquement.
        """
        self.rect = pygame.Rect(rect)
        self.tint_color = tint_color
        self.init_image(image_path,hover_image_path)
        self.action = action
        self.is_hovered = False

    def init_image(self,image_path,hover_image_path=None):
        self.image = self._load_image(image_path)
        self.image_path=image_path
        
        if hover_image_path is None:
            self.hover_image = self._create_hover_image(self.image)
        else:
            self.hover_image = self._load_image(hover_image_path)

        if self.tint_color is not None:
            self.tinted_image = self._create_tinted_image(self.image, self.tint_color)
            self.tinted_hover_image = self._create_tinted_image(self.hover_image, self.tint_color)
        else:
            self.tinted_image = None
            self.tinted_hover_image = None

    def _load_image(self, path):
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.scale(image, (self.rect.width, self.rect.height))
        return image

    def _create_hover_image(self, image):
        hover_img = image.copy()
        hover_img.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_SUB)
        return hover_img

    def _create_tinted_image(self, image, tint_color):
        tinted = image.copy()
        tinted.fill((*tint_color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.action()

    def draw(self, surface,is_tinted=False):
        if self.is_hovered:
            if is_tinted:
                surface.blit(self.tinted_hover_image, self.rect)
            else:
                surface.blit(self.hover_image, self.rect)
        else:
            if is_tinted:
                surface.blit(self.tinted_image, self.rect)
            else:
                surface.blit(self.image, self.rect)