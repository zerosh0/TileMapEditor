import time
import pygame
from editor.ui.Font import FontManager
from editor.ui.TextButton import Button

def lerp(a, b, t):
    return a + (b - a) * t

class MenuItem:
    def __init__(self, text, action, font, padding=10,
                 bg_color=(40, 40, 40), text_color=(230, 230, 230), hover_color=(60, 60, 60)):
        self.text = text
        self.action = action
        self.font = font
        self.padding = padding
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color

        self.text_surf = self.font.render(self.text, True, self.text_color)
        w, h = self.text_surf.get_size()
        self.rect = pygame.Rect(0, 0, w + 2*self.padding, h + 2*self.padding)
        self.is_hovered = False
    
    def set_position(self, x, y):
        self.rect.topleft = (x, y)

    def handle_event(self, event, offset_y=0):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.is_hovered = self.rect.move(0, -offset_y).collidepoint(mx, my)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered and event.button == 1:
            self.action()

    def draw(self, surface, offset_y=0):
        bg = self.hover_color if self.is_hovered else self.bg_color
        draw_rect = self.rect.move(0, -offset_y)
        pygame.draw.rect(surface, bg, draw_rect, border_radius=4)
        text_rect = self.text_surf.get_rect(midleft=(draw_rect.x + self.padding, draw_rect.centery))
        surface.blit(self.text_surf, text_rect)


class DropdownMenu:
    ANIM_DURATION = 0.1
    MAX_VISIBLE = 6
    SCROLLBAR_WIDTH = 8
    SCROLL_SPEED = 20

    def __init__(self, parent_button, items, item_font,
                 panel_color=(40, 40, 40), border_color=(80, 80, 80), border_width=2,
                 width_multiplier=1.5, keep_open_time=0.2):
        self.parent = parent_button
        self.panel_color = panel_color
        self.border_color = border_color
        self.border_width = border_width
        self.width_multiplier = width_multiplier
        self.keep_open_time = keep_open_time
        self.last_parent_hover = 0

        self.items = [MenuItem(text, action, item_font) for text, action in items]
        self.is_open = False
        self.open_time = None

        self.offset = 0
        self._layout_items()

    def _layout_items(self):
        parent_w = int(self.parent.rect.width * self.width_multiplier)
        for item in self.items:
            item.rect.width = parent_w
        self.item_height = self.items[0].rect.height if self.items else 0

        x = self.parent.rect.x
        y = self.parent.rect.bottom
        for item in self.items:
            item.set_position(x, y)
            y += self.item_height

        self.full_height = len(self.items) * self.item_height
        self.visible_height = min(self.full_height, self.MAX_VISIBLE * self.item_height)

        base_w = parent_w + 2*self.border_width
        if self.full_height > self.visible_height:
            total_w = base_w + self.SCROLLBAR_WIDTH
        else:
            total_w = base_w

        self.panel_rect = pygame.Rect(
            x - self.border_width,
            self.parent.rect.bottom - self.border_width,
            total_w,
            self.visible_height + 2*self.border_width
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            over_parent = self.parent.rect.collidepoint(event.pos)
            over_panel = self.panel_rect.collidepoint(event.pos)
            now = time.time()
            if over_parent:
                self.last_parent_hover = now
            new_open = (
                (over_panel and self.is_open) or
                over_parent or
                (over_panel and now - self.last_parent_hover <= self.keep_open_time)
            )
            if new_open and not self.is_open:
                self.is_open = True
                self.open_time = now
            elif not new_open and self.is_open:
                self.is_open = False
                self.open_time = None

        if self.is_open and event.type == pygame.MOUSEWHEEL and self.full_height > self.visible_height:
            self.offset = max(0, min(self.offset - event.y * self.SCROLL_SPEED,
                                     self.full_height - self.visible_height))

        if self.is_open and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for it in self.items:
                top = it.rect.y - self.offset
                bottom = top + self.item_height
                panel_top = self.parent.rect.bottom
                panel_bottom = panel_top + self.visible_height
                if bottom > panel_top and top < panel_bottom:
                    it.handle_event(event, offset_y=self.offset)

    def draw(self, surface):
        if not self.is_open:
            return

        elapsed = time.time() - (self.open_time or 0)
        t = min(elapsed / self.ANIM_DURATION, 1)
        anim_h = int(lerp(0, self.visible_height, t))

        anim_rect = pygame.Rect(
            self.panel_rect.x,
            self.panel_rect.y,
            self.panel_rect.width,
            anim_h + 2*self.border_width
        )

        shadow = pygame.Surface((anim_rect.width+4, anim_rect.height+4), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=6)
        surface.blit(shadow, (anim_rect.x-2, anim_rect.y-2))

        pygame.draw.rect(surface, self.panel_color, anim_rect, border_radius=6)
        pygame.draw.rect(surface, self.border_color, anim_rect, width=self.border_width, border_radius=6)

        clip = surface.get_clip()
        inner = pygame.Rect(
            anim_rect.x + self.border_width,
            anim_rect.y + self.border_width,
            anim_rect.width - 2*self.border_width - (self.SCROLLBAR_WIDTH if self.full_height > self.visible_height else 0),
            anim_h
        )
        surface.set_clip(inner)

        for it in self.items:
            y0 = it.rect.y - self.offset
            if (y0 + self.item_height > self.parent.rect.bottom and
                y0 < self.parent.rect.bottom + anim_h):
                it.draw(surface, offset_y=self.offset)

        surface.set_clip(clip)

        if self.full_height > self.visible_height:
            track = pygame.Rect(
                inner.right,
                inner.y,
                self.SCROLLBAR_WIDTH,
                inner.height
            )
            thumb_h = max(int(inner.height * inner.height / self.full_height), 20)
            thumb_y = inner.y + int((self.offset / (self.full_height - self.visible_height)) * (inner.height - thumb_h))
            thumb = pygame.Rect(track.x + 2, thumb_y, self.SCROLLBAR_WIDTH - 4, thumb_h)
            pygame.draw.rect(surface, (70, 70, 70), track, border_radius=4)
            pygame.draw.rect(surface, (140, 140, 140), thumb, border_radius=4)


class MenuButton(Button):
    def __init__(self, rect, text, submenu_items, action=None, font=None,
                 bg_color=(70, 70, 70), text_color=(230, 230, 230), hover_color=(90, 90, 90),
                 item_font_size=18, border_radius=-1):
        super().__init__(rect, text, action or (lambda: None), font,
                         bg_color, text_color, hover_color, border_radius=border_radius)
        font_manager = FontManager()
        item_font = font_manager.get(size=item_font_size)
        item_font.set_bold(False)
        self.dropdown = DropdownMenu(self, submenu_items, item_font)

    def handle_event(self, event):
        super().handle_event(event)
        self.dropdown.handle_event(event)

    def draw(self, surface):
        super().draw(surface)
        self.dropdown.draw(surface)
