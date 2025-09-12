import pygame
import time
import os

from editor.ui.Font import FontManager

class ReleaseNotesPopup:
    def __init__(self, screen_size, on_close, font_name=None):
        # Dimensions: 55% width, 55% height
        self.screen_w, self.screen_h = screen_size
        self.width  = int(self.screen_w * 0.55)
        self.height = int(self.screen_h * 0.55)
        self.rect = pygame.Rect(
            (self.screen_w - self.width) // 2,
            (self.screen_h - self.height) // 2,
            self.width, self.height
        )
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Fonts
        self.font_manager = FontManager()
        self.title_font   = self.font_manager.get(size=28)
        self.section_font = self.font_manager.get(size=22)
        self.text_font    = self.font_manager.get(size=18)

        # Style colors
        self.bg_color        = (28, 28, 30, 240)
        self.header_color    = (44, 44, 46)
        self.border_color    = (60, 60, 62)
        self.section_color   = (109, 132, 165)
        self.text_color      = (209, 209, 214)
        self.subtitle_color  = (180, 180, 185)
        self.divider_color   = (72, 72, 74)
        self.button_color    = (200, 71, 88)

        # Scrollbar
        self.scrollbar_track   = (50, 50, 52)
        self.scrollbar_thumb   = (100, 100, 104)
        self.scrollbar_width   = 6
        self.scrollbar_margin  = 12

        # Layout
        self.btn_radius        = 5
        self.padding           = 16
        self.header_h          = 32

        # Placeholder for title/version
        self.version_number    = None
        self.title             = ""
        self.subtitle = (
            "Version 1.1 - Optimisations et améliorations"
        )

        # Release sections
        self.sections = [
                ("Optimisations & Corrections",
     "Des optimisations ont été apportées à l'éditeur. "
     "L'utilisation des parallax n'a désormais plus d'impact significatif sur les performances, même dans des scènes complexes. "
     "De plus, le zoom étendu sur la carte n'entraîne plus de chutes importantes de FPS. "
     "Ces améliorations permettent de gérer des cartes plus lourdes et plus vastes avec une fluidité accrue. "
     "Enfin, un correctif a été appliqué au mode Play: le fond n'était pas redessiné correctement, "
     "ce qui provoquait un affichage erroné où l'écran précédent restait visible. Ce comportement a été corrigé."),
            # ("Interface & Dialogues",
            #  "L'interface a été entièrement revue pour offrir une meilleure lisibilité et une cohérence visuelle solide. "
            #  "Les anciennes boîtes de dialogue basées sur Tkinter ont été retirées au profit de composants SDL natifs, "
            #  "évitant ainsi les problèmes de compatibilité, notamment sur macOS. "
            #  "L'explorateur de fichiers et le sélecteur de couleurs sont désormais intégrés directement dans l'éditeur, "
            #  "rapides et plus adaptés à son ergonomie."),
            # ("Animations de Tiles",
            #  "Un système de timeline multi-calques permet de concevoir des animations détaillées pour les tiles. "
            #  "Vous pouvez poser, déplacer ou supprimer des keyframes librement, "
            #  "et contrôler la vitesse, la durée, et le comportement en boucle de chaque séquence."),
            # ("Mode Play & Personnage",
            #  "Le mode Play permet de lancer rapidement un niveau avec un personnage jouable déjà configuré. "
            #  "Ce dernier gère les collisions, les déplacements, les animations et les sauts. "
            #  "Plusieurs paramètres peuvent être ajustés à la volée : gravité, point d'apparition, vitesse de mouvement, "
            #  "et un mode fly utile pour explorer ou déboguer."),
            # ("Éditeur Nodal & Système Audio",
            #  "L'éditeur nodal permet de structurer la logique du jeu, les interactions et les déclencheurs de manière visuelle. "
            #  "Plus de 80 nœuds sont disponibles, couvrant la logique, le joueur, le monde, les événements, la physique ou encore l'audio spatial. "
            #  "Les graphes sont enregistrés dans un format dédié (.lvg), indépendant du niveau, pour faciliter la lisibilité et la modularité du projet.")
        ]
        self.already=False
        # Pre-rendered text lines
        self._prepare_lines()

        # Scrolling
        self.content_height = self._calc_content_height()
        self.scroll_y       = 0
        self.max_scroll     = max(0, self.content_height - (self.height - self.header_h - 2*self.padding))

        # Close button
        cr, m = self.btn_radius, 10
        self.cancel_center = (self.width - cr - m, cr + m)
        self.on_close      = on_close

        # Fade-in
        self.alpha         = 0
        self.fade_duration = 0.5
        self.start_time    = time.time()
        self.active        = True

        # Drag states
        self.dragging_thumb   = False
        self.dragging_header  = False
        self.drag_start_y     = 0
        self.scroll_start     = 0
        self.header_offset    = (0, 0)

    def _prepare_lines(self):
        """Pre-render title/subtitle/sections into self.lines."""
        self.lines = []
        y = self.header_h + self.padding * 2 + 2
        max_w = self.width - 2*self.padding - self.scrollbar_width - 4

        # Subtitle
        for line in self.subtitle.split('\n'):
            surf = self.text_font.render(line, True, self.subtitle_color)
            self.lines.append((y, surf))
            y += surf.get_height() + 6
        y += self.padding

        # Sections
        for title, body in self.sections:
            ts = self.section_font.render(title, True, self.section_color)
            self.lines.append((y, ts))
            y += ts.get_height() + 4

            words, buf = body.split(' '), ''
            for w in words:
                test = (buf + ' ' + w).strip()
                if self.text_font.size(test)[0] > max_w and buf:
                    surf = self.text_font.render(buf, True, self.text_color)
                    self.lines.append((y, surf))
                    y += surf.get_height() + 4
                    buf = w
                else:
                    buf = test
            if buf:
                surf = self.text_font.render(buf, True, self.text_color)
                self.lines.append((y, surf))
                y += surf.get_height() + 4

            div = pygame.Surface((max_w, 1)); div.fill(self.divider_color)
            self.lines.append((y + self.padding//2, div))
            y += div.get_height() + self.padding

    def _calc_content_height(self):
        if not self.lines:
            return 0
        last_y, last_surf = self.lines[-1]
        return last_y + last_surf.get_height()

    def handle_event(self, event):
        if not self.active: return

        # compute scrollbar geometry
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

            # Close button
            if (rx - self.cancel_center[0])**2 + (ry - self.cancel_center[1])**2 <= self.btn_radius**2:
                self.on_close()
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

        # Mouse wheel
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

        # Base
        self.surface.fill(self.bg_color)
        pygame.draw.rect(self.surface, self.border_color,
                         self.surface.get_rect(), 2, border_radius=8)

        # Header
        pygame.draw.rect(self.surface, self.header_color,
                         (0, 0, self.width, self.header_h),
                         border_top_left_radius=4,
                         border_top_right_radius=4)
        title_surf = self.title_font.render(self.title, True, self.text_color)
        self.surface.blit(title_surf,
                          (self.padding, (self.header_h - title_surf.get_height())//2))
        try:
            pygame.draw.aacircle(self.surface, self.button_color,
                             self.cancel_center, self.btn_radius)
        except:
            pygame.draw.circle(self.surface, self.button_color,
                             self.cancel_center, self.btn_radius)            

        # Content clip
        clip = pygame.Rect(
            self.padding,
            self.header_h + self.padding,
            self.width - 2*self.padding - self.scrollbar_width - 4,
            self.height - self.header_h - 2*self.padding
        )
        self.surface.set_clip(clip)
        for y, surf in self.lines:
            self.surface.blit(surf, (self.padding, y - self.scroll_y))
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

        # Fade & blit
        self.surface.set_alpha(self.alpha)
        screen.blit(self.surface, self.rect.topleft)

    def run(self, screen, version=None):
        """
        Displays the popup only if the stored .version differs from `version`.
        If no .version file exists, `version` must be provided.
        After showing, writes the current version to the .version file.
        """
        if self.already:
            return
        self.already=True
        # Determine paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        version_path = os.path.join(script_dir, ".version")

        # Read existing version
        stored = None
        if os.path.isfile(version_path):
            try:
                with open(version_path, "r") as f:
                    stored = float(f.read().strip())
            except Exception:
                stored = None

        # If no stored version, require version param
        if stored is None:
            if version is None:
                raise ValueError("No .version file found; you must pass `version=` to run().")
            stored = -1.0  # force display

        # Compare
        if version is None:
            current = stored
        else:
            current = float(version)

        # Only run popup if versions differ
        if stored != current:
            # update title to reflect version
            self.version_number = current
            self.title = f"Version {current:.1f} - Éditeur stable"

            # capture background once
            bg = screen.copy()
            clock = pygame.time.Clock()

            # show popup
            while self.active:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        self.active = False
                    else:
                        self.handle_event(e)

                self.update()
                screen.blit(bg, (0,0))
                self.draw(screen)
                pygame.display.flip()
                clock.tick(60)

            # write new version
            try:
                with open(version_path, "w") as f:
                    f.write(f"{current}")
            except Exception as e:
                print("Erreur écriture .version:", e)

# Exemple d'utilisation
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
    screen.fill((20,20,20))
    pygame.display.flip()

    popup = ReleaseNotesPopup(
        screen_size=screen.get_size(),
        on_close=lambda: print("Popup fermée !")
    )
    # passez la version actuelle pour trigger
    popup.run(screen, version=1.0)

    pygame.quit()
