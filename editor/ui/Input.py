import pygame

from editor.ui.Font import FontManager


class InputField:
    def __init__(self, rect, text="", bg_color = (41, 41, 41), text_color = (200, 200, 200),
                 border_color=(62, 62, 62), border_radius=3, font=None, on_change=None,placeholder=None,placeholder_color=(120, 120, 120),blink_interval=500):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font_manager = FontManager()
        self.font = font or self.font_manager.get(size=18)
        self.bg_color = bg_color
        self.text_color = text_color
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.border_color = border_color
        self.border_radius = border_radius
        self.cursor_pos = len(text)
        self.active = False
        self.cursor_timer = 0
        self.on_change = on_change
        self.sel_start = self.sel_end = self.cursor_pos
        self.dragging = False
        self.blink_interval = blink_interval
        self.last_blink_switch = 0
        self.cursor_visible = True
        self.offset_x = 0

    def has_selection(self):
        return self.sel_start != self.sel_end

    def _clear_selection(self):
        self.sel_start = self.sel_end = self.cursor_pos

    def _delete_selection(self):
        start = min(self.sel_start, self.sel_end)
        end   = max(self.sel_start, self.sel_end)
        self.text = self.text[:start] + self.text[end:]
        self.cursor_pos = start
        self._clear_selection()

    def _pos_from_x(self, rel_x):
        if rel_x <= 0:
            return 0
        # Balayer chaque position possible et mesurer la largeur
        for i in range(len(self.text) + 1):
            w = self.font.size(self.text[:i])[0]
            if w >= rel_x:
                return i
        # Au-delà de la longueur du texte, on place le curseur en fin
        return len(self.text)

    def _ensure_cursor_visible(self):
        padding = 5
        avail_width = self.rect.w - 2 * padding
        cursor_px = self.font.size(self.text[:self.cursor_pos])[0]
        if cursor_px - self.offset_x > avail_width:
            self.offset_x = cursor_px - avail_width
        if cursor_px - self.offset_x < 0:
            self.offset_x = cursor_px
        if self.offset_x < 0:
            self.offset_x = 0

    def handle_event(self, event):
        # 1) Clic souris -> activation, position curseur et début de sélection
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                padding = 5
                # on ajoute offset_x pour retrouver le bon index dans le texte décalé
                rel_x = event.pos[0] - (self.rect.x + padding) + self.offset_x
                self.cursor_pos = self._pos_from_x(rel_x)
                self.sel_start = self.sel_end = self.cursor_pos
                self.dragging = True
                self.active = True
            else:
                self.active = False

        # 2) Drag souris -> étendre la sélection
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            padding = 5
            # on ajoute offset_x pour retrouver le bon index dans le texte décalé
            rel_x = event.pos[0] - (self.rect.x + padding) + self.offset_x
            self.sel_end = self._pos_from_x(rel_x)
            self.cursor_pos = self.sel_end
            self._ensure_cursor_visible()

        # 3) Relâchement souris -> fin du drag
        elif event.type == pygame.MOUSEBUTTONUP and self.dragging:
            self.dragging = False

        # 4) Insertion de texte (IME, on-screen keyboard, etc.)
        elif event.type == pygame.TEXTINPUT and self.active:
            # supprimer la sélection avant insertion
            if self.has_selection():
                self._delete_selection()
            self.text = (self.text[:self.cursor_pos]
                        + event.text
                        + self.text[self.cursor_pos:])
            self.cursor_pos += len(event.text)
            self._clear_selection()
            self.on_change(self.text)
            self._ensure_cursor_visible()

        # 5) Toutes les touches quand le champ est actif
        elif event.type == pygame.KEYDOWN and self.active:
            mods = pygame.key.get_mods()

            # 5a) Collage (Ctrl+V) tout en haut
            if (mods & pygame.KMOD_CTRL) and event.key == pygame.K_v:
                s = pygame.scrap.get_text() or ""
                s = ''.join(ch for ch in s if ch.isprintable())
                if self.has_selection():
                    self._delete_selection()
                self.text = (self.text[:self.cursor_pos]
                            + s
                            + self.text[self.cursor_pos:])
                self.cursor_pos += len(s)
                self._clear_selection()
                self.on_change(self.text)
                self._ensure_cursor_visible()
                return
            
                        # --- Copie (Ctrl+C) ---
            if (mods & pygame.KMOD_CTRL) and event.key == pygame.K_c:
                if self.has_selection():
                    start = min(self.sel_start, self.sel_end)
                    end   = max(self.sel_start, self.sel_end)
                    to_copy = self.text[start:end]
                    pygame.scrap.put_text(to_copy)
                return
            
            if (mods & pygame.KMOD_CTRL) and event.key == pygame.K_a:
                # tout sélectionner
                self.sel_start = 0
                self.sel_end   = len(self.text)
                # placer le curseur à la fin
                self.cursor_pos = len(self.text)
                return
            
            # 5b) Shift + flèches -> modifier la sélection
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT) and (mods & pygame.KMOD_SHIFT):
                if event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                else:
                    self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                self.sel_end = self.cursor_pos
                return

            # 5c) Flèches seules -> déplacer curseur + annuler sélection
            if event.key == pygame.K_LEFT and not (mods & pygame.KMOD_SHIFT):
                self.cursor_pos = max(0, self.cursor_pos - 1)
                self._clear_selection()
                self._ensure_cursor_visible()
                return
            if event.key == pygame.K_RIGHT and not (mods & pygame.KMOD_SHIFT):
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                self._clear_selection()
                self._ensure_cursor_visible()
                return

            # 5d) Backspace / Delete -> suppression ou remplacement de la sélection
            if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                if self.has_selection():
                    self._delete_selection()
                else:
                    if event.key == pygame.K_BACKSPACE and self.cursor_pos > 0:
                        self.text = (self.text[:self.cursor_pos-1]
                                    + self.text[self.cursor_pos:])
                        self.cursor_pos -= 1
                    elif event.key == pygame.K_DELETE and self.cursor_pos < len(self.text):
                        self.text = (self.text[:self.cursor_pos]
                                    + self.text[self.cursor_pos+1:])
                self._clear_selection()
                self.on_change(self.text)
                self._ensure_cursor_visible()
                return

            # 5e) Entrée -> désactiver l’édition
            if event.key == pygame.K_RETURN:
                self.active = False
                return
            self.cursor_pos = max(0, min(self.cursor_pos, len(self.text)))
            self._ensure_cursor_visible()



    def draw(self, surf):
            # fond + bordure
            pygame.draw.rect(surf, self.bg_color, self.rect, border_radius=self.border_radius)
            pygame.draw.rect(surf, self.border_color, self.rect, width=1, border_radius=self.border_radius)

            # surface de masque pour le texte
            padding = 5
            avail_width = self.rect.w - 2 * padding
            mask_surf = pygame.Surface((avail_width, self.rect.h), pygame.SRCALPHA)
            mask_surf.fill((0, 0, 0, 0))  # transparent

            # texte à afficher (placeholder ou réel)
            if not self.text and self.placeholder and not self.active:
                display_text = self.placeholder
                color = self.placeholder_color
            else:
                display_text = self.text
                color = self.text_color
            txt_surf = self.font.render(display_text, True, color)

            # dessiner la sélection sur le mask_surf
            if self.sel_start != self.sel_end:
                start = min(self.sel_start, self.sel_end)
                end = max(self.sel_start, self.sel_end)
                x1 = self.font.size(self.text[:start])[0] - self.offset_x
                x2 = self.font.size(self.text[:end])[0] - self.offset_x
                sel_rect = pygame.Rect(x1, 2, x2 - x1, self.rect.h - 4)
                pygame.draw.rect(mask_surf, (100, 100, 150), sel_rect)

            # blit du texte décalé
            mask_surf.blit(txt_surf, (-self.offset_x, (self.rect.h - txt_surf.get_height()) // 2))

            # coller le mask dans le champ en tenant compte du padding
            surf.blit(mask_surf, (self.rect.x + padding, self.rect.y))

            # curseur clignotant
            if self.active:
                now = pygame.time.get_ticks()
                if now - self.last_blink_switch >= self.blink_interval:
                    self.cursor_visible = not self.cursor_visible
                    self.last_blink_switch = now
                if self.cursor_visible:
                    # position du curseur sur mask_surf
                    pre_txt = self.text[:self.cursor_pos]
                    cursor_px = self.font.size(pre_txt)[0] - self.offset_x
                    cursor_x = self.rect.x + padding + cursor_px
                    cursor_y = self.rect.y + (self.rect.h - txt_surf.get_height()) // 2
                    cursor_h = txt_surf.get_height()
                    pygame.draw.line(surf, self.text_color,
                                    (cursor_x, cursor_y),
                                    (cursor_x, cursor_y + cursor_h), 2)