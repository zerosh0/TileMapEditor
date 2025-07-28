import pygame
import math
from typing import List, Dict, Tuple, Union
from editor.core.utils import AnimatedTile

class Timeline:
    def __init__(self, on_click, start=0.0, end=10.0, scroll_h=8, rect=None):
        # bornes temporelles
        self.start, self.end = start, end
        self.duration = max(0.001, end - start)

        # échelle initiale (px / s)
        self.scale = 50 if end >= 10 else 710 / end
        self.min_scale = 10
        self.max_scale = 500 if end >= 500 else self.scale * 2

        # état principal
        self.current = start
        self.playing = False
        self.loop = False
        self.record = False
        self.keyframes: List[AnimatedTile] = []
        self.active = True

        # sélection par instance (liste)
        self.selected: List[AnimatedTile] = []

        # drag & drop keyframe
        self.dragging_kf: AnimatedTile = None
        self.dragging_kf_offset: float = 0.0
        self.drag_original_times: List[Tuple[AnimatedTile, float]] = []
        self.dragging_selected = False

        # géométrie
        screen = pygame.display.get_surface()
        sw, sh = screen.get_size()
        height = 120
        self.rect = rect or pygame.Rect(0, sh - height, sw - 250, height)
        self.header_h = 17
        self.edge_pad = 20

        # scrollbar
        self.scroll_h = scroll_h
        self.scroll_visible = True
        self.current_scroll_h = scroll_h
        self.dragging_thumb = False
        self.offset = 0.0
        self._update_scroll_visibility()

        self.on_click = on_click

        # bouton "close"
        cr, cm = 8, 6
        self.close_center = (
            self.rect.right - cr - cm,
            self.rect.y + cr + cm - 5
        )

        # police, boutons UI
        self.font = pygame.font.Font(None, 16)
        self.dragging_cursor = False
        self.images = {}
        for name in ("record", "playing", "loop"):
            self.images[name] = {
                False: pygame.image.load(f"./Assets/ui/icones/{name}_off.png").convert_alpha(),
                True:  pygame.image.load(f"./Assets/ui/icones/{name}_on.png").convert_alpha()
            }
        btn_w, btn_h = self.images["playing"][False].get_size()
        gap = 16
        total_w = 3 * btn_w + 2 * gap
        start_x = self.rect.x + (self.rect.w - total_w) // 2
        by = self.rect.y + (self.header_h - btn_h) // 2
        self.btn_record = pygame.Rect(start_x, by, btn_w, btn_h)
        self.btn_play   = pygame.Rect(start_x + (btn_w + gap), by, btn_w, btn_h)
        self.btn_loop   = pygame.Rect(start_x + 2 * (btn_w + gap), by, btn_w, btn_h)

        # sélection multiple par glissé (clic droit)
        self.dragging_selection = False
        self.sel_start = (0, 0)
        self.sel_rect = pygame.Rect(0, 0, 0, 0)


    def add_keyframe(self, tile: AnimatedTile):
        self.keyframes = [
            kf for kf in self.keyframes
            if not (
                kf.anim_id == tile.anim_id and
                abs(kf.time - tile.time) < 1e-6 and
                kf.tile.x == tile.tile.x and
                kf.tile.y == tile.tile.y and
                kf.layer  == tile.layer
            )
        ]
        self.keyframes.append(tile)

    def get_keyframes_at_time(self, time: float = None) -> List[AnimatedTile]:
        t = self.current if time is None else time
        return [kf for kf in self.keyframes if abs(kf.time - t) < 1e-6]

    def get_animation_states(self, time: float = None
        ) -> Dict[Union[str,int], Dict[Tuple[int,int,int], AnimatedTile]]:
        t = self.current if time is None else time
        states: Dict[Union[str,int], Dict[Tuple[int,int,int], AnimatedTile]] = {}
        for kf in sorted(self.keyframes, key=lambda k: k.time):
            if kf.time <= t:
                pos = (kf.tile.x, kf.tile.y, kf.layer)
                if kf.tile.TileMap == "":
                    if kf.anim_id in states:
                        states[kf.anim_id].pop(pos, None)
                else:
                    states.setdefault(kf.anim_id, {})[pos] = kf
        return states


    def get_selected_keyframes(self) -> List[AnimatedTile]:
        return list(self.selected)


    def compute_scale(self):
        self.duration = max(0.001, self.end - self.start)
        self.scale = 50 if self.end >= 10 else 710 / self.end
        self.min_scale = 10
        self.max_scale = 500 if self.end >= 500 else self.scale * 2
        self.update_rect()
        self._update_scroll_visibility()

    


    def update_rect(self):
        screen = pygame.display.get_surface()
        sw, sh = screen.get_size()
        height = 120
        self.rect = pygame.Rect(0, sh - height, sw - 250, height)
        cr, cm = 8, 6
        self.close_center = (
            self.rect.right - cr - cm,
            self.rect.y + cr + cm - 5
        )
        btn_w, btn_h = self.images["playing"][False].get_size()
        gap = 16
        total_w = 3 * btn_w + 2 * gap
        start_x = self.rect.x + (self.rect.w - total_w) // 2
        by = self.rect.y + (self.header_h - btn_h) // 2
        self.btn_record = pygame.Rect(start_x, by, btn_w, btn_h)
        self.btn_play   = pygame.Rect(start_x + (btn_w + gap), by, btn_w, btn_h)
        self.btn_loop   = pygame.Rect(start_x + 2 * (btn_w + gap), by, btn_w, btn_h)


    def on_close(self):
        self.active = False

    def _update_scroll_thumb(self):
        view_sec = (self.rect.w - 2*self.edge_pad) / self.scale
        frac = min(1.0, view_sec / self.duration)
        w = max(20, int(self.scroll_area.w * frac))
        max_rel = self.scroll_area.w - w
        rel = (self.offset / (self.duration - view_sec)) if self.duration > view_sec else 0
        x = int(self.scroll_area.x + rel * max_rel)
        self.scroll_thumb = pygame.Rect(x, self.scroll_area.y, w, self.scroll_area.h)

    def _update_scroll_visibility(self):
        view_sec = (self.rect.w - 2*self.edge_pad) / self.scale
        self.scroll_visible = (self.duration > view_sec)
        self.current_scroll_h = self.scroll_h if self.scroll_visible else 0
        self.scroll_area = pygame.Rect(
            self.rect.x, self.rect.bottom - self.current_scroll_h,
            self.rect.w, self.current_scroll_h
        )
        max_off = max(0.0, self.duration - view_sec)
        self.offset = max(0.0, min(self.offset, max_off))
        self._update_scroll_thumb()

    def _clamp_offset(self):
        view_sec = (self.rect.w - 2*self.edge_pad) / self.scale
        max_off = max(0.0, self.duration - view_sec)
        self.offset = max(0.0, min(self.offset, max_off))

    def time_to_x(self, t: float) -> int:
        return self.rect.x + self.edge_pad + int((t - self.offset)*self.scale)

    def x_to_time(self, x: int) -> float:
        return self.offset + (x - (self.rect.x + self.edge_pad)) / self.scale

    def ensure_current_visible(self):
        view_sec = (self.rect.w - 2*self.edge_pad) / self.scale
        if self.current < self.offset:
            self.offset = self.current
        elif self.current > self.offset + view_sec:
            self.offset = self.current - view_sec
        self._clamp_offset()
        self._update_scroll_visibility()

    def mouse_on(self):
        mx, my = pygame.mouse.get_pos()
        area = pygame.Rect(
            0,
            self.rect.y,
            self.rect.w,
            self.rect.h
        )
        return area.collidepoint(mx,my) and self.active

    def update(self, dt: float):
        if self.playing:
            self.current += dt
            if self.current > self.end:
                if self.loop:
                    self.current = self.start
                else:
                    self.current, self.playing = self.end, False
            self.ensure_current_visible()



    def _compute_kf_positions(self, area: pygame.Rect
        ) -> Tuple[List[Tuple[AnimatedTile,int,int]], List[Tuple[float,int]]]:
        """
        Renvoie deux listes :
          - positions = [(kf, x_screen, y_screen), ...] pour au plus 5 keyframes par temps
          - overflows = [(time, extra_count), ...] pour chaque groupe >5
        """
        groups: Dict[float, List[AnimatedTile]] = {}
        eps = 1e-2
        for kf in self.keyframes:
            placed = False
            for t0, lst in groups.items():
                if abs(kf.time - t0) < eps:
                    lst.append(kf)
                    placed = True
                    break
            if not placed:
                groups[kf.time] = [kf]

        positions: List[Tuple[AnimatedTile,int,int]] = []
        overflows: List[Tuple[float,int]] = []
        stack_h = 14
        max_stack = 5
        col_w = 14

        for t0, lst in groups.items():
            n = len(lst)
            visible = sorted(lst, key=lambda k: id(k))[:max_stack]
            rows = min(n, max_stack)
            total_h = (rows - 1) * stack_h
            for idx, kf in enumerate(visible):
                row = idx
                x0 = self.time_to_x(kf.time)
                xk = x0
                yk = area.centery - total_h/2 + row*stack_h
                positions.append((kf, int(xk), int(yk)))
            if n > max_stack:
                overflows.append((t0, n - max_stack))
        return positions, overflows


    def handle_event(self, event):
        if not self.active:
            return
        mx, my = pygame.mouse.get_pos()

        timeline_area = pygame.Rect(
            self.rect.x + self.edge_pad,
            self.rect.y + self.header_h + 2,
            self.rect.w - 2*self.edge_pad,
            self.rect.h - self.header_h - self.current_scroll_h - 12
        )
        tick_y1 = self.rect.y + self.header_h + 12
        area = pygame.Rect(
            self.rect.x + self.edge_pad,
            tick_y1 + 5,
            self.rect.w - 2*self.edge_pad,
            self.rect.h - self.header_h - (tick_y1 - self.rect.y) - self.current_scroll_h + 8
        )

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            positions, _ = self._compute_kf_positions(area)
            for kf, xk, yk in positions:
                if math.hypot(mx-xk, my-yk) <= 7:
                    if kf in self.selected:
                        self.selected.remove(kf)
                    else:
                        self.selected.append(kf)
                    return
            if timeline_area.collidepoint(mx, my):
                self.on_click()
                self.dragging_selection = True
                self.sel_start = (mx, my)
                self.sel_rect = pygame.Rect(mx, my, 0, 0)
                return

        if event.type == pygame.MOUSEMOTION and self.dragging_selection:
            x0, y0 = self.sel_start
            self.sel_rect.x = min(x0, mx); self.sel_rect.y = min(y0, my)
            self.sel_rect.width = abs(mx - x0); self.sel_rect.height = abs(my - y0)
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 3 and self.dragging_selection:
            self.dragging_selection = False
            positions, _ = self._compute_kf_positions(area)
            new_sel = []
            for kf, xk, yk in positions:
                if self.sel_rect.collidepoint(xk, yk):
                    self.on_click()
                    new_sel.append(kf)
            self.selected = new_sel
            return

        if event.type == pygame.MOUSEWHEEL and timeline_area.collidepoint(mx, my):
            t_mouse = self.x_to_time(mx)
            factor = 1.1 ** event.y
            self.scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
            self.offset = t_mouse - (mx - (self.rect.x + self.edge_pad)) / self.scale
            self.ensure_current_visible()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            close_rect = pygame.Rect(0,0,16,4); close_rect.center = self.close_center
            if close_rect.collidepoint(mx, my):
                self.on_close(); return

            for attr, btn in (("record", self.btn_record),
                              ("playing", self.btn_play),
                              ("loop",    self.btn_loop)):
                if btn.collidepoint(mx, my):
                    if attr == "playing":
                        new = not self.playing
                        if new and self.current >= self.end:
                            self.current = self.start
                        self.playing = new
                    else:
                        setattr(self, attr, not getattr(self, attr))
                    return

            # Shift + clic sur keyframe -> drag & drop
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                positions, _ = self._compute_kf_positions(area)
                for kf, xk, yk in positions:
                    if math.hypot(mx-xk, my-yk) <= 7:
                        if kf in self.selected:
                            self.dragging_selected = True
                            self.drag_start_mouse_time = self.x_to_time(mx)
                            self.drag_original_times = [
                                (sel_kf, sel_kf.time)
                                for sel_kf in self.selected
                            ]
                        else:
                            self.dragging_kf = kf
                            self.dragging_kf_offset = self.x_to_time(mx) - kf.time
                        return

            # scroll thumb
            if self.scroll_visible and self.scroll_thumb.collidepoint(mx, my):
                self.dragging_thumb = True; return

            if timeline_area.collidepoint(mx, my):
                t = self.x_to_time(mx)
                vs, ve = self.offset, self.offset + (self.rect.w - 2*self.edge_pad) / self.scale
                self.current = max(vs, min(ve, t))
                self.dragging_cursor = True
                self.on_click()
                return

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging_thumb = False
            self.dragging_cursor = False
            self.dragging_kf = None
            self.dragging_selected = False
            self.drag_original_times = []

        if event.type == pygame.MOUSEMOTION:
            if self.dragging_thumb:
                rel_x = mx - self.scroll_area.x - self.scroll_thumb.w/2
                max_rel = self.scroll_area.w - self.scroll_thumb.w
                rel_x = max(0, min(rel_x, max_rel))
                frac = rel_x / max_rel if max_rel>0 else 0
                view_sec = (self.rect.w - 2*self.edge_pad) / self.scale
                self.offset = frac * max(0, self.duration - view_sec)
                self._update_scroll_thumb()

            elif self.dragging_cursor:
                t = self.x_to_time(mx)
                vs, ve = self.offset, self.offset + (self.rect.w - 2*self.edge_pad)/self.scale
                self.current = max(vs, min(ve, t))

            elif self.dragging_kf:
                new_t = self.x_to_time(mx) - self.dragging_kf_offset
                self.dragging_kf.time = max(self.start, min(self.end, new_t))

            elif self.dragging_selected:
                new_mouse_time = self.x_to_time(mx)
                delta = new_mouse_time - self.drag_start_mouse_time
                for kf, t0 in self.drag_original_times:
                    kf.time = max(self.start, min(self.end, t0 + delta))
                self.ensure_current_visible()


        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self.playing and self.current >= self.end:
                    self.current = self.start
                self.playing = not self.playing
                return
            delta = 1.0 / self.scale
            if not self.playing:
                if event.unicode == '+' or event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.current = min(self.end, self.current + delta)
                    self.ensure_current_visible(); return
                if event.unicode == '-' or event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.current = max(self.start, self.current - delta)
                    self.ensure_current_visible(); return
            if event.key == pygame.K_DELETE:
                self.keyframes = [kf for kf in self.keyframes if kf not in self.selected]
                self.selected.clear(); return


    def draw(self, surf):
        if not self.active:
            return
        BG, HEADER_BG = (30,30,30), (60,60,60)
        DARK, GRAY, BLUE, RED = (33,33,33), (100,100,100), (66,109,174), (200,50,50)
        REMOVE = (90, 160, 170)	

        pygame.draw.rect(surf, BG, self.rect)
        pygame.draw.rect(surf, HEADER_BG,
                         (self.rect.x, self.rect.y, self.rect.w, self.header_h),
                         border_top_left_radius=2, border_top_right_radius=2)
        close_rect = pygame.Rect(0,0,16,4); close_rect.center = self.close_center
        pygame.draw.rect(surf, GRAY, close_rect, border_radius=2)

        for attr, btn in (("record", self.btn_record),
                          ("playing", self.btn_play),
                          ("loop",    self.btn_loop)):
            img = self.images[attr][getattr(self, attr)]
            surf.blit(img, btn.topleft)

        # graduations
        grad_y  = self.rect.y + self.header_h + 2
        tick_y1 = grad_y + 10
        possible = [0.1,0.2,0.5,1,2,5,10,20,30,60,120,300]
        target_px = 50
        for s in possible:
            if s*self.scale >= target_px:
                step = s; break
        else:
            step = possible[-1]
        view_sec = (self.rect.w-2*self.edge_pad)/self.scale
        t0 = math.floor(self.offset/step)*step
        t = t0
        while t <= self.offset + view_sec:
            x = self.time_to_x(t)
            if self.rect.x+self.edge_pad <= x <= self.rect.right-self.edge_pad:
                if step<1 or abs(t-round(t))<1e-6:
                    label = f"{t:.{1 if step<1 else 0}f}s"
                    txt = self.font.render(label, True, GRAY)
                    surf.blit(txt, (x-txt.get_width()//2, tick_y1-7))
            t += step

        area = pygame.Rect(
            self.rect.x+self.edge_pad,
            tick_y1+5,
            self.rect.w-2*self.edge_pad,
            self.rect.h-self.header_h-(tick_y1-self.rect.y)-self.current_scroll_h+8
        )
        # alternance blocs
        half = step/2.0; first_n = math.floor((self.offset-self.start)/half)
        if first_n<0: first_n=0
        t = self.start + first_n*half; n=first_n; end_time=self.offset+view_sec
        while t<=end_time:
            t0, t1 = t, t+half
            x0 = max(area.x, self.time_to_x(t0))
            x1 = min(area.right, self.time_to_x(t1))
            if x1>x0:
                color = DARK if (x1<=self.time_to_x(self.start) or x0>=self.time_to_x(self.end)) else (48,48,48)
                pad = 1 if (n%2==0) else 2
                surf.fill(color, (x0, area.y, x1-x0-pad, area.h))
            n+=1; t+=half

        # keyframes
        positions, overflows = self._compute_kf_positions(area)
        for kf, xk, yk in positions:
            if xk < area.x or xk > area.right:
                continue
            color=REMOVE if kf.tile.TileMap=="" else BLUE
            color = RED if kf in self.selected else color
            try:
                pygame.draw.aacircle(surf, color, (xk, yk), 5)
            except:
                pygame.draw.circle(surf, color, (xk, yk), 5)
        for t0, extra in overflows:
            x0 = self.time_to_x(t0)
            if x0 < area.x or x0 > area.right:
                continue
            stack_h = 14; rows = 5; total_h = (rows-1)*stack_h
            y_top = area.centery - total_h/2
            text = f"+{extra}"
            txt_surf = self.font.render(text, True, (255,255,255))
            surf.blit(txt_surf, (x0 - txt_surf.get_width()//2, y_top - txt_surf.get_height() - 2))

        # curseur actuel
        if self.offset <= self.current <= self.offset+view_sec:
            cx = self.time_to_x(self.current)
            pygame.draw.line(surf, BLUE, (cx, area.y), (cx, area.y+area.h), 2)
            time_label = f"{self.current:.2f}s"
            txt_surf = self.font.render(time_label, True, (255,255,255))
            pad_x, pad_y = 4,2
            w,h = txt_surf.get_size()
            tooltip = pygame.Rect(0,0,w+2*pad_x,h+2*pad_y)
            tooltip.centerx = cx; tooltip.bottom = tick_y1+5
            pygame.draw.rect(surf, BLUE, tooltip, border_radius=2)
            surf.blit(txt_surf, (tooltip.x+pad_x, tooltip.y+pad_y))

        # sélection glissée visuelle
        if self.dragging_selection and self.sel_rect.width>0 and self.sel_rect.height>0:
            pygame.draw.rect(surf, (100,100,200), self.sel_rect, 1)

        # scrollbar
        if self.scroll_visible:
            pygame.draw.rect(surf, HEADER_BG, self.scroll_area)
            pygame.draw.rect(surf, GRAY, self.scroll_thumb, border_radius=3)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800,600), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    tl = Timeline(start=0, end=4)
    tile = AnimatedTile(
        anim_id="hero",
        time=1.5,
        TileMap="hero_tiles.png",
        x=2, y=3,
        Originalx=0, Originaly=0,
        rotation=0,
        flipHorizontal=False,
        flipVertical=False,
        layer=1
    )
    running = True
    while running:
        dt = clock.tick()/1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN and e.key==pygame.K_i and tl.active:
                tile.time = max(tl.start, min(tl.end, tl.current))
                tl.add_keyframe(tile)
            tl.handle_event(e)
        tl.update(dt)
        screen.fill((20,20,20))
        tl.draw(screen)
        pygame.display.flip()
    pygame.quit()
