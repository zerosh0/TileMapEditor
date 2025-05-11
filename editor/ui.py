import pygame
from pygame import gfxdraw
import tkinter as tk
from tkinter import colorchooser,filedialog
class Button:
    def __init__(self, rect, text, action, font=None,
                 bg_color=(100, 100, 100), text_color=(255, 255, 255),
                 hover_color=None,size=36):
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
        self.text = text
        self.action = action
        self.font = font if font else pygame.font.Font(None, size)
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
        pygame.draw.rect(surface, color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class ImageButton:
    def __init__(self, rect, image_path, action, hover_image_path=None):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la zone du bouton.
        :param image_path: Chemin vers l'image affichée par défaut sur le bouton.
        :param action: Fonction à appeler lors d'un clic sur le bouton.
        :param hover_image_path: Chemin vers l'image affichée lorsque le bouton est survolé.
                                 Si None, une version assombrie de l'image sera générée automatiquement.
        """
        self.rect = pygame.Rect(rect)
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

    def _load_image(self, path):
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.scale(image, (self.rect.width, self.rect.height))
        return image

    def _create_hover_image(self, image):
        hover_img = image.copy()
        hover_img.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_SUB)
        return hover_img

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.action()

    def draw(self, surface):
        if self.is_hovered:
            surface.blit(self.hover_image, self.rect)
        else:
            surface.blit(self.image, self.rect)

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

    def draw(self, surface):
        """ Dessine le slider sur la surface donnée avec un curseur bien centré. """
        # Dessiner la barre de fond
        pygame.draw.rect(surface, self.bar_color, self.rect, border_radius=int(self.handle_radius))

        # Dessiner la barre de progression
        progress_rect = pygame.Rect(self.rect.x, self.rect.y, 
                                    self._value_to_pos(self.value) - self.rect.x, self.rect.height)
        pygame.draw.rect(surface, self.progress_color, progress_rect, border_radius=int(self.handle_radius))

        # Position du curseur
        handle_pos = (int(self._value_to_pos(self.value)), self.rect.centery)
        #gfxdraw pour l'anti aliasing
        pygame.gfxdraw.aacircle(surface, handle_pos[0], handle_pos[1], int(self.handle_radius)+2, self.handle_color)
        pygame.gfxdraw.filled_circle(surface, handle_pos[0], handle_pos[1], int(self.handle_radius)+2, self.handle_color)


class ColorButton:
    def __init__(self, rect, initial_color, action=None):
        """
        :param rect: Tuple (x, y, largeur, hauteur) définissant la zone du bouton.
        :param initial_color: Couleur initiale du bouton (tuple RGB).
        :param action: Fonction à appeler lors d'un clic
        """
        self.rect = pygame.Rect(rect)
        self.color = initial_color
        self.action = action  # Action facultative au clic
        self.is_hovered = False

    def handle_event(self, event):
        """ Gère les événements de la souris. """
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered and event.button == 1:
            self.pick_color()
            if self.action:
                self.action(self.color)

    def pick_color(self):
        """ Ouvre une palette de couleurs et met à jour la couleur du bouton. """
        root = tk.Tk()
        root.withdraw() 
        color = colorchooser.askcolor(title="Choisir une couleur")
        if color and color[0]:
            self.color = tuple(int(c) for c in color[0])

    def draw(self, surface):
        """ Dessine le bouton sur la surface donnée. """
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)

        # Ajoute un contour en surbrillance si la souris est dessus
        if self.is_hovered:
            pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=5)
