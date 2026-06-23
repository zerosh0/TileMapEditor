import pygame
import time
import os

class ReleaseNotesPopup:
    def __init__(self, screen_size, on_close, font_name=None):
        self.screen_w, self.screen_h = screen_size
        self.width  = int(self.screen_w * 0.70)
        self.height = int(self.screen_h * 0.75)
        self.rect = pygame.Rect(
            (self.screen_w - self.width) // 2,
            (self.screen_h - self.height) // 2,
            self.width, self.height
        )
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.bg_color        = (22, 22, 32, 245)  
        self.header_color    = (30, 30, 44)  
        self.border_color    = (45, 48, 68)        
        self.section_color   = (0, 175, 240)
        self.text_color      = (210, 215, 230)
        self.subtitle_color  = (130, 135, 150)
        self.divider_color   = (45, 48, 68)
        self.button_color    = (200, 71, 88)

        # Scrollbar
        self.scrollbar_track   = (32, 34, 48)
        self.scrollbar_thumb   = (58, 62, 85)
        self.scrollbar_width   = 6
        self.scrollbar_margin  = 12

        # Layout
        self.btn_radius        = 6
        self.padding           = 20
        self.header_h          = 42

        # Fonts
        self.title_font   = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.section_font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.text_font    = pygame.font.SysFont("Segoe UI", 13)

        self.version_number    = None
        self.title             = ""
        self.subtitle = (
            "Le système de particules (VFX) a été mis à jour et propose désormais :\n"
            "(Accessible sur la carte via l'outil VFX et après avoir posé un émetteur)"
        )

        self.sections = [
            ("Moteur de Particules VFX",
             "Vous pouvez placer et éditer des émetteurs de particules sur le niveau. Les particules supportent différents styles de rendu (Cercle, Étincelle, Bulle animée, Flocon de neige, Boule de feu, Étoile) pour animer vos cartes.",
             "portal"),

            ("Galerie des Presets",
             "Une galerie accessible dans le Playground VFX permet de choisir parmi plusieurs préconfigurations (Fire, Snow, Spark, Bubble, Portal, Fireball, Cosmic Starfield) avec une prévisualisation en temps réel.",
             "gallery"),

            ("Forces Physiques Modulaires",
             "Il est possible d'activer et de régler différents modules de forces physiques comme la Gravité, le Vent, le Vortex, le Chaos et la Friction de l'air.",
             "forces"),

            ("Collisions Physiques",
             "Les particules peuvent rebondir sur les blocs de collision de type 'collision' et sur le joueur, en générant des étincelles lors de l'impact.",
             "bubble"),

            ("Régulation de Performance",
             "Le système limite le nombre maximal de particules actives à 150 si le framerate descend sous les 20 FPS. Cette limite remonte automatiquement à 600 dans un délai de 2 secondes dès que la fluidité est rétablie.",
             "perf"),

            ("Éditeur Nodal Amélioré",
             "L'éditeur nodal a été redessiné avec une double grille d'alignement (fine et majeure), chaque catégorie de nœuds possède désormais sa propre couleur distinctive pour une meilleure lisibilité.",
             "nodes"),

            ("Contrôle Nodal des Particules",
             "De nouveaux nœuds de logique (Set Emitter Active, Set Emitter Rate, Trigger Emitter Burst) ont été ajoutés pour piloter dynamiquement vos émetteurs de particules VFX.",
             "particles_nodes")
        ]

        self._load_and_scale_images()

        self.already = False
        self._prepare_lines()

        self.content_height = self._calc_content_height()
        self.scroll_y       = 0
        self.max_scroll     = max(0, self.content_height - (self.height - self.header_h - 2*self.padding))

        self.cancel_center = (self.width - self.btn_radius - 16, self.header_h // 2)
        self.on_close      = on_close

        self.alpha         = 0
        self.fade_duration = 0.3
        self.start_time    = time.time()
        self.active        = True

        self.dragging_thumb   = False
        self.dragging_header  = False
        self.drag_start_y     = 0
        self.scroll_start     = 0
        self.header_offset    = (0, 0)
        self.v_file_exist=False

    def _load_and_scale_images(self):
        """Loads and pre-scales screenshots dynamically based on the current popup width."""
        self.images = {}
        max_w = self.width - 2 * self.padding - self.scrollbar_width - 8
        img_w = int(max_w * 0.90)

        for k, fname in [
            ("portal", "portal_effect.png"),
            ("gallery", "gallerie.png"),
            ("forces", "forces_gallerie.png"),
            ("bubble", "bubble_collision.png"),
            ("perf", "perf.png"),
            ("nodes", "nodes.png"),
            ("particles_nodes", "particles_nodes.png")
        ]:
            path = os.path.join("Assets", "images", "release", fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    h = int(img.get_height() * (img_w / img.get_width()))
                    scaled = pygame.transform.smoothscale(img, (img_w, h))
                    self.images[k] = scaled
                except Exception as e:
                    print(f"Error loading/scaling release image {fname}: {e}")

    def _prepare_lines(self):
        """Pre-render title/subtitle/sections/images into self.lines."""
        self.lines = []
        y = self.header_h + self.padding * 2 + 2
        max_w = self.width - 2 * self.padding - self.scrollbar_width - 8

        # Subtitle
        for line in self.subtitle.split('\n'):
            surf = self.text_font.render(line, True, self.subtitle_color)
            self.lines.append((y, "surface", surf))
            y += surf.get_height() + 6
        y += self.padding

        # Sections
        for title, body, img_key in self.sections:
            # Section Title
            ts = self.section_font.render(title, True, self.section_color)
            self.lines.append((y, "surface", ts))
            y += ts.get_height() + 6

            # Section Description wrapping
            words, buf = body.split(' '), ''
            for w in words:
                test = (buf + ' ' + w).strip()
                if self.text_font.size(test)[0] > max_w and buf:
                    surf = self.text_font.render(buf, True, self.text_color)
                    self.lines.append((y, "surface", surf))
                    y += surf.get_height() + 4
                    buf = w
                else:
                    buf = test
            if buf:
                surf = self.text_font.render(buf, True, self.text_color)
                self.lines.append((y, "surface", surf))
                y += surf.get_height() + 6

            # Optional Screenshot illustration
            if img_key and img_key in self.images:
                img_surf = self.images[img_key]
                y += 8
                self.lines.append((y, "image", img_surf))
                y += img_surf.get_height() + 12

            # Section Divider line
            div = pygame.Surface((max_w, 1))
            div.fill(self.divider_color)
            self.lines.append((y + self.padding // 2, "surface", div))
            y += div.get_height() + self.padding

    def _calc_content_height(self):
        if not self.lines:
            return 0
        last_y, last_type, last_item = self.lines[-1]
        return last_y + last_item.get_height()

    def handle_event(self, event):
        if not self.active: return

        # Compute scrollbar geometry
        tx = self.width - self.scrollbar_margin - self.scrollbar_width
        ty = self.header_h + self.padding
        ch = self.height - self.header_h - 2*self.padding
        if self.content_height > 0:
            th = max(int(ch * ch / self.content_height), 20)
            ty_thumb = ty + int(self.scroll_y * (ch - th) / max(1, self.max_scroll))
            thumb_rect = pygame.Rect(tx+1, ty_thumb, self.scrollbar_width-2, th)
            track_rect = pygame.Rect(tx, ty, self.scrollbar_width, ch)
        else:
            thumb_rect = track_rect = pygame.Rect(0,0,0,0)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            rx, ry = mx - self.rect.x, my - self.rect.y

            # Close button click
            if (rx - self.cancel_center[0])**2 + (ry - self.cancel_center[1])**2 <= (self.btn_radius + 4)**2:
                self.on_close(self.v_file_exist)
                self.active = False
                return

            # Thumb drag
            if thumb_rect.collidepoint(rx, ry):
                self.dragging_thumb = True
                self.drag_start_y   = ry
                self.scroll_start   = self.scroll_y
                return

            # Track click for page scroll
            if track_rect.collidepoint(rx, ry):
                if ry < thumb_rect.top:
                    self.scroll_y = max(self.scroll_y - (ch - th), 0)
                elif ry > thumb_rect.bottom:
                    self.scroll_y = min(self.scroll_y + (ch - th), self.max_scroll)
                return

            # Header drag
            header_rect = pygame.Rect(0, 0, self.width, self.header_h)
            if header_rect.collidepoint(rx, ry):
                self.dragging_header = True
                self.header_offset   = (mx - self.rect.x, my - self.rect.y)
                return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_thumb  = False
            self.dragging_header = False

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.dragging_thumb:
                dy = my - (self.rect.y + self.drag_start_y)
                track_h = ch - th
                dy = max(0, min(dy, track_h))
                self.scroll_y = int(dy * self.max_scroll / max(1, track_h))
            elif self.dragging_header:
                ox, oy = self.header_offset
                self.rect.x = mx - ox
                self.rect.y = my - oy

        # Mouse wheel scrolling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_y = max(self.scroll_y - 24, 0)
            elif event.button == 5:
                self.scroll_y = min(self.scroll_y + 24, self.max_scroll)

    def update(self):
        t = min((time.time() - self.start_time) / self.fade_duration, 1)
        self.alpha = int(255 * t)

    def draw(self, screen):
        if not self.active: return

        # Base Surface
        self.surface.fill(self.bg_color)
        pygame.draw.rect(self.surface, self.border_color,
                         self.surface.get_rect(), 2, border_radius=8)

        # Header bar
        pygame.draw.rect(self.surface, self.header_color,
                         (0, 0, self.width, self.header_h),
                         border_top_left_radius=6,
                         border_top_right_radius=6)
        pygame.draw.line(self.surface, self.border_color, (0, self.header_h), (self.width, self.header_h), 1)

        title_surf = self.title_font.render(self.title, True, self.text_color)
        self.surface.blit(title_surf,
                          (self.padding, (self.header_h - title_surf.get_height())//2))

        # Close button hover detection
        mx, my = pygame.mouse.get_pos()
        rx, ry = mx - self.rect.x, my - self.rect.y
        close_hovered = (rx - self.cancel_center[0])**2 + (ry - self.cancel_center[1])**2 <= (self.btn_radius + 4)**2

        # Draw close button circle (sober red, no cross inside)
        btn_col = (220, 90, 105) if close_hovered else self.button_color
        pygame.draw.circle(self.surface, btn_col, self.cancel_center, self.btn_radius)

        # Content clipping
        clip = pygame.Rect(
            self.padding,
            self.header_h + self.padding,
            self.width - 2*self.padding - self.scrollbar_width - 8,
            self.height - self.header_h - 2*self.padding
        )
        self.surface.set_clip(clip)
        for y, l_type, item in self.lines:
            draw_y = y - self.scroll_y
            if draw_y + item.get_height() > self.header_h + self.padding and draw_y < self.height - self.padding:
                if l_type == "surface":
                    self.surface.blit(item, (self.padding, draw_y))
                elif l_type == "image":
                    # Center-align the screenshot illustration
                    img_x = self.padding + (clip.w - item.get_width()) // 2
                    self.surface.blit(item, (img_x, draw_y))
                    # Draw a nice thin outline border
                    border_rect = pygame.Rect(img_x, draw_y, item.get_width(), item.get_height())
                    pygame.draw.rect(self.surface, (70, 72, 90), border_rect, 1, border_radius=4)
        self.surface.set_clip(None)

        # Scrollbar
        tx = self.width - self.scrollbar_margin - self.scrollbar_width
        ty = self.header_h + self.padding
        thtrack = clip.h
        pygame.draw.rect(self.surface, self.scrollbar_track,
                         (tx, ty, self.scrollbar_width, thtrack),
                         border_radius=4)
        if self.content_height > 0:
            th = max(int(thtrack * clip.h / self.content_height), 20)
            ty_thumb = ty + int(self.scroll_y * (thtrack - th) / max(1, self.max_scroll))
            pygame.draw.rect(self.surface, self.scrollbar_thumb,
                             (tx+1, ty_thumb, self.scrollbar_width-2, th),
                             border_radius=3)

        # Fade & blit to final screen
        self.surface.set_alpha(self.alpha)
        screen.blit(self.surface, self.rect.topleft)

    def run(self, screen, version=None):
        """
        Displays the popup only if the stored version differs from `version`.
        Writes the current version to the .version file upon completion.
        """
        if self.already:
            return
        self.already = True
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        version_path = os.path.join(script_dir, ".version")

        stored = None
        if os.path.isfile(version_path):
            self.v_file_exist = True
            try:
                with open(version_path, "r") as f:
                    stored = float(f.read().strip())
            except Exception:
                stored = None

        if stored is None:
            if version is None:
                raise ValueError("No .version file found; you must pass `version=` to run().")
            stored = -1.0

        if version is None:
            current = stored
        else:
            current = float(version)

        # Only run popup if versions differ
        if stored != current:
            self.version_number = current
            self.title = f"Version {current:.1f} - Nouveau système de particules"

            bg = screen.copy()
            clock = pygame.time.Clock()

            while self.active:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        self.active = False
                    elif e.type == pygame.VIDEORESIZE:
                        w, h = e.w, e.h
                        screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                        self.screen_w, self.screen_h = w, h
                        self.width  = int(self.screen_w * 0.70)
                        self.height = int(self.screen_h * 0.75)
                        self.rect = pygame.Rect(
                            (self.screen_w - self.width) // 2,
                            (self.screen_h - self.height) // 2,
                            self.width, self.height
                        )
                        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                        self.cancel_center = (self.width - self.btn_radius - 16, self.header_h // 2)

                        # Recompute scaled screenshots and layout coordinates on resize
                        self._load_and_scale_images()
                        self._prepare_lines()
                        self.content_height = self._calc_content_height()
                        self.max_scroll     = max(0, self.content_height - (self.height - self.header_h - 2*self.padding))
                        self.scroll_y       = min(self.scroll_y, self.max_scroll)

                        bg = screen.copy()
                    else:
                        self.handle_event(e)

                self.update()
                screen.blit(bg, (0,0))
                self.draw(screen)
                pygame.display.flip()
                clock.tick(60)

            # Save the version value
            try:
                with open(version_path, "w") as f:
                    f.write(f"{current}")
            except Exception as e:
                print("Erreur écriture .version:", e)
