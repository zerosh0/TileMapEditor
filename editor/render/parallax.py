import pygame


class ParallaxBackground:
    def __init__(self,surface: pygame.Surface,viewport_data,layers: list[tuple[str, float]],
                 bg_color: tuple[int, int, int] = (200, 200, 200)):
        """
        :param surface: la surface du viewport pour dessiner
        :param viewport_data: objet ViewPort avec panningOffset
        :param layers: liste de (chemin_image, parallax_factor)
        :param bg_color: couleur unie derrière les couches
        """
        self.surface = surface
        self.viewport_data = viewport_data
        self.bg_color = bg_color
        self.layers = []
        for path, parallax in layers:
            orig = pygame.image.load(path)
            self.layers.append({
                "orig": orig,
                "parallax": parallax,
                "scaled": None,
                "height": 0
            })

    def render(self):
        vw, vh = self.surface.get_size()
        pan_x, _ = self.viewport_data.parallaxOffset

        self.surface.fill(self.bg_color)

        for layer in self.layers:
            if layer["height"] != vh:
                orig = layer["orig"]
                ow, oh = orig.get_size()
                scale = vh / oh
                nw = int(ow * scale)
                layer["scaled"] = pygame.transform.scale(orig, (nw, vh))
                layer["height"] = vh

            img = layer["scaled"]
            w, _ = img.get_size()
            par = layer["parallax"]
            offset_x = int(-pan_x * par) % w

            x = -offset_x
            while x < vw:
                self.surface.blit(img, (x, 0))
                x += w
