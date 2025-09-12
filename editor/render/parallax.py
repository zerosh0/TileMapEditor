import pygame

class ParallaxBackground:
    def __init__(self, surface: pygame.Surface, viewport_data, layers: list[tuple[str, float]],
                 bg_color=(200, 200, 200)):
        """
        :param surface: surface du viewport pour dessiner
        :param viewport_data: objet ViewPort avec panningOffset
        :param layers: liste de (chemin_image, parallax_factor)
        :param bg_color: couleur unie derrière les couches
        """
        self.surface = surface
        self.viewport_data = viewport_data
        self.bg_color = bg_color
        self.layers = []
        self.buffers = {}

        for path, parallax in layers:
            orig = pygame.image.load(path).convert_alpha()
            self.layers.append({
                "orig": orig,
                "parallax": parallax,
                "scaled": None,
                "last_height": 0,
                "is_static": parallax == 0
            })

    def render(self):
        vw, vh = self.surface.get_size()
        pan_x, _ = self.viewport_data.parallaxOffset

        self.surface.fill(self.bg_color)

        for idx, layer in enumerate(self.layers):
            # scale si nécessaire
            if layer["scaled"] is None or layer["last_height"] != vh:
                ow, oh = layer["orig"].get_size()
                scale = vh / oh
                nw = int(ow * scale)
                layer["scaled"] = pygame.transform.scale(layer["orig"], (nw, vh)).convert_alpha()
                layer["last_height"] = vh

                # créer buffer pour layer statique si besoin
                if layer["is_static"]:
                    self.buffers[idx] = layer["scaled"].copy()

            img = layer["scaled"]
            w, _ = img.get_size()
            par = layer["parallax"]

            offset_x = int(-pan_x * par) % w

            if layer["is_static"]:
                buffer_img = self.buffers[idx]
                self.surface.blit(buffer_img, (-offset_x, 0))
                self.surface.blit(buffer_img, (-offset_x + w, 0))
            else:
                self.surface.blit(img, (-offset_x, 0))
                self.surface.blit(img, (-offset_x + w, 0))
