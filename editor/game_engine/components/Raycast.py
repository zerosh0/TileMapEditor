import pygame

class Raycast:
    def __init__(self, start, direction, max_distance, debug=False):
        """
        :param start: Tuple (x, y) du point d'origine.
        :param direction: Vecteur direction (x, y). Il sera normalisé.
        :param max_distance: Distance maximale du rayon.
        :param debug: Si True, active l'affichage du rayon.
        """
        self.start = pygame.math.Vector2(start)
        # Normalisation de la direction pour éviter des erreurs de distance
        self.direction = pygame.math.Vector2(direction)
        if self.direction.length() != 0:
            self.direction = self.direction.normalize()
        else:
            raise ValueError("La direction ne peut pas être le vecteur nul.")
        self.max_distance = max_distance
        self.debug = debug
        self.collision_point = None
        self.collided_rect = None

    def cast(self, rects):
        """
        Lance le rayon et vérifie les collisions avec un ou plusieurs rect.
        
        :param rects: Peut être un pygame.Rect, une liste de pygame.Rect,
                      ou un pygame.sprite.Group (les sprites doivent avoir un attribut 'rect').
        :return: Tuple (point_collision, rect_collidé, distance)
                 Si aucune collision n'est détectée, retourne (None, None, max_distance).
        """
        # Transformation en liste pour simplifier le traitement
        if isinstance(rects, pygame.Rect):
            rect_list = [rects]
        elif isinstance(rects, pygame.sprite.Group):
            rect_list = [sprite.rect for sprite in rects]
        else:
            rect_list = rects

        # Calcul du point final théorique du rayon
        end = self.start + self.direction * self.max_distance

        nearest_collision = None
        nearest_rect = None
        min_distance = self.max_distance

        for rect in rect_list:
            # Vérification de l'overlap : si le point de départ est à l'intérieur du rect
            if rect.collidepoint(self.start):
                nearest_collision = self.start
                nearest_rect = rect
                min_distance = 0
                break  # Collision immédiate détectée
            # Utilisation de clipline pour récupérer l'intersection éventuelle
            result = rect.clipline(self.start, end)
            if result:
                # result contient (x1, y1, x2, y2) : le segment du rayon à l'intérieur du rect
                # On considère le premier point d'intersection comme le point de collision
                collision_pt = pygame.math.Vector2(result[0], result[1])
                dist = collision_pt.distance_to(self.start)
                if dist < min_distance:
                    min_distance = dist
                    nearest_collision = collision_pt
                    nearest_rect = rect

        self.collision_point = nearest_collision
        self.collided_rect = nearest_rect

        return nearest_collision, nearest_rect, min_distance

    def debug_draw(self, surface, color=(255, 0, 0)):
        """
        Trace la ligne du rayon sur la surface passée.
        Si une collision a été détectée, trace le rayon jusqu'au point de collision,
        sinon trace le rayon complet.
        
        :param surface: Surface Pygame sur laquelle dessiner.
        :param color: Couleur de la ligne du rayon.
        """
        if self.debug:
            # Point final théorique
            end_point = self.start + self.direction * self.max_distance
            # Si collision, raccourcir le rayon
            if self.collision_point:
                end_point = self.collision_point
            pygame.draw.line(surface, color, self.start, end_point, 5)
