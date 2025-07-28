import pygame
import colorsys
import math
from editor.ui.Font import FontManager
from editor.ui.Input import InputField



class ColorPicker:
    def __init__(self, rect, initial_color=(255,128,64),on_confirm=None,on_cancel=None):
        self.rect = pygame.Rect(rect)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.font_manager = FontManager()
        self.font = self.font_manager.get(size=18)
        self._initial_color=initial_color

        # zone de drag de la "fenêtre"
        self.header_height = 20
        self.dragging_window = False
        self.window_drag_offset = (0, 0)

        # géométrie principale
        side = min(self.rect.w, self.rect.h) - 50
        self.wheel_radius = int(side // 2.2)
        self.wheel_center = (self.rect.w // 2, self.wheel_radius + 30)

        # slider Value centré
        slider_w = side
        slider_h = 12
        slider_x = (self.rect.w - slider_w)//2
        slider_y = self.wheel_center[1]*2-16
        self.val_slider_rect = pygame.Rect(slider_x, slider_y, slider_w, slider_h)

        # prérendu roue HS
        self._make_wheel(supersample=2)

        # Inputs pour #hex, rgb
        input_w = side
        input_h = 24
        input_x = (self.rect.w - input_w)//2
        gap = 8
        y0 = self.val_slider_rect.bottom + 20
        self.inputs = []
        for i in range(2):
                ip_rect = (input_x, y0 + i*(input_h+gap), input_w, input_h)
                # hex-field est index 0, rgb index 1
                self.inputs.append(InputField(ip_rect,
                                            font=self.font,
                                            on_change=self.on_input_change))
        # ── Aperçu couleur ──────────────────────────────────────────
        prev_size = 30
        px = self.rect.x + self.rect.w - input_x - prev_size
        py = self.inputs[-1].rect.bottom + 10
        self.preview_rect = pygame.Rect(px, py, prev_size, prev_size)
        # composantes HSV
        r, g, b = [c/255 for c in initial_color]
        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r, g, b)
        self._update_color()

        # ── Boutons Valider / Annuler ──────────────────────────────────

        self.on_confirm = on_confirm or (lambda: None)
        self.on_cancel  = on_cancel  or (lambda: None)
        self.confirm_text = "OK"
        self.cancel_radius = 5
        self.cancel_color = (200, 71, 88)
        self.cancel_margin = 4

        self.cancel_center = (
            self.rect.w - self.cancel_radius - self.cancel_margin,
            self.cancel_radius + self.cancel_margin
        )



        # aperçu responsive en dessous
        prev_h = 25
        prev_w = self.rect.w - 300
        prev_x =  (self.rect.w - prev_w)//2
        prev_y = self.inputs[-1].rect.bottom + 10
        self.preview_rect = pygame.Rect(prev_x, prev_y, prev_w, prev_h)
        self.preview_radius = 10

        # état d’entrée
        self.dragging_wheel = False
        self.dragging_slider = False
        self.inputs[0].text = "#{:02x}{:02x}{:02x}".format(*initial_color)
        self.inputs[1].text = f"rgb{initial_color}"

    def _confirm_action(self):
        self.on_confirm(self.current_color)

    def _cancel_action(self):
        self.on_cancel()
        r,g,b = self._initial_color
        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        self._update_color()

    def on_input_change(self, new_text):
        # 1) Détermination du (r,g,b) à partir du champ actif
        if self.inputs[0].active:
            # on édite le HEX
            htxt = self.inputs[0].text.lstrip('#')
            if len(htxt) == 6 and all(c in "0123456789abcdefABCDEF" for c in htxt):
                r = int(htxt[0:2], 16)
                g = int(htxt[2:4], 16)
                b = int(htxt[4:6], 16)
            else:
                return
        elif self.inputs[1].active:
            # on édite le RGB
            rtxt = self.inputs[1].text
            parts = rtxt.strip().lstrip('rgb(').rstrip(')').split(',')
            if len(parts) == 3 and all(p.strip().isdigit() for p in parts):
                r, g, b = map(int, parts)
                if not all(0 <= v <= 255 for v in (r, g, b)):
                    return
            else:
                return
        else:
            return

        # 2) Conversion en HSV et mise à jour interne
        rn, gn, bn = [c/255 for c in (r, g, b)]
        self.hue, self.sat, self.val = colorsys.rgb_to_hsv(rn, gn, bn)
        # cette méthode met à jour self.current_color
        self._update_color()

        # 3) Réécriture **immédiate** des deux champs pour qu’ils soient cohérents
        hex_s = "#{:02x}{:02x}{:02x}".format(r, g, b)
        rgb_s = f"rgb({r},{g},{b})"
        if self.inputs[0].active:
            self.inputs[1].text = rgb_s
        else:
            self.inputs[0].text = hex_s



    def _make_wheel(self, supersample=2):
        size = 2*self.wheel_radius * supersample
        surf = pygame.Surface((size, size), flags=pygame.SRCALPHA)
        center = size/2
        radius = self.wheel_radius * supersample
        for x in range(size):
            for y in range(size):
                dx, dy = x-center, y-center
                dist = math.hypot(dx, dy)
                if dist <= radius:
                    angle = math.atan2(dy, dx)
                    h = (angle / (2*math.pi)) % 1.0
                    s = dist / radius
                    r,g,b = colorsys.hsv_to_rgb(h, s, 1)
                    surf.set_at((x,y), (int(r*255),int(g*255),int(b*255)))
        self.wheel_surf = pygame.transform.smoothscale(
            surf, (2*self.wheel_radius, 2*self.wheel_radius)
        )

    def _update_color(self):
        r, g, b = colorsys.hsv_to_rgb(self.hue, self.sat, self.val)
        self.current_color = (int(r*255), int(g*255), int(b*255))

        # seulement si **aucun** champ n'est actif
        if not any(inp.active for inp in self.inputs):
            hex_s = "#{:02x}{:02x}{:02x}".format(*self.current_color)
            rgb_s = f"rgb{self.current_color}"
            self.inputs[0].text = hex_s
            self.inputs[1].text = rgb_s



    def handle_event(self, event):
        # --- Calcul des coordonnées locales et globales ---
       # --- Calcul des coordonnées locales et globales ---
        if hasattr(event, 'pos'):
            mx, my = event.pos
            rel = (mx - self.rect.x, my - self.rect.y)
        else:
            rel = None

        # --- 1) Gestion du drag de la fenêtre en priorité ---
        if rel and event.type == pygame.MOUSEBUTTONDOWN:
            x, y = rel

            # on ne drague que dans le header
            if 0 <= y <= self.header_height:
                # exclure explicitement la zone du bouton annuler
                cx, cy = self.cancel_center
                if (x-cx)**2 + (y-cy)**2 <= self.cancel_radius**2:
                    # clic sur Close → on laisse passer pour le traitement normal plus bas
                    pass
                else:
                    # vérifier qu'on n'est pas sur la roue, le slider ni un input
                    dx, dy = x - self.wheel_center[0], y - self.wheel_center[1]
                    in_wheel  = (dx*dx + dy*dy) <= self.wheel_radius**2
                    in_slider = self.val_slider_rect.collidepoint(rel)
                    in_input  = any(
                        inp.rect.collidepoint((mx, my))
                        for inp in self.inputs
                    )
                    if not (in_wheel or in_slider or in_input):
                        self.dragging_window = True
                        self.window_drag_offset = (x, y)
                        return  # on démarre le drag-window, on stoppe tout

        # --- 2) Fin de drag pour tout ---
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging_window = False
            self.dragging_wheel  = False
            self.dragging_slider = False

        # --- 3) Drag-window en cours ---
        if rel and event.type == pygame.MOUSEMOTION and self.dragging_window:
            new_x = mx - self.window_drag_offset[0]
            new_y = my - self.window_drag_offset[1]
            surf = pygame.display.get_surface()
            if surf:
                screen_w, screen_h = surf.get_size()
                new_x = max(0, min(new_x, screen_w  - self.rect.w))
                new_y = max(0, min(new_y, screen_h - self.rect.h))
            self.rect.topleft = (new_x, new_y)
            return

        elif event.type == pygame.MOUSEMOTION and self.dragging_window:
            # déplacer la "fenêtre"
            new_x = mx - self.window_drag_offset[0]
            new_y = my - self.window_drag_offset[1]
            self.rect.topleft = (new_x, new_y)
            return  # pendant le drag-window, on n'évalue pas la roue/slider/inputs

        # --- 2) Propagation aux inputs (texte, sélection…) ---
        if hasattr(event, 'pos'):
            local_pos = rel
            event_for_inputs = pygame.event.Event(
                event.type,
                {**{k: v for k, v in event.__dict__.items() if k != 'pos'},
                 'pos': local_pos}
            )
        else:
            event_for_inputs = event

        for inp in self.inputs:
            inp.handle_event(event_for_inputs)

        # --- 3) Si un champ texte est actif, on re-parse au clavier ---
        if any(inp.active for inp in self.inputs) and event.type == pygame.KEYDOWN:
            txt0 = self.inputs[0].text.lstrip('#')
            txt1 = self.inputs[1].text
            try:
                if len(txt0) == 6 and all(c in "0123456789abcdefABCDEF" for c in txt0):
                    r = int(txt0[0:2], 16)
                    g = int(txt0[2:4], 16)
                    b = int(txt0[4:6], 16)
                else:
                    parts = txt1.strip().lstrip('rgb(').rstrip(')').split(',')
                    if len(parts) == 3:
                        r, g, b = [int(p) for p in parts]
                        if not all(0 <= v <= 255 for v in (r, g, b)):
                            return
                    else:
                        raise ValueError
                rn, gn, bn = [c/255 for c in (r, g, b)]
                self.hue, self.sat, self.val = colorsys.rgb_to_hsv(rn, gn, bn)
                self._update_color()
            except Exception:
                pass
            return

        # --- 4) Roue, slider, boutons Annuler/OK ---
        if event.type == pygame.MOUSEBUTTONDOWN and rel:
            # roue
            dx, dy = rel[0] - self.wheel_center[0], rel[1] - self.wheel_center[1]
            if math.hypot(dx, dy) <= self.wheel_radius:
                self.dragging_wheel = True
                return
            # slider
            if self.val_slider_rect.collidepoint(rel):
                self.dragging_slider = True
                return
            # bouton Annuler (le rond rouge)
            gx = self.rect.x + self.cancel_center[0]
            gy = self.rect.y + self.cancel_center[1]
            if (mx-gx)**2 + (my-gy)**2 <= self.cancel_radius**2:
                self._cancel_action()
                return
            # clic sur l'aperçu (zone OK)
            if self.preview_rect.collidepoint(rel):
                self._confirm_action()
                return

        elif event.type == pygame.MOUSEMOTION:
            # déplacement dans la roue
            if self.dragging_wheel:
                dx, dy = rel[0] - self.wheel_center[0], rel[1] - self.wheel_center[1]
                self.sat = min(max(math.hypot(dx, dy)/self.wheel_radius, 0), 1)
                angle = math.atan2(dy, dx)
                self.hue = (angle/(2*math.pi)) % 1
                self._update_color()
            # déplacement dans le slider
            elif self.dragging_slider:
                v = (rel[0] - self.val_slider_rect.x) / self.val_slider_rect.w
                self.val = min(max(v, 0), 1)
                self._update_color()

        # les autres événements (KEYUP, etc.) n'ont pas d'effet supplémentaire




    def draw(self, target_surf):
        self.surface.fill((30,30,30))
        pygame.draw.rect(self.surface, (50,50,50),
                                pygame.Rect(0, 0, self.rect.w, self.header_height))
        # éventuellement un titre
        txt = self.font.render("Color Picker", True, (200,200,200))
        self.surface.blit(txt, (5, (self.header_height - txt.get_height())//2))
        # roue
        wheel_tl = (self.wheel_center[0]-self.wheel_radius,
                    self.wheel_center[1]-self.wheel_radius)
        self.surface.blit(self.wheel_surf, wheel_tl)
        # indicateur
        ang = 2*math.pi*self.hue
        dx = math.cos(ang)*self.sat*self.wheel_radius
        dy = math.sin(ang)*self.sat*self.wheel_radius
        pos = (int(self.wheel_center[0]+dx), int(self.wheel_center[1]+dy))
        try:
            pygame.draw.aacircle(self.surface, (0,0,0), pos, 6, 1)
        except:
            pygame.draw.circle(self.surface, (0,0,0), pos, 6, 1)

        # gradient - slider
        grad = pygame.Surface((self.val_slider_rect.w, 1), flags=pygame.SRCALPHA)
        for i in range(self.val_slider_rect.w):
            c = colorsys.hsv_to_rgb(self.hue, self.sat, i / self.val_slider_rect.w)
            grad.set_at((i, 0), (int(c[0]*255), int(c[1]*255), int(c[2]*255), 255))
        grad = pygame.transform.scale(grad, self.val_slider_rect.size)
        mask = pygame.Surface(self.val_slider_rect.size, flags=pygame.SRCALPHA)
        pygame.draw.rect(mask, (255,255,255,255), mask.get_rect(), border_radius=3)
        mask.blit(grad, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        self.surface.blit(mask, self.val_slider_rect.topleft)
        pygame.draw.rect(self.surface,(62, 62, 62),self.val_slider_rect,width=1,border_radius=3)
        # curseur du slider
        hw, hh = 8, self.val_slider_rect.h+4
        hx = self.val_slider_rect.x + int(self.val*(self.val_slider_rect.w-hw))
        hy = self.val_slider_rect.y - 2
        handle = pygame.Rect(hx,hy,hw,hh)
        pygame.draw.rect(self.surface, (210, 210, 210), handle, border_radius=3)


        for inp in self.inputs:
            inp.draw(self.surface)

        # ── Dessin de l’aperçu de la couleur actuelle ───────────────
        pygame.draw.rect(self.surface, self.current_color,
                         self.preview_rect, border_radius=4)
        # bordure neutre
        pygame.draw.rect(self.surface, (62,62,62),
                         self.preview_rect, width=1, border_radius=4)
        # ──          TEXTE “OK” SUR L’APERÇU                ──────────
        # calcul de la luminosité (pour choisir blanc ou noir)
        r, g, b = self.current_color
        lum = 0.2126*r + 0.7152*g + 0.0722*b
        text_col = (255,255,255) if lum < 128 else (0,0,0)

        txt_surf = self.font.render(self.confirm_text, True, text_col)
        tx = self.preview_rect.x + (self.preview_rect.w - txt_surf.get_width())//2
        ty = self.preview_rect.y + (self.preview_rect.h - txt_surf.get_height())//2
        self.surface.blit(txt_surf, (tx, ty))

        # ──      ROND ROUGE “ANNULER” ───────────────────────────────
        cr = self.cancel_radius
        cx, cy = self.cancel_center
        try:
            pygame.draw.aacircle(self.surface, self.cancel_color, (cx, cy), cr)
        except:
            pygame.draw.circle(self.surface, self.cancel_color, (cx, cy), cr)

        mask_picker = pygame.Surface(self.rect.size, flags=pygame.SRCALPHA)
        pygame.draw.rect(mask_picker, (255,255,255,255),
                         mask_picker.get_rect(),
                         border_radius=5)
        mask_picker.blit(self.surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        target_surf.blit(mask_picker, self.rect.topleft)
        pygame.draw.rect(target_surf,(62, 62, 62),self.rect,width=1,border_radius=3)





# Demo
if __name__ == "__main__":
    show_picker=True
    def confirm(color):
        print(f"Couleur choisie {color}")
    
    def close():
        global show_picker
        print("Close")
        show_picker=False

    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    picker = ColorPicker(rect=(100,100,220,330), initial_color=(200,50,100),on_confirm=confirm,on_cancel=close)
    clock = pygame.time.Clock()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if show_picker:
                picker.handle_event(e)


        screen.fill((20,20,20))
        if show_picker:
            picker.draw(screen)
        pygame.display.flip()
        clock.tick(60)



