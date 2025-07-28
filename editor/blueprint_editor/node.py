from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type
import pygame
from pygame.locals import *

from editor.ui.Font import FontManager
if TYPE_CHECKING:
    from system import BlueprintEditor


# --- Logic Layer ---
class Pin:
    RADIUS = 4

    def __init__(self, node: 'Node', name: str, pin_type: str = 'exec', is_output: bool = True, label: str = '', offset_y: int = 0):
        self.node = node
        self.name = name
        self.pin_type = pin_type  # 'exec' or 'data'
        self.is_output = is_output
        self.connection: Optional['Pin'] = None
        self.label = label  # static label shown next to pin
        self.offset_y=offset_y

    def connect(self, other: 'Pin'):
        if self.is_output == other.is_output or self.pin_type != other.pin_type:
            return
        if self.node == other.node:
            return
        out_pin, in_pin = (self, other) if self.is_output else (other, self)
        out_pin.connection = in_pin
        in_pin.connection = out_pin

    def disconnect(self):
        if self.connection:
            peer = self.connection
            self.connection = None
            peer.connection = None

    @property
    def pos(self) -> Tuple[int,int]:
        return self.node.get_pin_pos(self)

NODE_REGISTRY: Dict[str, Tuple[Type['Node'], str]] = {}
CATEGORY_ORDER: List[str] = []
CATEGORY_COLORS = {
    "Events"   : (180,100,100),
    "Logic"    : (100,180,100),
    "Debug"    : (100,100,180),
}


def register_node(name: Optional[str]=None, category: str="General"):
    """Décorateur qui enregistre une Node dans le registry, avec sa catégorie."""
    def _decorator(cls):
        key = name or cls.__name__
        NODE_REGISTRY[key] = (cls, category)
        if category not in CATEGORY_ORDER:
            CATEGORY_ORDER.append(category)
        return cls
    return _decorator

class Node:
    WIDTH = 160
    HEIGHT = 100
    HEADER_HEIGHT = 24

    def __init__(self, pos: Tuple[int,int], title: str, editor: 'BlueprintEditor', properties : Dict[str, Any] = {}, is_event: bool=False):
        self.x, self.y = pos
        self.title = title
        self.editor = editor
        self.is_event = is_event
        self.inputs: List[Pin] = []
        self.outputs: List[Pin] = []
        self.properties: Dict[str, Any] = properties
        self.ui_elements = []
        self.dragging = False
        self.drag_offset = (0,0)
        self.height=self.HEIGHT
        self.create_pins()

    def create_pins(self):
        # execution flow pins
        if not self.is_event:
            self.inputs.append(Pin(self, 'in', 'exec', False, 'Exec flow in'))
        self.outputs.append(Pin(self, 'out', 'exec', True, 'Exec flow out'))

    def add_data_pin(self, name: str, is_output: bool = False, default: Any = None, label: str = '', offset_y = 0):
        pin = Pin(self, name, 'data', is_output, label,offset_y=offset_y)
        if is_output:
            self.outputs.append(pin)
        else:
            self.inputs.append(pin)
        if name not in self.properties:
            self.properties[name] = default
        return pin

    def get_pin_pos(self, pin: Pin) -> Tuple[int,int]:
        ox, oy = self.editor.offset
        lst = self.outputs if pin.is_output else self.inputs
        idx = lst.index(pin)
        x = self.x - ox + (self.WIDTH if pin.is_output else 0)
        y = self.y - oy + self.HEADER_HEIGHT + 10 + idx * 25 + pin.offset_y
        return int(x), int(y)

    def handle_event(self, e: pygame.event.Event):
        mx, my = pygame.mouse.get_pos()
        ox, oy = self.editor.offset
        hdr = pygame.Rect(self.x - ox, self.y - oy, self.WIDTH, self.HEADER_HEIGHT)
        if e.type == MOUSEBUTTONDOWN and e.button == 1 and hdr.collidepoint(mx, my):
            self.dragging = True
            self.drag_offset = (mx - (self.x - ox), my - (self.y - oy))
        elif e.type == MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == MOUSEMOTION and self.dragging:
            self.x = mx - self.drag_offset[0] + ox
            self.y = my - self.drag_offset[1] + oy
            # update UI positions
            for el in self.ui_elements:
                if hasattr(el, 'update_position'):
                    el.update_position(self.x, self.y)

        for el in self.ui_elements:
            el.handle_event(e)

    def draw(self, surf: pygame.Surface, selected: bool = False, draw_ui: bool = True,draw_label: bool = True):
        ox, oy = self.editor.offset
        x, y, w, h = self.x - ox, self.y - oy, self.WIDTH, self.height
        rect = pygame.Rect(x, y, w, h)
        # background and border
        pygame.draw.rect(surf, (30, 30, 30), rect, border_radius=4)
        selected_color = (100, 100, 200) if not self.is_event else (200, 100, 100)
        border_color =  selected_color if selected else (70, 70, 70)
        pygame.draw.rect(surf, border_color, rect, 2, border_radius=4)
        # header
        hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
        hdr_color = (200,100,100) if self.is_event else (100,100,200)
        pygame.draw.rect(surf, hdr_color, hdr, border_top_left_radius=4, border_top_right_radius=4)
        if getattr(self, 'has_error', False):
            badge_w, badge_h = 52, 16
            badge = pygame.Surface((badge_w, badge_h), flags=pygame.SRCALPHA)
            badge.fill((220, 60, 60, 200))
            try:
                pygame.draw.aacircle(badge, (255,255,255), (8, badge_h//2), 5)
            except AttributeError:
                pygame.draw.circle(badge, (255,255,255), (8, badge_h//2), 5)
            font = FontManager().get(size=14)
            ex = font.render("!", True, (220,60,60))
            badge.blit(ex, (7, badge_h//2 - ex.get_height()//2+1))
            txt = font.render("ERROR", True, (255,255,255))
            badge.blit(txt, (16, badge_h//2 - txt.get_height()//2))
            surf.blit(badge, (x + w - badge_w - 8, y + 4))
        font = FontManager().get(size=18)
        surf.blit(font.render(self.title, True, (20,20,20)), (x + 6, y + 4))
        if draw_ui:
            for el in self.ui_elements:
                el.draw(surf)
        for pin in self.inputs + self.outputs:
            col = (230, 230, 230) if pin.pin_type == 'exec' else (100, 100, 200)
            try:
                pygame.draw.aacircle(surf, col, pin.pos, Pin.RADIUS)
            except AttributeError:
                pygame.draw.circle(surf, col, pin.pos, Pin.RADIUS)
            if (pin.pin_type!= 'exec' and pin.label or pin.label in ("True", "False","Next","Loop","A","B")) and draw_label:
                lbl = font.render(pin.label, True, (200, 200, 200))
                label_x = pin.pos[0] + 10 if not pin.is_output else pin.pos[0] + (Pin.RADIUS + 2) - lbl.get_width() - 20
                label_y = pin.pos[1] - 6
                surf.blit(lbl, (label_x, label_y))

    def execute(self, context: Dict[str, Any]) -> Optional['Node']:
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

class DropdownButton:
    def __init__(self, node: Node, rel_rect: pygame.Rect, options: List[str], callback: Callable[[str], None]):
        self.node = node
        self.editor = node.editor
        self.base_rect = rel_rect.copy()
        self.rect = rel_rect.copy()
        self.options = options
        self.callback = callback
        self.selected = options[0] if options else ""
        self.is_open = False

        # Scroll
        self.max_visible = 5
        self.scroll_offset = 0

        self.items: List[pygame.Rect] = []
        self._calc_items()
        # position initiale
        self.update_position(node.x, node.y)


    def update_position(self, node_x: int, node_y: int):
        ox, oy = self.editor.offset
        # repositionne le bouton
        self.rect.topleft = (
            node_x - ox + self.base_rect.x + 10,
            node_y - oy + self.base_rect.y
        )
        # recalcule les items
        self._calc_items()

    def handle_event(self, e: pygame.event.Event) -> bool:
        mx, my = pygame.mouse.get_pos()

        # 1) Scroll
        if self.is_open and e.type == pygame.MOUSEWHEEL:
            items_top = self.rect.y + self.rect.h
            items_bot = items_top + self.max_visible * self.rect.h
            if items_top <= my <= items_bot and len(self.options) > self.max_visible:
                self.scroll_offset = max(
                    0,
                    min(
                        self.scroll_offset - e.y,
                        len(self.options) - self.max_visible
                    )
                )
                return True

        # 2) Clic gauche
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            # sur le bouton : toggle
            if self.rect.collidepoint(mx, my):
                self.is_open = not self.is_open
                # reset scroll quand on rouvre
                if self.is_open:
                    self.scroll_offset = 0
                return True

            # si ouvert, clic sur un item visible
            if self.is_open:
                x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h
                # on parcourt uniquement les max_visible lignes
                for line in range(1, min(self.max_visible, len(self.options) - self.scroll_offset) + 1):
                    idx = self.scroll_offset + (line - 1)
                    item_rect = pygame.Rect(x, y + line * h, w, h)
                    if item_rect.collidepoint(mx, my):
                        # sélection
                        self.selected = self.options[idx]
                        self.callback(self.selected)
                        self.is_open = False
                        self.scroll_offset = 0
                        return True

                # tout autre clic ferme
                self.is_open = False
                self.scroll_offset = 0
                return True

        return False

    def _calc_items(self):
        """Stocke juste la taille standard (w,h)."""
        self.item_size = (self.rect.w, self.rect.h)

    def draw(self, surf: pygame.Surface):
        font = FontManager().get(size=16)
        x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h

        # 1) Bouton principal
        # fond semi-transparent
        btn_bg = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        btn_bg.fill((40, 40, 40, 180))
        surf.blit(btn_bg, (x, y))
        # bordure arrondie
        pygame.draw.rect(surf, (80, 80, 80), (x, y, w, h), 2, border_radius=8)
        # label centré
        text_surf = font.render(self.selected, True, (240, 240, 240))
        surf.blit(text_surf, (x + 10, y + (h - text_surf.get_height()) // 2))
        # flèche vers le bas
        arrow = [(x + w - 16, y + h//2 - 3),
                 (x + w - 8, y + h//2 - 3),
                 (x + w - 12, y + h//2 + 3)]
        pygame.draw.polygon(surf, (200,200,200), arrow)

        # 2) Liste déroulante
        if self.is_open:
            total_h = len(self.options) * h
            list_h = min(total_h, self.max_visible * h)
            # zone de fond
            panel = pygame.Surface((w, list_h), flags=pygame.SRCALPHA)
            panel.fill((30, 30, 30, 200))
            surf.blit(panel, (x, y + h))
            # bordure arrondie (seulement derrière les items visibles)
            pygame.draw.rect(surf, (80, 80, 80), (x, y + h, w, list_h), 2, border_radius=8)



            # items
            mx, my = pygame.mouse.get_pos()
            start = self.scroll_offset
            end = min(start + self.max_visible, len(self.options))
            for display_idx, opt_idx in enumerate(range(start, end), start=1):
                opt = self.options[opt_idx]
                item_y = y + display_idx * h
                item_rect = pygame.Rect(x, item_y, w, h)

                # highlight au survol
                if item_rect.collidepoint(mx, my):
                    hl = pygame.Surface((w, h), flags=pygame.SRCALPHA)
                    hl.fill((80, 80, 120, 100))
                    surf.blit(hl, (x, item_y))

                # texte
                txt_s = font.render(opt, True, (230, 230, 230))
                surf.blit(txt_s, (x + 10, item_y + (h - txt_s.get_height()) // 2))

            # scrollbar
            if len(self.options) > self.max_visible:
                sb_w = 6
                sb_x = x + w - sb_w - 4
                sb_y = y + h + 4
                sb_h = list_h - 8
                # track
                pygame.draw.rect(surf, (50,50,50), (sb_x, sb_y, sb_w, sb_h), border_radius=3)
                # thumb
                thumb_h = max(20, sb_h * self.max_visible // len(self.options))
                thumb_y = sb_y + (sb_h - thumb_h) * (self.scroll_offset / (len(self.options) - self.max_visible))
                pygame.draw.rect(surf, (120,120,120), (sb_x, thumb_y, sb_w, thumb_h), border_radius=3)