import pygame
from editor.ui.Font import FontManager
from editor.ui.Input import InputField

class DialogBox:
    def __init__(self, rect, title, description,
                 buttons,
                 inputs=None,
                 on_cancel=None,
                 font=None,active=True):
        """
        rect: (x,y,w,h)
        title: str
        description: str (peut contenir \n)
        buttons: list de dicts {'text': str, 'callback': func}
        inputs: list de dicts {'placeholder': str, 'rules': [callable]}
        on_cancel: fonction appelée par le bouton rouge du header
        """
        self.active=active
        self.rect = pygame.Rect(rect)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.font_manager = FontManager()
        self.font = font or self.font_manager.get(size=18)

        # Styles
        self.bg_color       = (30,30,30)
        self.header_color   = (50,50,50)
        self.text_color     = (200,200,200)
        self.border_color   = (62,62,62)
        self.btn_color = (80, 80, 80)
        self.btn_hover_color = (110, 110, 110)
        self.btn_text_color = (255,255,255)
        self.btn_radius     = 2
        self.padding        = 10
        self.btn_spacing    = 25

        # Header
        self.header_h       = 20
        self.title          = title

        # Bouton rouge Annuler en header
        self.on_cancel = on_cancel or (lambda: None)
        self.cancel_radius = 5
        self.cancel_margin = 4
        self.cancel_center = (
            self.rect.w - self.cancel_radius - self.cancel_margin,
            self.cancel_radius + self.cancel_margin
        )

        # Description (wrap)
        self.desc_surfs = self._wrap_text(description,
                                          self.font,
                                          self.rect.w - 2*self.padding)
        
        self.inputs_conf = inputs or []
        self.inputs       = []  # liste alternée de (Surface label ou InputField)
        y = self.header_h + self.padding + sum(s.get_height() for s in self.desc_surfs) + self.padding//2
        for conf in self.inputs_conf:
            # 1) Label (optionnel)
            label_text = conf.get('label')
            if label_text:
                lbl = self.font.render(label_text, True, self.text_color)
                self.inputs.append(('label', lbl, (self.padding, y)))
                y += lbl.get_height() + 2

            # 2) InputField
            ip = InputField(
                rect=(self.padding, y,
                      self.rect.w - 2*self.padding, 24),
                font=self.font,
                placeholder=conf.get('placeholder', ''),
                text=conf.get('text', ''),
                on_change=lambda txt, ip_ref=None, rules=conf.get('rules', []):
                           self._validate_input(ip_ref, txt, rules)
            )
            # corriger le on_change pour capturer ip
            ip.on_change = lambda txt, ip_ref=ip, rules=conf.get('rules', []): self._validate_input(ip_ref, txt, rules)

            self.inputs.append(('input', ip, None))
            y += ip.rect.height + self.padding//2
        self._renderables = self.inputs  

        # Sélectionner uniquement les InputField pour self.inputs
        self.inputs = [
            widget
            for kind, widget, _ in self._renderables
            if kind == 'input'
        ]
        # Buttons (juste sous inputs)
        self.inputs_end_y = y
 
        # Buttons (juste sous inputs)
        self.buttons = []
        btn_surfs = []
        total_btn_w = 0
        for b in buttons:
            surf = self.font.render(b['text'], True, self.btn_text_color)
            w = surf.get_width() + 2*self.padding + 3
            h = surf.get_height() + self.padding//2 + 3
            btn_surfs.append((b, surf, (w, h)))
            total_btn_w += w + self.btn_spacing
        total_btn_w -= self.btn_spacing
        x0 = (self.rect.w - total_btn_w)//2

        # on place les boutons juste en-dessous de self.inputs_end_y
        y0 = self.inputs_end_y + self.padding//2 + 10

        for b, surf, (w,h) in btn_surfs:
            btn_rect = pygame.Rect(x0, y0, w, h)
            self.buttons.append({'rect': btn_rect, 'surf': surf, **b})
            x0 += w + self.btn_spacing

        # Drag
        self.dragging = False
        self.drag_offset = (0,0)

    def _validate_input(self, ip, text, rules):
        # supprime tous les caractères qui ne passent pas
        filtered = text
        for rule in rules:
            filtered = ''.join(ch for ch in filtered if rule(ch))
        if filtered != ip.text:
            ip.text = filtered
            # replacer le curseur en fin
            ip.cursor_pos = len(filtered)

    def _wrap_text(self, text, font, max_w):
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split(' ')
            cur = ''
            for w in words:
                test = cur + (' ' if cur else '') + w
                if font.size(test)[0] > max_w and cur:
                    lines.append(font.render(cur, True, self.text_color))
                    cur = w
                else:
                    cur = test
            if cur:
                lines.append(font.render(cur, True, self.text_color))
        return lines

    def handle_event(self, event):
        if not self.active:
            return
        # Gestion du drag fenêtre
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx,my = event.pos
            rel = (mx - self.rect.x, my - self.rect.y)
            # si clic dans header hors bouton rouge
            if 0 <= rel[1] <= self.header_h:
                dx = rel[0] - self.cancel_center[0]
                dy = rel[1] - self.cancel_center[1]
                if dx*dx + dy*dy > self.cancel_radius**2:
                    self.dragging = True
                    self.drag_offset = rel
                else:
                    # clic sur rond rouge
                    self.on_cancel()
            # clic sur boutons
            for btn in self.buttons:
                if btn['rect'].collidepoint(rel):
                    btn['callback']()
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mx,my = event.pos
            self.rect.topleft = (mx - self.drag_offset[0],
                                 my - self.drag_offset[1])
        # Propager aux inputs
        local_event = event
        if hasattr(event, 'pos'):
            local_event = pygame.event.Event(
                event.type,
                {**event.__dict__,
                 'pos': (event.pos[0]-self.rect.x, event.pos[1]-self.rect.y)}
            )

        for kind, widget, _ in self._renderables:
            if kind == 'input':
                widget.handle_event(local_event)

    def draw(self, target):
        if not self.active:
            return
        # Fond & bordure
        self.surface.fill(self.bg_color)
        pygame.draw.rect(self.surface,
                         self.border_color,
                         self.surface.get_rect(),
                         width=1, border_radius=5)
        # Header
        pygame.draw.rect(self.surface,
                         self.header_color,
                         pygame.Rect(0,0,self.rect.w,self.header_h),
                         border_radius=5)
        # Titre
        txt = self.font.render(self.title, True, self.text_color)
        self.surface.blit(txt, (self.padding,
                                (self.header_h - txt.get_height())//2))
        # Rond rouge Annuler
        try:
            pygame.draw.aacircle(self.surface,
                                (200,71,88),
                                self.cancel_center,
                                self.cancel_radius)
        except:
            pygame.draw.circle(self.surface,
                                (200,71,88),
                                self.cancel_center,
                                self.cancel_radius)            
        # Description
        y = self.header_h + self.padding//2+5
        for s in self.desc_surfs:
            self.surface.blit(s, (self.padding, y))
            y += s.get_height()

        # dessin des inputs (labels + champs)
        for kind, widget, pos in self._renderables:
            if kind == 'label':
                # widget est une Surface
                self.surface.blit(widget, pos)
            else:
                # widget est un InputField
                widget.draw(self.surface)

        # Boutons
        mx, my = pygame.mouse.get_pos()
        local_mouse = (mx - self.rect.x, my - self.rect.y)
        for btn in self.buttons:
            color=self.btn_hover_color if btn['rect'].collidepoint(local_mouse) else self.btn_color,
            pygame.draw.rect(self.surface,
                             color,
                             btn['rect'],
                             border_radius=self.btn_radius)
            # texte centré, notamment verticalement
            tx = btn['rect'].x + (btn['rect'].w - btn['surf'].get_width())//2
            ty = btn['rect'].y + (btn['rect'].h - btn['surf'].get_height())//2
            self.surface.blit(btn['surf'], (tx,ty))

        # Blit final
        target.blit(self.surface, self.rect.topleft)


# ---------------- Démo ----------------
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800,600), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    running = True

    # règle : laisser passer que les chiffres
    is_digit = lambda ch: ch.isdigit()

    dlg = DialogBox(
        rect=(150,100,300,125),
        title="Saisir un nombre",
        description="Entrez un nombre entier :",
        inputs=[{'placeholder': 'Chiffres uniquement', 'rules':[is_digit]}],
        buttons=[
            {'text':'Annuler', 'callback':lambda: print("Annulé")},
            {'text':'Valider', 'callback':lambda: print("Validé !")}
        ],
        on_cancel=lambda: print("Cancel via header")
    )
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            dlg.handle_event(e)

        screen.fill((20,20,20))
        dlg.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
