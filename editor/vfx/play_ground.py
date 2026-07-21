import pygame
import random
import math
import time
from editor.vfx.vfx import ParticleEmitter, Particle
from editor.ui.ColorPicker import ColorPicker
from editor.ui.DropDownMenu import MenuButton


BG_COLOR = (14, 14, 22)
PANEL_COLOR = (22, 22, 32)
PANEL_BORDER_COLOR = (42, 44, 58)
TEXT_COLOR = (210, 215, 230)
TEXT_MUTED = (130, 135, 150)
ACCENT_BLUE = (0, 175, 240)
ACCENT_GREEN = (40, 200, 110)
ACCENT_RED = (230, 70, 70)
ACCENT_GOLD = (245, 185, 45)
BUTTON_COLOR = (32, 34, 48)
BUTTON_HOVER = (45, 48, 68)


class PreviewObstacle:
    def __init__(self, rect):
        self.rect = rect
        self.type = "collision"


class Slider:
    def __init__(self, x, y, w, label, min_v, max_v, cur_v, is_int=False):
        self.rect = pygame.Rect(x, y, w, 8)
        self.label = label
        self.min_v = min_v
        self.max_v = max_v
        self.val = cur_v
        self.is_int = is_int
        self.grabbed = False
        self.hovered = False

    def draw(self, surf, font):
        pygame.draw.rect(surf, (38, 40, 54), self.rect, border_radius=4)
        
        factor = (self.val - self.min_v) / (self.max_v - self.min_v + 0.0001)
        factor = max(0.0, min(1.0, factor))
        fill_w = int(self.rect.w * factor)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            pygame.draw.rect(surf, ACCENT_BLUE, fill_rect, border_radius=4)
        
        px = self.rect.x + fill_w
        thumb_color = (255, 255, 255) if (self.grabbed or self.hovered) else ACCENT_BLUE
        pygame.draw.circle(surf, thumb_color, (px, self.rect.y + 4), 6)
        if self.grabbed or self.hovered:
            pygame.draw.circle(surf, (*ACCENT_BLUE, 60), (px, self.rect.y + 4), 10, 2)
            
        val_str = f"{int(self.val)}" if self.is_int else f"{self.val:.2f}"
        lbl_surf = font.render(f"{self.label}:", True, TEXT_MUTED)
        val_surf = font.render(val_str, True, (255, 255, 255))
        
        surf.blit(lbl_surf, (self.rect.x, self.rect.y - 18))
        surf.blit(val_surf, (self.rect.x + self.rect.w - val_surf.get_width(), self.rect.y - 18))

    def handle(self, event):
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.inflate(10, 20).collidepoint(mx, my)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(15, 25).collidepoint(event.pos):
                self.grabbed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.grabbed = False
            
        if self.grabbed:
            rel_x = max(0, min(mx - self.rect.x, self.rect.w))
            raw_val = self.min_v + (rel_x / self.rect.w) * (self.max_v - self.min_v)
            self.val = int(round(raw_val)) if self.is_int else raw_val


class SimpleButton:
    def __init__(self, x, y, w, h, text, color=BUTTON_COLOR, hover_color=BUTTON_HOVER, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False

    def draw(self, surf, font):
        bg = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surf, bg, self.rect, border_radius=5)
        pygame.draw.rect(surf, PANEL_BORDER_COLOR, self.rect, width=1, border_radius=5)
        
        txt_surf = font.render(self.text, True, self.text_color)
        tx = self.rect.x + (self.rect.w - txt_surf.get_width()) // 2
        ty = self.rect.y + (self.rect.h - txt_surf.get_height()) // 2
        surf.blit(txt_surf, (tx, ty))

    def handle(self, event):
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mx, my)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                return True
        return False


class TextInput:
    def __init__(self, x, y, w, h, initial_val=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = initial_val
        self.active = False

    def draw(self, surf, font):
        bg = (28, 28, 42) if self.active else (18, 18, 26)
        border = ACCENT_BLUE if self.active else PANEL_BORDER_COLOR
        pygame.draw.rect(surf, bg, self.rect, border_radius=5)
        pygame.draw.rect(surf, border, self.rect, width=1, border_radius=5)
        
        display_text = self.val + ("|" if (self.active and (int(time.time() * 2) % 2 == 0)) else "")
        txt_surf = font.render(display_text, True, (255, 255, 255))
        surf.blit(txt_surf, (self.rect.x + 8, self.rect.y + (self.rect.h - txt_surf.get_height()) // 2))

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.val = self.val[:-1]
            elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.active = False
            elif event.unicode.isprintable():
                self.val += event.unicode


class ParticleEditor:
    def __init__(self, screen, clock, emitter=None, nm=None):
        self.screen = screen
        self.clock = clock
        self.emitter = emitter if emitter else ParticleEmitter(0, 0, "sandbox_vfx")
        self.nm = nm
        
        self.font_title = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.font_normal = pygame.font.SysFont("Segoe UI", 11)
        self.font_heading = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.font_dropdown = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.font_tutorial_body = pygame.font.SysFont("Segoe UI", 14)
        self.font_tutorial_title = pygame.font.SysFont("Segoe UI", 15, bold=True)
        
        self.color_picker = None
        self.picker_stop_idx = 0
        
        self.dragged_stop_idx = None
        self.dragged_stop_moved = False
        
        self.add_module_open = False
        self.txt_module_search = None
        self.modules_info = [
            {"id": "gravity", "name": "Gravity", "desc": "Applies Y gravity acceleration."},
            {"id": "wind", "name": "Wind", "desc": "Applies X lateral wind force."},
            {"id": "vortex", "name": "Vortex", "desc": "Swirls particles around source."},
            {"id": "chaos", "name": "Chaos", "desc": "Applies random turbulence noise."},
            {"id": "collision", "name": "Collision", "desc": "Bounces off walls & player."},
            {"id": "trail", "name": "Trail", "desc": "Spawns sub-particles trails."},
            {"id": "explosion", "name": "Explosion", "desc": "Detonates spark ring on death."}
        ]
        
        self.preview_emitter = ParticleEmitter(0, 0, "preview")
        self.preview_emitter.is_preview = True
        self.copy_properties(self.emitter, self.preview_emitter)
        
        self.dragging_mod_slider = None
        
        self.gallery_open = False
        self.gallery_emitters = {}
        for name in ["fire", "snow", "spark", "bubble", "portal", "fireball", "starfield", "rain", "laser", "lightning"]:
            em = ParticleEmitter(0, 0, name)
            em.is_preview = True
            self.load_preset_to_emitter(name, em)
            self.gallery_emitters[name] = em
            
        self.running = True
        self.drag_origin = False
        self.active_module = 0
        
        sw, sh = self.screen.get_size()
        self.preview_x = sw // 2
        self.preview_y = sh // 2 - 40
        self.preview_emitter.preview_pos = (self.preview_x, self.preview_y)
        
        self.fps_throttled = False
        self.last_throttle_time = 0
        self.particle_cap = 600
        self.last_warn_time = 0
        self.last_restore_time = 0

        import os
        tuto_flag_path = os.path.join("Assets", "ui", ".tutorial_done")
        self.tutorial_active = False
        self.tutorial_prompt = not os.path.exists(tuto_flag_path)
        self.tutorial_step = 0
        self.btn_tut_yes = pygame.Rect(0, 0, 0, 0)
        self.btn_tut_no = pygame.Rect(0, 0, 0, 0)
        self.btn_tut_next = pygame.Rect(0, 0, 0, 0)
        self.btn_tut_skip = pygame.Rect(0, 0, 0, 0)
        
        self.preview_obstacles = [PreviewObstacle(pygame.Rect(sw // 2 - 40, sh // 2 + 50, 80, 80))]
        self.gallery_page = 0
        self.current_editing_emitter = self.preview_emitter
        self.setup_ui()
        
    def mark_tutorial_as_done(self):
        import os
        tuto_flag_path = os.path.join("Assets", "ui", ".tutorial_done")
        try:
            os.makedirs(os.path.dirname(tuto_flag_path), exist_ok=True)
            with open(tuto_flag_path, "w") as f:
                f.write("done")
        except Exception:
            pass

    def copy_properties(self, src, dest):
        dest.name = src.name
        dest.rate = src.rate
        dest.spread = src.spread
        dest.speed = src.speed
        dest.size = src.size
        dest.gravity = src.gravity
        dest.friction = src.friction
        dest.colors = [dict(c) for c in src.colors]
        dest.lifetime = src.lifetime
        dest.active = src.active
        dest.vortex = getattr(src, "vortex", 0.0)
        dest.color_mode = getattr(src, "color_mode", "Lerp")
        dest.spawn_mode = getattr(src, "spawn_mode", "Continuous")
        dest.particle_style = getattr(src, "particle_style", "circle")
        dest.custom_sprite = getattr(src, "custom_sprite", "")
        dest.burst_interval = getattr(src, "burst_interval", 45)
        dest.chaos = getattr(src, "chaos", 0.0)
        dest.size_mode = getattr(src, "size_mode", "Constant")
        dest.overall_scale = getattr(src, "overall_scale", 0.5)
        dest.preview_scale = getattr(src, "preview_scale", 1.0)
        dest.active_modules = [dict(m) for m in getattr(src, "active_modules", [])]
        
        dest.emitter_type = getattr(src, "emitter_type", "Point")
        dest.spawn_width = getattr(src, "spawn_width", 100)
        dest.spawn_height = getattr(src, "spawn_height", 50)
        dest.direction_angle = getattr(src, "direction_angle", -1.57)
        dest.is_sub_emitter = getattr(src, "is_sub_emitter", False)
        
        dest.sub_emitters = []
        for sub_src in getattr(src, "sub_emitters", []):
            sub_dest = ParticleEmitter(sub_src.x, sub_src.y, sub_src.name)
            self.copy_properties(sub_src, sub_dest)
            dest.sub_emitters.append(sub_dest)

    def setup_ui(self):
        sw, sh = self.screen.get_size()
        px = 20
        
        self.txt_name = TextInput(px, 45, 140, 26, self.preview_emitter.name)
        
        self.btn_active = SimpleButton(
            px + 150, 45, 60, 26,
            "Active" if self.preview_emitter.active else "Inactive",
            color=(22, 48, 36) if self.preview_emitter.active else (42, 24, 28),
            hover_color=(32, 68, 48) if self.preview_emitter.active else (62, 34, 40),
            text_color=(60, 220, 130) if self.preview_emitter.active else (230, 100, 100)
        )
        
        self.module_tabs = [
            SimpleButton(px, 115, 210, 30, "Spawn Module"),
            SimpleButton(px, 150, 210, 30, "Particle Initialization"),
            SimpleButton(px, 185, 210, 30, "Physics & Forces Update"),
            SimpleButton(px, 220, 210, 30, "Color Over Life Module")
        ]

        import math
        self.sliders = {
            # Spawn
            "rate": Slider(px, 345, 210, "Spawn Rate", 0.1, 25.0, self.preview_emitter.rate),
            "burst_interval": Slider(px, 405, 210, "Burst Interval (frames)", 10, 180, self.preview_emitter.burst_interval, is_int=True),
            "spawn_width": Slider(px, 515, 210, "Spawn Width", 10, 1200, getattr(self.preview_emitter, "spawn_width", 100), is_int=True),
            "spawn_height": Slider(px, 565, 210, "Spawn Height", 10, 1000, getattr(self.preview_emitter, "spawn_height", 50), is_int=True),
            
            # Init
            "life": Slider(px, 300, 210, "Lifetime (frames)", 10, 180, self.preview_emitter.lifetime, is_int=True),
            "speed": Slider(px, 340, 210, "Initial Speed", 0.0, 15.0, self.preview_emitter.speed),
            "spread": Slider(px, 380, 210, "Spread Angle (rad)", 0.0, 6.28, self.preview_emitter.spread),
            "size": Slider(px, 420, 210, "Start Size", 1.0, 25.0, self.preview_emitter.size),
            "direction_angle": Slider(px, 460, 210, "Direction Angle (deg)", -180.0, 180.0, math.degrees(getattr(self.preview_emitter, "direction_angle", -1.57))),
            "preview_scale": Slider(px, 500, 210, "Preview Scale Factor", 0.1, 4.0, self.preview_emitter.preview_scale),
            
            # Physics
            "friction": Slider(px, 300, 210, "Base Friction", 0.90, 1.00, self.preview_emitter.friction),
        }

        self.btn_spawn_mode = SimpleButton(px, 295, 210, 28, f"Spawn Mode: {self.preview_emitter.spawn_mode}")
        self.btn_color_mode = SimpleButton(px, 295, 210, 28, f"Color Mode: {self.preview_emitter.color_mode}")
        self.btn_emitter_type = SimpleButton(px, 465, 210, 28, f"Emitter Type: {getattr(self.preview_emitter, 'emitter_type', 'Point')}")
        
        self.btn_style = MenuButton(
            rect=(px, 545, 150, 28),
            text=f"Style: {self.preview_emitter.particle_style.capitalize()}",
            submenu_items=[
                ("Circle", lambda: self.set_style("circle")),
                ("Spark", lambda: self.set_style("spark")),
                ("Bubble", lambda: self.set_style("bubble")),
                ("Snow", lambda: self.set_style("snow")),
                ("Fireball", lambda: self.set_style("fireball")),
                ("Star", lambda: self.set_style("star")),
                ("Laser", lambda: self.set_style("laser")),
                ("Lightning", lambda: self.set_style("lightning")),
            ],
            font=self.font_dropdown,
            item_font_size=14,
            bg_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            hover_color=BUTTON_HOVER
        )
        self.btn_size_mode = MenuButton(
            rect=(px, 580, 150, 28),
            text=f"Size: {self.preview_emitter.size_mode}",
            submenu_items=[
                ("Constant", lambda: self.set_size_mode("Constant")),
                ("Shrink", lambda: self.set_size_mode("Shrink")),
                ("Grow", lambda: self.set_size_mode("Grow")),
                ("Grow & Shrink", lambda: self.set_size_mode("Grow & Shrink")),
            ],
            font=self.font_dropdown,
            item_font_size=14,
            bg_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            hover_color=BUTTON_HOVER
        )
        self.txt_sprite = TextInput(px, 635, 210, 26, self.preview_emitter.custom_sprite)
        
        self.btn_open_add_module = SimpleButton(px, 330, 210, 28, "+ Add Module", color=BUTTON_COLOR, hover_color=BUTTON_HOVER)
        
        self.btn_static_color = SimpleButton(px, 345, 210, 28, "Set Color Stop", color=BUTTON_COLOR)
        
        self.btn_add_stop = SimpleButton(px, 410, 100, 28, "Add Color", color=(40,55,80))
        self.btn_remove_stop = SimpleButton(px + 110, 410, 100, 28, "Remove Color", color=(80,45,45))
        
        self.btn_grad_flame = SimpleButton(px, 455, 48, 20, "Flame", color=(120,40,20), hover_color=(160,50,25))
        self.btn_grad_glacier = SimpleButton(px + 53, 455, 48, 20, "Frost", color=(20,70,120), hover_color=(25,90,160))
        self.btn_grad_nebula = SimpleButton(px + 106, 455, 48, 20, "Void", color=(80,30,120), hover_color=(110,40,160))
        self.btn_grad_acid = SimpleButton(px + 159, 455, 48, 20, "Toxic", color=(30,100,40), hover_color=(40,130,50))
        
        rx = sw - 230
        self.btn_presets_gallery = SimpleButton(rx, 340, 210, 32, "Presets Gallery", color=ACCENT_BLUE)
        self.btn_replay_tutorial = SimpleButton(rx, 385, 210, 32, "Rejouer le Guide", color=BUTTON_COLOR, hover_color=BUTTON_HOVER)
        bx = sw // 2 - 160
        by = sh - 45
        self.btn_apply = SimpleButton(bx, by, 150, 32, "Apply to Level", color=ACCENT_BLUE, text_color=(255, 255, 255))
        self.btn_cancel = SimpleButton(bx + 170, by, 150, 32, "Cancel & Exit", color=(40, 42, 54))

    def set_style(self, style_name):
        self.current_editing_emitter.particle_style = style_name
        self.btn_style.text = f"Style: {style_name.capitalize()}"

    def set_size_mode(self, size_mode):
        self.current_editing_emitter.size_mode = size_mode
        self.btn_size_mode.text = f"Size: {size_mode}"

    def add_module(self, mod_id):
        if any(m["id"] == mod_id for m in self.current_editing_emitter.active_modules):
            return
        
        defaults = {
            "gravity": {"id": "gravity", "enabled": True, "gravity": -0.1},
            "wind": {"id": "wind", "enabled": True, "wind": 0.05},
            "vortex": {"id": "vortex", "enabled": True, "vortex": 0.1},
            "chaos": {"id": "chaos", "enabled": True, "chaos": 0.08},
            "collision": {"id": "collision", "enabled": True, "target": "All", "bounce": True, "add_particles": True, "kill_on_collision": False},
            "trail": {"id": "trail", "enabled": True},
            "explosion": {"id": "explosion", "enabled": True}
        }
        self.current_editing_emitter.active_modules.append(defaults[mod_id])

    def load_preset_to_emitter(self, p_name, em):
        preset_values = {
            "fire": {
                "rate": 10.0, "life": 45, "speed": 3.8, "spread": 0.35, "size": 9.0,
                "friction": 0.98, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 200]},
                    {"pos": 0.3, "color": [255, 140, 0]},
                    {"pos": 0.7, "color": [255, 50, 0]},
                    {"pos": 1.0, "color": [40, 10, 10]}
                ],
                "style": "circle", "size_mode": "Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "gravity", "enabled": True, "gravity": -0.15},
                    {"id": "chaos", "enabled": True, "chaos": 0.20}
                ]
            },
            "snow": {
                "rate": 2.0, "life": 150, "speed": 1.0, "spread": 3.14, "size": 3.0,
                "friction": 0.99, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 255]},
                    {"pos": 1.0, "color": [190, 220, 255]}
                ],
                "style": "snow", "size_mode": "Constant", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "gravity", "enabled": True, "gravity": 0.04},
                    {"id": "chaos", "enabled": True, "chaos": 0.05}
                ]
            },
            "spark": {
                "rate": 12.0, "life": 25, "speed": 6.0, "spread": 3.14, "size": 2.5,
                "friction": 0.94, "color_mode": "Lerp", "spawn_mode": "Burst", "burst_interval": 45,
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 255]},
                    {"pos": 0.5, "color": [0, 220, 255]},
                    {"pos": 1.0, "color": [255, 0, 150]}
                ],
                "style": "spark", "size_mode": "Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "gravity", "enabled": True, "gravity": 0.15},
                    {"id": "chaos", "enabled": True, "chaos": 0.10}
                ]
            },
            "bubble": {
                "rate": 3.0, "life": 100, "speed": 1.8, "spread": 0.6, "size": 12.0,
                "friction": 0.97, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [120, 255, 120]},
                    {"pos": 0.5, "color": [0, 200, 160]},
                    {"pos": 1.0, "color": [0, 80, 40]}
                ],
                "style": "bubble", "size_mode": "Grow & Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "gravity", "enabled": True, "gravity": -0.05},
                    {"id": "chaos", "enabled": True, "chaos": 0.05},
                    {"id": "collision", "enabled": True, "target": "All", "bounce": True, "add_particles": True, "kill_on_collision": False}
                ]
            },
            "portal": {
                "rate": 7.0, "life": 60, "speed": 2.4, "spread": 6.28, "size": 5.0,
                "friction": 0.98, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 255]},
                    {"pos": 0.5, "color": [180, 50, 255]},
                    {"pos": 1.0, "color": [30, 0, 120]}
                ],
                "style": "circle", "size_mode": "Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "vortex", "enabled": True, "vortex": 0.22}
                ]
            },
            "fireball": {
                "rate": 8.0, "life": 45, "speed": 4.2, "spread": 0.15, "size": 11.0,
                "friction": 0.98, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 255]},
                    {"pos": 0.2, "color": [255, 220, 0]},
                    {"pos": 0.6, "color": [255, 60, 0]},
                    {"pos": 1.0, "color": [60, 0, 0]}
                ],
                "style": "fireball", "size_mode": "Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "chaos", "enabled": True, "chaos": 0.12}
                ]
            },
            "starfield": {
                "rate": 5.0, "life": 80, "speed": 0.6, "spread": 6.28, "size": 6.0,
                "friction": 1.0, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 255]},
                    {"pos": 0.4, "color": [130, 210, 255]},
                    {"pos": 1.0, "color": [80, 0, 150]}
                ],
                "style": "star", "size_mode": "Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "active_modules": [
                    {"id": "wind", "enabled": True, "wind": 0.12},
                    {"id": "chaos", "enabled": True, "chaos": 0.02}
                ]
            },
            "rain": {
                "rate": 0.61, "life": 100, "speed": 5.0, "spread": 0.02, "size": 1.0,
                "friction": 1.0, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [98, 148, 255]},
                    {"pos": 1.0, "color": [98, 148, 255]}
                ],
                "style": "spark", "size_mode": "Constant", "overall_scale": 0.5, "preview_scale": 1.0,
                "emitter_type": "Line", "spawn_width": 295, "spawn_height": 30,
                "direction_angle": 1.57,
                "active_modules": [
                    {"id": "gravity", "enabled": True, "gravity": 0.08},
                    {
                        "id": "collision", "enabled": True, "target": "All", "bounce": False,
                        "add_particles": True, "kill_on_collision": True,
                        "collision_trigger_emitter": "splash", "splash_style": "circle",
                        "splash_count": 5, "splash_speed": 2.2
                    }
                ],
                "sub_emitters": [
                    {
                        "name": "splash",
                        "rate": 4.0, "life": 22, "speed": 2.2, "spread": 0.9, "size": 4.0,
                        "friction": 1.0, "color_mode": "Lerp", "spawn_mode": "Continuous",
                        "colors": [
                            {"pos": 0.0, "color": [98, 148, 255]},
                            {"pos": 1.0, "color": [98, 148, 255]}
                        ],
                        "style": "circle", "size_mode": "Grow", "overall_scale": 0.5, "preview_scale": 1.0,
                        "emitter_type": "Point", "direction_angle": -1.57, "is_sub_emitter": True,
                        "active_modules": [
                            {"id": "gravity", "enabled": True, "gravity": 0.15}
                        ]
                    }
                ]
            },
            "laser": {
                "rate": 10.0, "life": 60, "speed": 6.0, "spread": 0.2, "size": 6.0,
                "friction": 0.96, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 60, 60]},
                    {"pos": 1.0, "color": [200, 0, 0]}
                ],
                "style": "laser", "size_mode": "Shrink", "overall_scale": 0.5, "preview_scale": 1.0,
                "direction_angle": 1.57,
                "active_modules": [
                    {
                        "id": "collision", "enabled": True, "target": "All", "bounce": False,
                        "add_particles": True, "kill_on_collision": False,
                        "collision_trigger_emitter": "None", "splash_style": "circle",
                        "splash_count": 3, "splash_speed": 2.0
                    }
                ]
            },
            "lightning": {
                "rate": 3.0, "life": 45, "speed": 4.0, "spread": 0.5, "size": 5.0,
                "friction": 0.95, "color_mode": "Lerp", "spawn_mode": "Continuous",
                "colors": [
                    {"pos": 0.0, "color": [255, 255, 255]},
                    {"pos": 0.5, "color": [180, 220, 255]},
                    {"pos": 1.0, "color": [100, 150, 255]}
                ],
                "style": "lightning", "size_mode": "Constant", "overall_scale": 0.5, "preview_scale": 1.0,
                "direction_angle": 1.57,
                "active_modules": [
                    {
                        "id": "collision", "enabled": True, "target": "All", "bounce": False,
                        "add_particles": True, "kill_on_collision": False,
                        "collision_trigger_emitter": "None", "splash_style": "circle",
                        "splash_count": 4, "splash_speed": 3.0
                    }
                ]
            }
        }
        p = preset_values.get(p_name, preset_values["fire"])
        self.load_preset_dict_to_emitter(p, em)

    def load_preset_dict_to_emitter(self, p, em):
        em.rate = p["rate"]
        em.burst_interval = p.get("burst_interval", 45)
        em.lifetime = p.get("life", 60)
        em.speed = p["speed"]
        em.spread = p.get("spread", 0.5)
        em.size = p.get("size", 6.0)
        em.friction = p["friction"]
        em.color_mode = p.get("color_mode", "Lerp")
        em.spawn_mode = p.get("spawn_mode", "Continuous")
        em.particle_style = p.get("style", "circle")
        em.size_mode = p.get("size_mode", "Constant")
        em.custom_sprite = p.get("custom_sprite", "")
        em.overall_scale = p.get("overall_scale", 0.5)
        em.preview_scale = p.get("preview_scale", 1.0)
        em.colors = [dict(c) for c in p["colors"]]
        em.active_modules = [dict(m) for m in p["active_modules"]]
        em.particles.clear()
        
        em.emitter_type = p.get("emitter_type", "Point")
        em.spawn_width = p.get("spawn_width", 100)
        em.spawn_height = p.get("spawn_height", 50)
        em.direction_angle = p.get("direction_angle", -1.57)
        em.is_sub_emitter = p.get("is_sub_emitter", False)
        
        em.sub_emitters = []
        for sub_p in p.get("sub_emitters", []):
            sub_name = sub_p.get("name", "sub")
            sub_em = ParticleEmitter(em.x, em.y, sub_name)
            self.load_preset_dict_to_emitter(sub_p, sub_em)
            em.sub_emitters.append(sub_em)

    def load_preset(self, p_name):
        self.load_preset_to_emitter(p_name, self.current_editing_emitter)
        if p_name == "rain":
            self.preview_y = 60
        self.sync_ui_from_selected()

    def update_from_sliders(self):
        em = self.current_editing_emitter
        em.name = self.txt_name.val
        em.rate = self.sliders["rate"].val
        em.burst_interval = int(self.sliders["burst_interval"].val)
        em.lifetime = int(self.sliders["life"].val)
        em.speed = self.sliders["speed"].val
        em.spread = self.sliders["spread"].val
        em.size = self.sliders["size"].val
        em.friction = self.sliders["friction"].val
        em.preview_scale = self.sliders["preview_scale"].val
        em.custom_sprite = self.txt_sprite.val
        
        em.spawn_width = self.sliders["spawn_width"].val
        em.spawn_height = self.sliders["spawn_height"].val
        import math
        em.direction_angle = math.radians(self.sliders["direction_angle"].val)

    def sync_ui_from_selected(self):
        em = self.current_editing_emitter
        self.sliders["rate"].val = em.rate
        self.sliders["burst_interval"].val = em.burst_interval
        self.sliders["life"].val = em.lifetime
        self.sliders["speed"].val = em.speed
        self.sliders["spread"].val = em.spread
        self.sliders["size"].val = em.size
        self.sliders["friction"].val = em.friction
        self.sliders["preview_scale"].val = em.preview_scale
        
        self.sliders["spawn_width"].val = getattr(em, "spawn_width", 100)
        self.sliders["spawn_height"].val = getattr(em, "spawn_height", 50)
        import math
        self.sliders["direction_angle"].val = math.degrees(getattr(em, "direction_angle", -1.57))
        
        self.txt_name.val = em.name
        self.txt_sprite.val = em.custom_sprite
        
        self.btn_spawn_mode.text = f"Spawn Mode: {em.spawn_mode}"
        self.btn_color_mode.text = f"Color Mode: {em.color_mode}"
        self.btn_emitter_type.text = f"Emitter Type: {getattr(em, 'emitter_type', 'Point')}"
        self.btn_style.text = f"Style: {em.particle_style.capitalize()}"
        self.btn_size_mode.text = f"Size: {em.size_mode}"
        self.btn_active.text = "Active" if em.active else "Inactive"
        self.btn_active.color = (22, 48, 36) if em.active else (42, 24, 28)
        self.btn_active.hover_color = (32, 68, 48) if em.active else (62, 34, 40)
        self.btn_active.text_color = (60, 220, 130) if em.active else (230, 100, 100)

    def confirm_color_picker(self, color):
        self.current_editing_emitter.colors[self.picker_stop_idx]["color"] = list(color)
        self.color_picker = None

    def close_color_picker(self):
        self.color_picker = None

    def interpolate_color_stops(self, stops, t):
        n = len(stops)
        if n == 0:
            return (255, 255, 255)
        if n == 1:
            return tuple(stops[0]["color"])
        if t <= stops[0]["pos"]:
            return tuple(stops[0]["color"])
        if t >= stops[-1]["pos"]:
            return tuple(stops[-1]["color"])
        for i in range(n - 1):
            s1 = stops[i]
            s2 = stops[i + 1]
            if s1["pos"] <= t <= s2["pos"]:
                span = s2["pos"] - s1["pos"] + 0.0001
                factor = (t - s1["pos"]) / span
                c1 = s1["color"]
                c2 = s2["color"]
                return tuple(int(c1[j] + (c2[j] - c1[j]) * factor) for j in range(3))
        return tuple(stops[-1]["color"])

    def run(self):
        sw, sh = self.screen.get_size()
        preview_area = pygame.Rect(250, 0, sw - 500, sh - 60)
        
        while self.running:
            sw, sh = self.screen.get_size()
            mx, my = pygame.mouse.get_pos()
            preview_area = pygame.Rect(250, 0, sw - 500, sh - 60)
            
            fps = self.clock.get_fps()
            now = time.time()
            if fps > 0 and fps < 20 and len(self.preview_emitter.particles) > 150:
                if not self.fps_throttled:
                    self.fps_throttled = True
                    self.last_throttle_time = now
                    if self.nm and (now - self.last_warn_time > 45.0):
                        self.nm.notify('warning', 'Perf Regulation', 'High load: capping to 150 active particles.', duration=3.0)
                        self.last_warn_time = now
                self.particle_cap = 150
            elif fps > 35 and self.fps_throttled and now - self.last_throttle_time > 2.0:
                self.fps_throttled = False
                self.particle_cap = 600
                self.last_throttle_time = now
                if self.nm and (now - self.last_restore_time > 45.0):
                    self.nm.notify('success', 'Perf Restored', 'FPS stabilized: cap restored to 600 particles.', duration=2.0)
                    self.last_restore_time = now
            
            self.preview_emitter.particle_cap = self.particle_cap
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                
                if self.tutorial_prompt:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.btn_tut_yes.collidepoint(event.pos):
                            self.tutorial_prompt = False
                            self.tutorial_active = True
                            self.tutorial_step = 0
                            self.mark_tutorial_as_done()
                        elif self.btn_tut_no.collidepoint(event.pos):
                            self.tutorial_prompt = False
                            self.mark_tutorial_as_done()
                    continue

                if self.tutorial_active:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.btn_tut_next.collidepoint(event.pos):
                            if self.tutorial_step < 7:
                                self.tutorial_step += 1
                                if self.tutorial_step == 6:
                                    self.gallery_open = True
                                else:
                                    self.gallery_open = False
                            else:
                                self.tutorial_active = False
                                self.gallery_open = False
                            continue
                        elif self.btn_tut_skip.collidepoint(event.pos):
                            self.tutorial_active = False
                            self.gallery_open = False
                            continue
                            
                        is_tab_click = False
                        for tab_idx, tab_btn in enumerate(self.module_tabs):
                            if tab_btn.rect.collidepoint(event.pos):
                                is_tab_click = True
                                break
                        if is_tab_click:
                            if self.nm:
                                self.nm.notify('info', 'Tutoriel', "Veuillez utiliser le bouton SUIVANT pour changer d'onglet.", duration=1.5)
                            continue
                            
                        x, y = event.pos
                        allowed = False
                        reason = ""
                        
                        if self.tutorial_step == 0:
                            if preview_area.collidepoint(event.pos):
                                allowed = True
                            else:
                                reason = "Déplacez l'émetteur en glissant la souris dans la zone centrale."
                                
                        elif self.tutorial_step == 1:
                            if x < 250:
                                allowed = True
                            else:
                                reason = "Utilisez les contrôles de Spawn dans le panneau de gauche."
                                
                        elif self.tutorial_step == 2:
                            if preview_area.collidepoint(event.pos):
                                allowed = True
                            else:
                                reason = "Consultez les informations de performance en haut à gauche."
                                
                        elif self.tutorial_step == 3:
                            if x < 250:
                                allowed = True
                            else:
                                reason = "Utilisez les contrôles d'Initialisation dans le panneau de gauche."
                                
                        elif self.tutorial_step == 4:
                            if x < 250 or self.add_module_open:
                                allowed = True
                            else:
                                reason = "Utilisez les contrôles de Physique dans le panneau de gauche."
                                
                        elif self.tutorial_step == 5:
                            if x < 250:
                                allowed = True
                            else:
                                reason = "Utilisez les contrôles de Couleur dans le panneau de gauche."
                                
                        elif self.tutorial_step == 6:
                            if (x > sw - 250) or self.gallery_open:
                                allowed = True
                            else:
                                reason = "Cliquez sur 'Presets Gallery' en haut à droite."
                                
                        elif self.tutorial_step == 7:
                            if y > sh - 60:
                                allowed = True
                            else:
                                reason = "Cliquez sur 'Apply to Level' ou 'Cancel & Exit' pour terminer."
                                
                        if not allowed:
                            if self.nm and reason:
                                self.nm.notify('info', 'Action Bloquée', reason, duration=2.0)
                            continue

                if self.color_picker is not None:
                    self.color_picker.handle_event(event)
                    continue
                
                if self.gallery_open:
                    modal_w, modal_h = 740, 360
                    modal_x = (sw - modal_w) // 2
                    modal_y = (sh - modal_h) // 2
                    close_rect = pygame.Rect(modal_x + modal_w - 35, modal_y + 12, 22, 22)
                    prev_rect = pygame.Rect(modal_x + 15, modal_y + 165, 24, 30)
                    next_rect = pygame.Rect(modal_x + modal_w - 39, modal_y + 165, 24, 30)
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if close_rect.collidepoint(event.pos):
                            self.gallery_open = False
                            continue
                        
                        if prev_rect.collidepoint(event.pos) and self.gallery_page > 0:
                            self.gallery_page -= 1
                            continue
                            
                        if next_rect.collidepoint(event.pos) and self.gallery_page < 2:
                            self.gallery_page += 1
                            continue
                        
                        presets_list = ["fire", "snow", "spark", "bubble", "portal", "fireball", "starfield", "rain", "laser", "lightning"]
                        start_idx = self.gallery_page * 4
                        end_idx = min(start_idx + 4, len(presets_list))
                        
                        for local_idx in range(start_idx, end_idx):
                            p_name = presets_list[local_idx]
                            idx_on_page = local_idx - start_idx
                            card_x = modal_x + 60 + idx_on_page * 160
                            card_y = modal_y + 70
                            card_rect = pygame.Rect(card_x, card_y, 140, 240)
                            if card_rect.collidepoint(event.pos):
                                self.load_preset(p_name)
                                self.gallery_open = False
                                break
                    continue

                if self.add_module_open:
                    modal_w, modal_h = 400, 450
                    modal_x = (sw - modal_w) // 2
                    modal_y = (sh - modal_h) // 2
                    close_rect = pygame.Rect(modal_x + modal_w - 35, modal_y + 12, 22, 22)
                    
                    self.txt_module_search.handle(event)
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if close_rect.collidepoint(event.pos):
                            self.add_module_open = False
                            self.txt_module_search.active = False
                            continue
                        
                        query = self.txt_module_search.val.lower()
                        filtered = [m for m in self.modules_info if query in m["name"].lower() or query in m["desc"].lower()]
                        row_y = modal_y + 90
                        for mod in filtered:
                            add_btn = pygame.Rect(modal_x + 300, row_y + 11, 70, 20)
                            if add_btn.collidepoint(event.pos):
                                is_added = any(m["id"] == mod["id"] for m in self.current_editing_emitter.active_modules)
                                if not is_added:
                                    self.add_module(mod["id"])
                                    self.add_module_open = False
                                    self.txt_module_search.active = False
                                    break
                            row_y += 50
                    continue

                active_dropdown = None
                if self.active_module == 1:
                    if self.btn_style.dropdown.is_open:
                        active_dropdown = self.btn_style.dropdown
                    elif self.btn_size_mode.dropdown.is_open:
                        active_dropdown = self.btn_size_mode.dropdown
                
                if active_dropdown is not None:
                    active_dropdown.handle_event(event)
                    continue

                self.txt_name.handle(event)
                
                if self.btn_active.handle(event):
                    self.current_editing_emitter.active = not self.current_editing_emitter.active
                    self.btn_active.text = "Active" if self.current_editing_emitter.active else "Inactive"
                    self.btn_active.color = (22, 48, 36) if self.current_editing_emitter.active else (42, 24, 28)
                    self.btn_active.hover_color = (32, 68, 48) if self.current_editing_emitter.active else (62, 34, 40)
                    self.btn_active.text_color = (60, 220, 130) if self.current_editing_emitter.active else (230, 100, 100)
                
                for i, tab in enumerate(self.module_tabs):
                    if tab.handle(event):
                        self.active_module = i
                
                if self.active_module == 0: # Spawn
                    if self.btn_spawn_mode.handle(event):
                        next_mode = "Burst" if self.current_editing_emitter.spawn_mode == "Continuous" else "Continuous"
                        self.current_editing_emitter.spawn_mode = next_mode
                        self.btn_spawn_mode.text = f"Spawn Mode: {next_mode}"
                    if self.btn_emitter_type.handle(event):
                        types = ["Point", "Line", "Box"]
                        cur_t = getattr(self.current_editing_emitter, "emitter_type", "Point")
                        next_t = types[(types.index(cur_t) + 1) % len(types)]
                        self.current_editing_emitter.emitter_type = next_t
                        self.btn_emitter_type.text = f"Emitter Type: {next_t}"
                    self.sliders["rate"].handle(event)
                    if self.current_editing_emitter.spawn_mode == "Burst":
                        self.sliders["burst_interval"].handle(event)
                    if getattr(self.current_editing_emitter, "emitter_type", "Point") in ["Line", "Box"]:
                        self.sliders["spawn_width"].handle(event)
                    if getattr(self.current_editing_emitter, "emitter_type", "Point") == "Box":
                        self.sliders["spawn_height"].handle(event)
                        
                elif self.active_module == 1: # Init
                    self.txt_sprite.handle(event)
                    self.sliders["life"].handle(event)
                    self.sliders["speed"].handle(event)
                    self.sliders["spread"].handle(event)
                    self.sliders["size"].handle(event)
                    self.sliders["direction_angle"].handle(event)
                    self.sliders["preview_scale"].handle(event)
                    self.btn_style.handle_event(event)
                    self.btn_size_mode.handle_event(event)
                    
                elif self.active_module == 2: # Physics Component Stack
                    self.sliders["friction"].handle(event)
                    
                    if self.btn_open_add_module.handle(event):
                        self.add_module_open = True
                        modal_w, modal_h = 400, 450
                        modal_x = (sw - modal_w) // 2
                        modal_y = (sh - modal_h) // 2
                        self.txt_module_search = TextInput(modal_x + 20, modal_y + 50, 360, 26, "")
                        self.txt_module_search.active = True
                    
                    y_offset = 375
                    modules_to_remove = []
                    for idx, mod in enumerate(self.current_editing_emitter.active_modules):
                        m_id = mod["id"]
                        has_slider = m_id in ["gravity", "wind", "vortex", "chaos"]
                        if m_id == "collision":
                            h = 165
                        else:
                            h = 48 if has_slider else 30
                        
                        cb_rect = pygame.Rect(25, y_offset + 8, 14, 14)
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            if cb_rect.collidepoint(event.pos):
                                mod["enabled"] = not mod["enabled"]
                        
                        del_rect = pygame.Rect(205, y_offset + 6, 18, 18)
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            if del_rect.collidepoint(event.pos):
                                modules_to_remove.append(mod)
                        
                        if has_slider:
                            track_rect = pygame.Rect(45, y_offset + 28, 120, 6)
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                if track_rect.inflate(10, 15).collidepoint(event.pos):
                                    self.dragging_mod_slider = (idx, m_id)
                            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                                self.dragging_mod_slider = None
                            
                            if event.type == pygame.MOUSEMOTION and self.dragging_mod_slider == (idx, m_id):
                                p = max(0.0, min(1.0, (mx - track_rect.x) / track_rect.w))
                                if m_id in ["gravity", "wind", "vortex"]:
                                    val = -0.5 + p * 1.0 # range [-0.5, 0.5]
                                else: # chaos
                                    val = p # range [0.0, 1.0]
                                mod[m_id] = val
                        
                        if m_id == "collision":
                            btn_rect = pygame.Rect(45, y_offset + 24, 150, 18)
                            bounce_rect = pygame.Rect(45, y_offset + 48, 70, 14)
                            kill_rect = pygame.Rect(135, y_offset + 48, 80, 14)
                            sparks_rect = pygame.Rect(45, y_offset + 68, 120, 14)
                            
                            trigger_btn_rect = pygame.Rect(45, y_offset + 88, 115, 18)
                            create_btn_rect = pygame.Rect(165, y_offset + 88, 30, 18)
                            style_btn_rect = pygame.Rect(45, y_offset + 108, 150, 18)
                            track_rect_count = pygame.Rect(45, y_offset + 132, 110, 6)
                            track_rect_speed = pygame.Rect(45, y_offset + 152, 110, 6)
                            
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                if btn_rect.collidepoint(event.pos):
                                    cur = mod.get("target", "All")
                                    if cur == "All":
                                        mod["target"] = "Collisions Only"
                                    elif cur == "Collisions Only":
                                        mod["target"] = "Player Only"
                                    else:
                                        mod["target"] = "All"
                                elif bounce_rect.collidepoint(event.pos):
                                    mod["bounce"] = not mod.get("bounce", True)
                                elif kill_rect.collidepoint(event.pos):
                                    mod["kill_on_collision"] = not mod.get("kill_on_collision", False)
                                elif sparks_rect.collidepoint(event.pos):
                                    mod["add_particles"] = not mod.get("add_particles", True)
                                elif trigger_btn_rect.collidepoint(event.pos):
                                    subs = ["None"] + [sub.name for sub in self.preview_emitter.sub_emitters]
                                    cur = mod.get("collision_trigger_emitter", "None")
                                    if cur not in subs:
                                        cur = "None"
                                    next_idx = (subs.index(cur) + 1) % len(subs)
                                    mod["collision_trigger_emitter"] = subs[next_idx]
                                elif create_btn_rect.collidepoint(event.pos):
                                    existing_names = [sub.name for sub in self.preview_emitter.sub_emitters]
                                    i = 1
                                    while f"sub_{i}" in existing_names:
                                        i += 1
                                    new_sub_name = f"sub_{i}"
                                    new_sub = ParticleEmitter(self.preview_emitter.x, self.preview_emitter.y, new_sub_name)
                                    new_sub.is_sub_emitter = True
                                    new_sub.rate = 5
                                    new_sub.spread = 0.8
                                    new_sub.speed = 2.5
                                    new_sub.size = 6.0
                                    new_sub.lifetime = 25
                                    new_sub.particle_style = "spark"
                                    new_sub.preview_pos = (self.preview_x, self.preview_y)
                                    self.preview_emitter.sub_emitters.append(new_sub)
                                    mod["collision_trigger_emitter"] = new_sub_name
                                    self.current_editing_emitter.preview_pos = (self.preview_x, self.preview_y)
                                    self.current_editing_emitter = new_sub
                                    self.sync_ui_from_selected()
                                    if self.nm:
                                        self.nm.notify('success', 'On-Hit Emitter Created', f"Created and selected '{new_sub_name}'.")
                                elif style_btn_rect.collidepoint(event.pos):
                                    styles = ["spark", "circle", "bubble", "snow", "fireball", "star"]
                                    cur = mod.get("splash_style", "spark")
                                    if cur not in styles:
                                        cur = "spark"
                                    next_idx = (styles.index(cur) + 1) % len(styles)
                                    mod["splash_style"] = styles[next_idx]
                                elif track_rect_count.inflate(10, 15).collidepoint(event.pos):
                                    self.dragging_mod_slider = (idx, "splash_count")
                                elif track_rect_speed.inflate(10, 15).collidepoint(event.pos):
                                    self.dragging_mod_slider = (idx, "splash_speed")
                                        
                            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                                if self.dragging_mod_slider and self.dragging_mod_slider[1] in ["splash_count", "splash_speed"]:
                                    self.dragging_mod_slider = None
                                    
                            if event.type == pygame.MOUSEMOTION and self.dragging_mod_slider and self.dragging_mod_slider[0] == idx:
                                slider_id = self.dragging_mod_slider[1]
                                if slider_id == "splash_count":
                                    p = max(0.0, min(1.0, (mx - track_rect_count.x) / track_rect_count.w))
                                    mod["splash_count"] = int(1 + p * 7)
                                elif slider_id == "splash_speed":
                                    p = max(0.0, min(1.0, (mx - track_rect_speed.x) / track_rect_speed.w))
                                    mod["splash_speed"] = round(0.5 + p * 4.5, 1)
                        
                        y_offset += h + 8
                    
                    for r_mod in modules_to_remove:
                        if r_mod in self.current_editing_emitter.active_modules:
                            self.current_editing_emitter.active_modules.remove(r_mod)
                        
                elif self.active_module == 3: # Color
                    if self.btn_color_mode.handle(event):
                        modes = ["Lerp", "Static", "Rainbow"]
                        idx = (modes.index(self.current_editing_emitter.color_mode) + 1) % len(modes)
                        next_mode = modes[idx]
                        self.current_editing_emitter.color_mode = next_mode
                        self.btn_color_mode.text = f"Color Mode: {next_mode}"
                        
                    if self.current_editing_emitter.color_mode == "Lerp":
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            for idx, stop in enumerate(self.current_editing_emitter.colors):
                                p = stop["pos"]
                                px = 20 + p * 210
                                handle_rect = pygame.Rect(px - 10, 365, 20, 20)
                                if handle_rect.collidepoint(event.pos):
                                    self.dragged_stop_idx = idx
                                    self.dragged_stop_moved = False
                                    break
                                    
                        elif event.type == pygame.MOUSEMOTION and self.dragged_stop_idx is not None:
                            new_p = max(0.0, min(1.0, (mx - 20) / 210.0))
                            self.current_editing_emitter.colors[self.dragged_stop_idx]["pos"] = new_p
                            self.dragged_stop_moved = True
                            
                        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragged_stop_idx is not None:
                            if not self.dragged_stop_moved:
                                self.picker_stop_idx = self.dragged_stop_idx
                                self.color_picker = ColorPicker(
                                    rect=(260, 100, 220, 330),
                                    initial_color=tuple(self.current_editing_emitter.colors[self.picker_stop_idx]["color"]),
                                    on_confirm=self.confirm_color_picker,
                                    on_cancel=self.close_color_picker
                                )
                            self.dragged_stop_idx = None
                            self.current_editing_emitter.colors.sort(key=lambda s: s["pos"])
                                    
                        if self.btn_add_stop.handle(event) and len(self.current_editing_emitter.colors) < 5:
                            existing_positions = [s["pos"] for s in self.current_editing_emitter.colors]
                            new_pos = 0.5
                            while new_pos in existing_positions and new_pos < 0.90:
                                new_pos += 0.10
                            self.current_editing_emitter.colors.append({"pos": new_pos, "color": [255, 255, 255]})
                            self.current_editing_emitter.colors.sort(key=lambda s: s["pos"])
                        if self.btn_remove_stop.handle(event) and len(self.current_editing_emitter.colors) > 2:
                            self.current_editing_emitter.colors.pop()
                            
                        if self.btn_grad_flame.handle(event):
                            self.current_editing_emitter.colors = [
                                {"pos": 0.0, "color": [255, 255, 180]},
                                {"pos": 0.4, "color": [255, 120, 0]},
                                {"pos": 1.0, "color": [150, 20, 0]}
                            ]
                        elif self.btn_grad_glacier.handle(event):
                            self.current_editing_emitter.colors = [
                                {"pos": 0.0, "color": [200, 255, 255]},
                                {"pos": 0.5, "color": [50, 150, 255]},
                                {"pos": 1.0, "color": [10, 30, 120]}
                            ]
                        elif self.btn_grad_nebula.handle(event):
                            self.current_editing_emitter.colors = [
                                {"pos": 0.0, "color": [255, 200, 255]},
                                {"pos": 0.5, "color": [180, 50, 255]},
                                {"pos": 1.0, "color": [30, 0, 100]}
                            ]
                        elif self.btn_grad_acid.handle(event):
                            self.current_editing_emitter.colors = [
                                {"pos": 0.0, "color": [220, 255, 100]},
                                {"pos": 0.5, "color": [50, 200, 50]},
                                {"pos": 1.0, "color": [20, 60, 20]}
                            ]
                            
                    elif self.current_editing_emitter.color_mode == "Static":
                        if self.btn_static_color.handle(event):
                            self.picker_stop_idx = 0
                            self.color_picker = ColorPicker(
                                rect=(260, 100, 220, 330),
                                initial_color=tuple(self.current_editing_emitter.colors[0]["color"]),
                                on_confirm=self.confirm_color_picker,
                                on_cancel=self.close_color_picker
                            )
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    hrx = sw - 250
                    main_card = pygame.Rect(hrx + 20, 45, 210, 30)
                    
                    sub_y = 80
                    add_btn_y = sub_y + len(self.preview_emitter.sub_emitters) * 35
                    add_card = pygame.Rect(hrx + 20, add_btn_y, 210, 30)
                    
                    if main_card.collidepoint(event.pos):
                        self.current_editing_emitter.preview_pos = (self.preview_x, self.preview_y)
                        self.current_editing_emitter = self.preview_emitter
                        pos = getattr(self.current_editing_emitter, "preview_pos", None)
                        if pos is None:
                            pos = (sw // 2, sh // 2 - 40)
                            self.current_editing_emitter.preview_pos = pos
                        self.preview_x, self.preview_y = pos
                        self.sync_ui_from_selected()
                    else:
                        clicked_hier = False
                        sub_to_delete = None
                        
                        for idx, sub in enumerate(self.preview_emitter.sub_emitters):
                            card_y = sub_y + idx * 35
                            sub_card = pygame.Rect(hrx + 20, card_y, 210, 30)
                            sub_del_rect = pygame.Rect(hrx + 195, card_y, 35, 30)
                            
                            if sub_del_rect.collidepoint(event.pos):
                                sub_to_delete = sub
                                clicked_hier = True
                                break
                            elif sub_card.collidepoint(event.pos):
                                self.current_editing_emitter.preview_pos = (self.preview_x, self.preview_y)
                                self.current_editing_emitter = sub
                                pos = getattr(self.current_editing_emitter, "preview_pos", None)
                                if pos is None:
                                    pos = (sw // 2, sh // 2 - 40)
                                    self.current_editing_emitter.preview_pos = pos
                                self.preview_x, self.preview_y = pos
                                self.sync_ui_from_selected()
                                clicked_hier = True
                                break
                        
                        if sub_to_delete:
                            if sub_to_delete in self.preview_emitter.sub_emitters:
                                self.preview_emitter.sub_emitters.remove(sub_to_delete)
                            
                            if self.current_editing_emitter == sub_to_delete:
                                self.current_editing_emitter = self.preview_emitter
                                pos = getattr(self.current_editing_emitter, "preview_pos", None)
                                if pos is None:
                                    pos = (sw // 2, sh // 2 - 40)
                                    self.current_editing_emitter.preview_pos = pos
                                self.preview_x, self.preview_y = pos
                                self.sync_ui_from_selected()
                        
                        elif not clicked_hier and add_card.collidepoint(event.pos) and len(self.preview_emitter.sub_emitters) < 6:
                            existing_names = [sub.name for sub in self.preview_emitter.sub_emitters]
                            i = 1
                            while f"sub_{i}" in existing_names:
                                i += 1
                            new_sub_name = f"sub_{i}"
                            new_sub = ParticleEmitter(self.preview_emitter.x, self.preview_emitter.y, new_sub_name)
                            new_sub.is_sub_emitter = True
                            new_sub.rate = 5
                            new_sub.spread = 0.8
                            new_sub.speed = 2.5
                            new_sub.size = 6.0
                            new_sub.lifetime = 25
                            new_sub.particle_style = "spark"
                            new_sub.preview_pos = (self.preview_x, self.preview_y)
                            self.preview_emitter.sub_emitters.append(new_sub)
                            self.current_editing_emitter.preview_pos = (self.preview_x, self.preview_y)
                            self.current_editing_emitter = new_sub
                            self.sync_ui_from_selected()

                if self.btn_presets_gallery.handle(event):
                    self.gallery_open = True
                
                if self.btn_replay_tutorial.handle(event):
                    self.tutorial_active = True
                    self.tutorial_step = 0
                    self.tutorial_prompt = False
                    self.gallery_open = False
                
                if self.btn_apply.handle(event):
                    self.update_from_sliders()
                    self.copy_properties(self.preview_emitter, self.emitter)
                    self.running = False
                elif self.btn_cancel.handle(event):
                    self.running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if preview_area.collidepoint(event.pos):
                        mods = pygame.key.get_mods()
                        if (mods & pygame.KMOD_CTRL):
                            clicked_idx = -1
                            for idx, obs in enumerate(self.preview_obstacles):
                                if obs.rect.collidepoint(event.pos):
                                    clicked_idx = idx
                                    break
                            if clicked_idx >= 0:
                                self.preview_obstacles.pop(clicked_idx)
                            else:
                                grid_size = 40
                                ox = int(round(event.pos[0] / grid_size)) * grid_size - 40
                                oy = int(round(event.pos[1] / grid_size)) * grid_size - 40
                                self.preview_obstacles.append(PreviewObstacle(pygame.Rect(ox, oy, 80, 80)))
                        else:
                            self.drag_origin = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.drag_origin = False
                    
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.preview_x = sw // 2
                    self.preview_y = sh // 2 - 40
                    self.current_editing_emitter.preview_pos = (self.preview_x, self.preview_y)
            
            if self.drag_origin:
                self.preview_x = max(265, min(mx, sw - 265))
                self.preview_y = max(40, min(my, sh - 80))
                self.current_editing_emitter.preview_pos = (self.preview_x, self.preview_y)
            
            self.update_from_sliders()
            if self.current_editing_emitter != self.preview_emitter:
                was_sub = self.current_editing_emitter.is_sub_emitter
                self.current_editing_emitter.is_sub_emitter = False
                self.current_editing_emitter.x = self.preview_x
                self.current_editing_emitter.y = self.preview_y
                self.current_editing_emitter.update(collision_rects=self.preview_obstacles)
            else:
                self.preview_emitter.x = self.preview_x
                self.preview_emitter.y = self.preview_y
                self.preview_emitter.update(collision_rects=self.preview_obstacles)
            
            self.screen.fill(BG_COLOR)
            
            pygame.draw.rect(self.screen, (12, 12, 18), preview_area)
            for gx in range(250, sw - 250, 40):
                pygame.draw.line(self.screen, (20, 20, 28), (gx, 0), (gx, sh - 60))
            for gy in range(0, sh - 60, 40):
                pygame.draw.line(self.screen, (20, 20, 28), (250, gy), (sw - 250, gy))
            for obs in self.preview_obstacles:
                pygame.draw.rect(self.screen, (34, 18, 18), obs.rect, border_radius=6)
                pygame.draw.rect(self.screen, (220, 60, 60), obs.rect, width=2, border_radius=6)
                
            help_surf = self.font_normal.render("[Ctrl + Click] to toggle obstacle blocks", True, (100, 110, 140))
            self.screen.blit(help_surf, (sw - 250 - help_surf.get_width() - 15, 15))
            
            if self.current_editing_emitter != self.preview_emitter:
                self.current_editing_emitter.draw(self.screen, (0, 0), 1.0)
                self.current_editing_emitter.is_sub_emitter = was_sub
            else:
                self.preview_emitter.draw(self.screen, (0, 0), 1.0)
            
            pygame.draw.circle(self.screen, (255, 255, 255), (self.preview_x, self.preview_y), 3)
            pygame.draw.circle(self.screen, ACCENT_BLUE, (self.preview_x, self.preview_y), 7, 1)
            
            pygame.draw.rect(self.screen, PANEL_COLOR, (0, 0, 250, sh))
            pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (250, 0), (250, sh))
            
            self.screen.blit(self.font_title.render("NIAGARA SFX EMITTER", True, (255, 255, 255)), (20, 15))
            self.txt_name.draw(self.screen, self.font_normal)
            self.btn_active.draw(self.screen, self.font_normal)
            
            self.screen.blit(self.font_heading.render("EMITTER MODULES", True, ACCENT_GOLD), (20, 88))
            for i, tab in enumerate(self.module_tabs):
                if self.active_module == i:
                    tab.color = (35, 55, 80)
                    tab.hover_color = (35, 55, 80)
                    tab.text_color = (255, 255, 255)
                else:
                    tab.color = BUTTON_COLOR
                    tab.hover_color = BUTTON_HOVER
                    tab.text_color = TEXT_MUTED
                tab.draw(self.screen, self.font_heading)
                
            pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (20, 260), (230, 260))
            self.screen.blit(self.font_heading.render("MODULE PROPERTIES", True, ACCENT_GOLD), (20, 272))
            
            if self.active_module == 0: # Spawn Module
                self.btn_spawn_mode.draw(self.screen, self.font_heading)
                self.sliders["rate"].draw(self.screen, self.font_normal)
                if self.current_editing_emitter.spawn_mode == "Burst":
                    self.sliders["burst_interval"].draw(self.screen, self.font_normal)
                
                pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (20, 445), (230, 445))
                self.btn_emitter_type.draw(self.screen, self.font_heading)
                if getattr(self.current_editing_emitter, "emitter_type", "Point") in ["Line", "Box"]:
                    self.sliders["spawn_width"].draw(self.screen, self.font_normal)
                if getattr(self.current_editing_emitter, "emitter_type", "Point") == "Box":
                    self.sliders["spawn_height"].draw(self.screen, self.font_normal)
                    
            elif self.active_module == 1: # Particle Init Module (Compact)
                self.sliders["life"].draw(self.screen, self.font_normal)
                self.sliders["speed"].draw(self.screen, self.font_normal)
                self.sliders["spread"].draw(self.screen, self.font_normal)
                self.sliders["size"].draw(self.screen, self.font_normal)
                self.sliders["direction_angle"].draw(self.screen, self.font_normal)
                self.sliders["preview_scale"].draw(self.screen, self.font_normal)
                
                self.screen.blit(self.font_normal.render("Custom Sprite Asset Name:", True, TEXT_MUTED), (20, 620))
                self.txt_sprite.draw(self.screen, self.font_normal)
                
            elif self.active_module == 2: 
                self.sliders["friction"].draw(self.screen, self.font_normal)
                self.btn_open_add_module.draw(self.screen, self.font_heading)
                
                y_offset = 375
                for idx, mod in enumerate(self.current_editing_emitter.active_modules):
                    m_id = mod["id"]
                    enabled = mod["enabled"]
                    has_slider = m_id in ["gravity", "wind", "vortex", "chaos"]
                    if m_id == "collision":
                        card_h = 165
                    else:
                        card_h = 48 if has_slider else 30
                    
                    card_rect = pygame.Rect(20, y_offset, 210, card_h)
                    pygame.draw.rect(self.screen, (26, 28, 38), card_rect, border_radius=4)
                    border_color = ACCENT_BLUE if enabled else PANEL_BORDER_COLOR
                    pygame.draw.rect(self.screen, border_color, card_rect, width=1, border_radius=4)
                    
                    cb_rect = pygame.Rect(25, y_offset + 8, 14, 14)
                    pygame.draw.rect(self.screen, (16, 16, 24), cb_rect, border_radius=3)
                    if enabled:
                        pygame.draw.rect(self.screen, ACCENT_GREEN, cb_rect.inflate(-4, -4), border_radius=2)
                        
                    self.screen.blit(self.font_heading.render(m_id.capitalize(), True, TEXT_COLOR if enabled else TEXT_MUTED), (45, y_offset + 6))
                    
                    del_rect = pygame.Rect(205, y_offset + 6, 18, 18)
                    pygame.draw.rect(self.screen, (40, 24, 28), del_rect, border_radius=3)
                    self.screen.blit(self.font_normal.render("x", True, ACCENT_RED), (211, y_offset + 2))
                    
                    if has_slider:
                        val = mod.get(m_id, 0.0)
                        if m_id in ["gravity", "wind", "vortex"]:
                            factor = (val - (-0.5)) / (0.5 - (-0.5))
                        else: # chaos
                            factor = val
                        factor = max(0.0, min(1.0, factor))
                        
                        track_rect = pygame.Rect(45, y_offset + 28, 120, 6)
                        pygame.draw.rect(self.screen, (16, 16, 24), track_rect, border_radius=3)
                        
                        progress_w = int(track_rect.w * factor)
                        if progress_w > 0:
                            pygame.draw.rect(self.screen, ACCENT_BLUE if enabled else TEXT_MUTED, (track_rect.x, track_rect.y, progress_w, track_rect.h), border_radius=3)
                        
                        tx = track_rect.x + progress_w
                        pygame.draw.circle(self.screen, (255, 255, 255) if enabled else TEXT_MUTED, (tx, track_rect.y + 3), 4)
                        
                        val_txt = self.font_normal.render(f"{val:.2f}", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(val_txt, (180, y_offset + 24))
                    if m_id == "collision":
                        target_val = mod.get("target", "All")
                        btn_rect = pygame.Rect(45, y_offset + 24, 150, 18)
                        pygame.draw.rect(self.screen, (32, 34, 48), btn_rect, border_radius=4)
                        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, btn_rect, width=1, border_radius=4)
                        btn_txt = self.font_normal.render(f"Target: {target_val}", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(btn_txt, (btn_rect.x + 8, btn_rect.y + 3))
                        
                        bounce_val = mod.get("bounce", True)
                        b_cb = pygame.Rect(45, y_offset + 48, 14, 14)
                        pygame.draw.rect(self.screen, (16, 16, 24), b_cb, border_radius=3)
                        if bounce_val:
                            pygame.draw.rect(self.screen, ACCENT_BLUE if enabled else TEXT_MUTED, b_cb.inflate(-4, -4), border_radius=2)
                        b_txt = self.font_normal.render("Bounce", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(b_txt, (65, y_offset + 48))
                        
                        kill_val = mod.get("kill_on_collision", False)
                        k_cb = pygame.Rect(135, y_offset + 48, 14, 14)
                        pygame.draw.rect(self.screen, (16, 16, 24), k_cb, border_radius=3)
                        if kill_val:
                            pygame.draw.rect(self.screen, ACCENT_BLUE if enabled else TEXT_MUTED, k_cb.inflate(-4, -4), border_radius=2)
                        k_txt = self.font_normal.render("Kill on hit", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(k_txt, (155, y_offset + 48))
                        
                        sparks_val = mod.get("add_particles", True)
                        s_cb = pygame.Rect(45, y_offset + 68, 14, 14)
                        pygame.draw.rect(self.screen, (16, 16, 24), s_cb, border_radius=3)
                        if sparks_val:
                            pygame.draw.rect(self.screen, ACCENT_BLUE if enabled else TEXT_MUTED, s_cb.inflate(-4, -4), border_radius=2)
                        s_txt = self.font_normal.render("Default Sparks", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(s_txt, (65, y_offset + 68))
                        
                        trigger_val = mod.get("collision_trigger_emitter", "None")
                        trig_btn_rect = pygame.Rect(45, y_offset + 88, 115, 18)
                        pygame.draw.rect(self.screen, (32, 34, 48), trig_btn_rect, border_radius=4)
                        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, trig_btn_rect, width=1, border_radius=4)
                        trig_txt = self.font_normal.render(f"Trig: {trigger_val}", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(trig_txt, (trig_btn_rect.x + 8, trig_btn_rect.y + 3))

                        create_btn_rect = pygame.Rect(165, y_offset + 88, 30, 18)
                        pygame.draw.rect(self.screen, (22, 48, 36) if enabled else (32, 32, 32), create_btn_rect, border_radius=4)
                        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, create_btn_rect, width=1, border_radius=4)
                        create_txt = self.font_normal.render("+", True, (60, 220, 130) if enabled else TEXT_MUTED)
                        self.screen.blit(create_txt, (create_btn_rect.x + 10, create_btn_rect.y + 2))

                        splash_style = mod.get("splash_style", "spark")
                        style_btn_rect = pygame.Rect(45, y_offset + 108, 150, 18)
                        pygame.draw.rect(self.screen, (32, 34, 48), style_btn_rect, border_radius=4)
                        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, style_btn_rect, width=1, border_radius=4)
                        style_txt = self.font_normal.render(f"Splash: {splash_style.capitalize()}", True, TEXT_COLOR if enabled else TEXT_MUTED)
                        self.screen.blit(style_txt, (style_btn_rect.x + 8, style_btn_rect.y + 3))

                        scount = mod.get("splash_count", 3)
                        track_rect_count = pygame.Rect(45, y_offset + 132, 110, 6)
                        pygame.draw.rect(self.screen, (16, 16, 24), track_rect_count, border_radius=3)
                        factor_c = (scount - 1) / 7.0
                        progress_w_c = int(track_rect_count.w * factor_c)
                        if progress_w_c > 0:
                            pygame.draw.rect(self.screen, ACCENT_BLUE if enabled else TEXT_MUTED, (track_rect_count.x, track_rect_count.y, progress_w_c, track_rect_count.h), border_radius=3)
                        pygame.draw.circle(self.screen, (255, 255, 255) if enabled else TEXT_MUTED, (track_rect_count.x + progress_w_c, track_rect_count.y + 3), 4)
                        self.screen.blit(self.font_normal.render(f"Qty: {scount}", True, TEXT_COLOR if enabled else TEXT_MUTED), (165, y_offset + 128))

                        sspeed = mod.get("splash_speed", 2.0)
                        track_rect_speed = pygame.Rect(45, y_offset + 152, 110, 6)
                        pygame.draw.rect(self.screen, (16, 16, 24), track_rect_speed, border_radius=3)
                        factor_s = (sspeed - 0.5) / 4.5
                        progress_w_s = int(track_rect_speed.w * factor_s)
                        if progress_w_s > 0:
                            pygame.draw.rect(self.screen, ACCENT_BLUE if enabled else TEXT_MUTED, (track_rect_speed.x, track_rect_speed.y, progress_w_s, track_rect_speed.h), border_radius=3)
                        pygame.draw.circle(self.screen, (255, 255, 255) if enabled else TEXT_MUTED, (track_rect_speed.x + progress_w_s, track_rect_speed.y + 3), 4)
                        self.screen.blit(self.font_normal.render(f"Spd: {sspeed:.1f}", True, TEXT_COLOR if enabled else TEXT_MUTED), (165, y_offset + 148))
                        
                    y_offset += card_h + 8
                    
            elif self.active_module == 3: # Color Module
                self.btn_color_mode.draw(self.screen, self.font_heading)
                if self.current_editing_emitter.color_mode == "Lerp":
                    pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, (20, 345, 210, 20), border_radius=4)
                    if len(self.current_editing_emitter.colors) >= 2:
                        grad_surf = pygame.Surface((100, 1))
                        stops = sorted(self.current_editing_emitter.colors, key=lambda s: s["pos"])
                        for x_pixel in range(100):
                            t = x_pixel / 99.0
                            col = self.interpolate_color_stops(stops, t)
                            grad_surf.set_at((x_pixel, 0), col)
                        scaled_grad = pygame.transform.smoothscale(grad_surf, (210, 20))
                        self.screen.blit(scaled_grad, (20, 345))
                        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, (20, 345, 210, 20), width=1, border_radius=4)
                    
                    for idx, stop in enumerate(self.current_editing_emitter.colors):
                        p = stop["pos"]
                        px = 20 + p * 210
                        pygame.draw.circle(self.screen, tuple(stop["color"]), (px, 375), 6)
                        border_c = (255, 255, 255) if idx == self.dragged_stop_idx else PANEL_BORDER_COLOR
                        pygame.draw.circle(self.screen, border_c, (px, 375), 6, 1)
                        
                    self.btn_add_stop.draw(self.screen, self.font_heading)
                    self.btn_remove_stop.draw(self.screen, self.font_heading)
                    
                    self.screen.blit(self.font_normal.render("Quick Gradient Presets:", True, TEXT_MUTED), (20, 440))
                    self.btn_grad_flame.draw(self.screen, self.font_normal)
                    self.btn_grad_glacier.draw(self.screen, self.font_normal)
                    self.btn_grad_nebula.draw(self.screen, self.font_normal)
                    self.btn_grad_acid.draw(self.screen, self.font_normal)
                    
                elif self.current_editing_emitter.color_mode == "Static":
                    static_col = tuple(self.current_editing_emitter.colors[0]["color"])
                    self.btn_static_color.color = static_col
                    self.btn_static_color.hover_color = static_col
                    self.btn_static_color.text = "Set Static Color"
                    self.btn_static_color.draw(self.screen, self.font_heading)
            
            if self.active_module == 1:
                self.btn_style.draw(self.screen)
                self.btn_size_mode.draw(self.screen)
            
            rx = sw - 250
            pygame.draw.rect(self.screen, PANEL_COLOR, (rx, 0, 250, sh))
            pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (rx, 0), (rx, sh))
            
            self.screen.blit(self.font_title.render("VFX HIERARCHY", True, ACCENT_GOLD), (rx + 20, 15))
            
            main_selected = (self.current_editing_emitter == self.preview_emitter)
            main_card = pygame.Rect(rx + 20, 45, 210, 30)
            pygame.draw.rect(self.screen, (35, 55, 80) if main_selected else (20, 22, 32), main_card, border_radius=4)
            pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, main_card, width=1, border_radius=4)
            self.screen.blit(self.font_heading.render(self.preview_emitter.name, True, TEXT_COLOR), (rx + 30, 52))
            
            sub_y = 80
            for idx, sub in enumerate(self.preview_emitter.sub_emitters):
                card_y = sub_y + idx * 35
                sub_selected = (self.current_editing_emitter == sub)
                sub_card = pygame.Rect(rx + 20, card_y, 210, 30)
                pygame.draw.rect(self.screen, (35, 55, 80) if sub_selected else (20, 22, 32), sub_card, border_radius=4)
                pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, sub_card, width=1, border_radius=4)
                
                pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (rx + 28, card_y - 10), (rx + 28, card_y + 15))
                pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (rx + 28, card_y + 15), (rx + 38, card_y + 15))
                
                self.screen.blit(self.font_normal.render(sub.name, True, TEXT_COLOR), (rx + 42, card_y + 7))
                
                sub_del_rect = pygame.Rect(rx + 202, card_y + 6, 18, 18)
                pygame.draw.rect(self.screen, (40, 24, 28), sub_del_rect, border_radius=3)
                x_text = self.font_normal.render("x", True, ACCENT_RED)
                self.screen.blit(x_text, (rx + 202 + (18 - x_text.get_width()) // 2, card_y + 6 + (18 - x_text.get_height()) // 2 - 2))
                
            add_btn_y = sub_y + len(self.preview_emitter.sub_emitters) * 35
            add_card = pygame.Rect(rx + 20, add_btn_y, 210, 30)
            is_hover_add = add_card.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (30, 42, 60) if is_hover_add else (24, 28, 40), add_card, border_radius=4)
            pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, add_card, width=1, border_radius=4)
            self.screen.blit(self.font_heading.render("+ Add Sub-Emitter", True, TEXT_COLOR if is_hover_add else TEXT_MUTED), (rx + 45, add_btn_y + 6))
            
            self.btn_presets_gallery.draw(self.screen, self.font_heading)
            self.btn_replay_tutorial.draw(self.screen, self.font_heading)
                
            guide_y = sh - 170
            pygame.draw.rect(self.screen, (16, 16, 24), (rx + 20, guide_y, 210, 100), border_radius=6)
            pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, (rx + 20, guide_y, 210, 100), width=1, border_radius=6)
            self.screen.blit(self.font_heading.render("VIEWPORT CONTROLS", True, ACCENT_GOLD), (rx + 30, guide_y + 10))
            self.screen.blit(self.font_normal.render("- Left-Click + Drag inside viewport:", True, TEXT_COLOR), (rx + 30, guide_y + 35))
            self.screen.blit(self.font_normal.render("  Move Emitter source location", True, TEXT_MUTED), (rx + 30, guide_y + 50))
            self.screen.blit(self.font_normal.render("- Press [R]: Reset to center", True, TEXT_COLOR), (rx + 30, guide_y + 75))
            
            by = sh - 60
            pygame.draw.rect(self.screen, PANEL_COLOR, (250, by, sw - 500, 60))
            pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (250, by), (sw - 250, by))
            
            self.btn_apply.draw(self.screen, self.font_heading)
            self.btn_cancel.draw(self.screen, self.font_heading)
            
            reg_str = " | REGULE" if self.fps_throttled else " | PERF OK"
            reg_color = (230, 100, 100) if self.fps_throttled else (60, 220, 130)
            stats_surf = self.font_normal.render(f"Particles: {len(self.preview_emitter.particles)} | FPS: {fps:.0f}", True, TEXT_MUTED)
            reg_surf = self.font_normal.render(reg_str, True, reg_color)
            self.screen.blit(stats_surf, (260, 10))
            self.screen.blit(reg_surf, (260 + stats_surf.get_width(), 10))
            
            if self.color_picker is not None:
                self.color_picker.draw(self.screen)
                
            if self.gallery_open:
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((10, 10, 15, 200))
                self.screen.blit(overlay, (0, 0))
                
                modal_w, modal_h = 740, 360
                modal_x = (sw - modal_w) // 2
                modal_y = (sh - modal_h) // 2
                modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
                
                s_surf = pygame.Surface((modal_w + 10, modal_h + 10), pygame.SRCALPHA)
                s_surf.fill((0, 0, 0, 60))
                self.screen.blit(s_surf, (modal_x - 5, modal_y - 5))
                
                pygame.draw.rect(self.screen, (18, 18, 28), modal_rect, border_radius=12)
                pygame.draw.rect(self.screen, (60, 62, 85), modal_rect, width=2, border_radius=12)
                
                self.screen.blit(self.font_title.render("PRESETS GALLERY - LIVE SIMULATIONS", True, (255, 255, 255)), (modal_x + 20, modal_y + 15))
                
                close_rect = pygame.Rect(modal_x + modal_w - 35, modal_y + 12, 22, 22)
                pygame.draw.rect(self.screen, (40, 24, 28), close_rect, border_radius=4)
                self.screen.blit(self.font_heading.render("X", True, ACCENT_RED), (modal_x + modal_w - 28, modal_y + 14))
                
                presets_list = ["fire", "snow", "spark", "bubble", "portal", "fireball", "starfield", "rain", "laser", "lightning"]
                
                prev_rect = pygame.Rect(modal_x + 15, modal_y + 165, 24, 30)
                next_rect = pygame.Rect(modal_x + modal_w - 39, modal_y + 165, 24, 30)
                
                if self.gallery_page > 0:
                    is_prev_hover = prev_rect.collidepoint((mx, my))
                    arrow_col = ACCENT_GOLD if is_prev_hover else TEXT_MUTED
                    pygame.draw.line(self.screen, arrow_col, (modal_x + 28, modal_y + 165), (modal_x + 18, modal_y + 180), 3)
                    pygame.draw.line(self.screen, arrow_col, (modal_x + 18, modal_y + 180), (modal_x + 28, modal_y + 195), 3)
                    
                if self.gallery_page < 2:
                    is_next_hover = next_rect.collidepoint((mx, my))
                    arrow_col = ACCENT_GOLD if is_next_hover else TEXT_MUTED
                    pygame.draw.line(self.screen, arrow_col, (modal_x + modal_w - 28, modal_y + 165), (modal_x + modal_w - 18, modal_y + 180), 3)
                    pygame.draw.line(self.screen, arrow_col, (modal_x + modal_w - 18, modal_y + 180), (modal_x + modal_w - 28, modal_y + 195), 3)

                for dot_idx in range(3):
                    dot_x = modal_x + modal_w // 2 - 20 + dot_idx * 20
                    dot_y = modal_y + modal_h - 22
                    dot_color = ACCENT_GOLD if self.gallery_page == dot_idx else (45, 48, 68)
                    try:
                        pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y), 4, antialiased=True)
                    except TypeError:
                        pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y), 4)

                start_idx = self.gallery_page * 4
                end_idx = min(start_idx + 4, len(presets_list))
                
                for local_idx in range(start_idx, end_idx):
                    p_name = presets_list[local_idx]
                    idx_on_page = local_idx - start_idx
                    card_x = modal_x + 60 + idx_on_page * 160
                    card_y = modal_y + 70
                    card_rect = pygame.Rect(card_x, card_y, 140, 240)
                    
                    is_hover = card_rect.collidepoint((mx, my))
                    bg_col = (26, 28, 42) if is_hover else (22, 23, 34)
                    border_col = ACCENT_BLUE if is_hover else PANEL_BORDER_COLOR
                    
                    pygame.draw.rect(self.screen, bg_col, card_rect, border_radius=8)
                    pygame.draw.rect(self.screen, border_col, card_rect, width=2 if is_hover else 1, border_radius=8)
                    
                    clip_rect = pygame.Rect(card_x + 2, card_y + 2, 136, 148)
                    
                    em = self.gallery_emitters[p_name]
                    em.x = card_x + 70
                    if p_name in ["rain", "laser", "lightning"]:
                        em.y = card_y + 20
                    else:
                        em.y = card_y + 80
                    
                    em.update()
                    
                    old_clip = self.screen.get_clip()
                    self.screen.set_clip(clip_rect)
                    em.draw(self.screen, (0, 0), 1.0)
                    self.screen.set_clip(old_clip)
                    
                    pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (card_x, card_y + 152), (card_x + 140, card_y + 152))
                    
                    label_titles = {
                        "fire": "Fire/Flame",
                        "snow": "Snow/Bliz",
                        "spark": "Neon Spark",
                        "bubble": "Tox Bubble",
                        "portal": "Portal E.",
                        "fireball": "Fireball",
                        "starfield": "Starfield",
                        "rain": "Rain",
                        "laser": "Death Beam",
                        "lightning": "Lightning"
                    }
                    lbl_text = label_titles.get(p_name, p_name.capitalize())
                    lbl_surf = self.font_heading.render(lbl_text, True, (255, 255, 255) if is_hover else TEXT_COLOR)
                    self.screen.blit(lbl_surf, (card_x + (140 - lbl_surf.get_width()) // 2, card_y + 165))
                    
                    desc_dict = {
                        "fire": "Flame drift",
                        "snow": "Snow drift",
                        "spark": "Gravity line",
                        "bubble": "Colliding",
                        "portal": "Vortex field",
                        "fireball": "Comet trail",
                        "starfield": "Cosmic twink",
                        "rain": "Sub-emit splash",
                        "laser": "Wall reflection",
                        "lightning": "Zigzag arc glow"
                    }
                    desc_surf = self.font_normal.render(desc_dict.get(p_name, ""), True, TEXT_MUTED)
                    self.screen.blit(desc_surf, (card_x + (140 - desc_surf.get_width()) // 2, card_y + 195))

            if self.add_module_open:
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((10, 10, 15, 200))
                self.screen.blit(overlay, (0, 0))
                
                modal_w, modal_h = 400, 450
                modal_x = (sw - modal_w) // 2
                modal_y = (sh - modal_h) // 2
                modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
                
                s_surf = pygame.Surface((modal_w + 10, modal_h + 10), pygame.SRCALPHA)
                s_surf.fill((0, 0, 0, 60))
                self.screen.blit(s_surf, (modal_x - 5, modal_y - 5))
                
                pygame.draw.rect(self.screen, (18, 18, 28), modal_rect, border_radius=10)
                pygame.draw.rect(self.screen, (60, 62, 85), modal_rect, width=2, border_radius=10)
                
                self.screen.blit(self.font_title.render("ADD FORCE MODULE", True, (255, 255, 255)), (modal_x + 20, modal_y + 15))
                
                close_rect = pygame.Rect(modal_x + modal_w - 35, modal_y + 12, 22, 22)
                pygame.draw.rect(self.screen, (40, 24, 28), close_rect, border_radius=4)
                self.screen.blit(self.font_heading.render("X", True, ACCENT_RED), (modal_x + modal_w - 28, modal_y + 14))
                
                self.txt_module_search.draw(self.screen, self.font_normal)
                if self.txt_module_search.val == "" and not self.txt_module_search.active:
                    watermark = self.font_normal.render("Search forces (e.g. gravity, collision)...", True, TEXT_MUTED)
                    self.screen.blit(watermark, (self.txt_module_search.rect.x + 8, self.txt_module_search.rect.y + 6))
                
                query = self.txt_module_search.val.lower()
                filtered = [m for m in self.modules_info if query in m["name"].lower() or query in m["desc"].lower()]
                
                row_y = modal_y + 90
                for mod in filtered:
                    is_added = any(m["id"] == mod["id"] for m in self.preview_emitter.active_modules)
                    
                    row_rect = pygame.Rect(modal_x + 20, row_y, 360, 42)
                    pygame.draw.rect(self.screen, (24, 25, 37), row_rect, border_radius=6)
                    pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, row_rect, width=1, border_radius=6)
                    
                    self.screen.blit(self.font_heading.render(mod["name"], True, (255, 255, 255)), (modal_x + 32, row_y + 4))
                    self.screen.blit(self.font_normal.render(mod["desc"], True, TEXT_MUTED), (modal_x + 32, row_y + 22))
                    
                    add_btn = pygame.Rect(modal_x + 300, row_y + 11, 70, 20)
                    if is_added:
                        pygame.draw.rect(self.screen, (32, 34, 48), add_btn, border_radius=4)
                        btn_txt = self.font_normal.render("Added", True, TEXT_MUTED)
                    else:
                        is_hover = add_btn.collidepoint((mx, my))
                        bg_c = ACCENT_GREEN if is_hover else (32, 45, 68)
                        pygame.draw.rect(self.screen, bg_c, add_btn, border_radius=4)
                        btn_txt = self.font_normal.render("+ Add", True, (15, 30, 20) if is_hover else ACCENT_GREEN)
                        
                    self.screen.blit(btn_txt, (add_btn.x + (70 - btn_txt.get_width()) // 2, add_btn.y + 3))
                    
                    row_y += 50

            if self.tutorial_prompt:
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((10, 10, 15, 160))
                self.screen.blit(overlay, (0, 0))
                
                dialog_w, dialog_h = 420, 160
                dialog_x = (sw - dialog_w) // 2
                dialog_y = (sh - dialog_h) // 2
                dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
                
                pygame.draw.rect(self.screen, (10, 11, 16), dialog_rect, border_radius=10)
                pygame.draw.rect(self.screen, ACCENT_BLUE, dialog_rect, width=2, border_radius=10)
                
                title_surf = self.font_title.render("TUTORIEL PARTICULES", True, ACCENT_GOLD)
                body_line1 = self.font_heading.render("Bienvenue dans le Playground VFX !", True, (255, 255, 255))
                body_line2 = self.font_tutorial_body.render("Souhaitez-vous suivre un court guide interactif", True, (255, 255, 255))
                body_line3 = self.font_tutorial_body.render("pour apprendre à configurer vos effets ?", True, (255, 255, 255))
                
                self.screen.blit(title_surf, (dialog_x + 20, dialog_y + 15))
                self.screen.blit(body_line1, (dialog_x + 20, dialog_y + 45))
                self.screen.blit(body_line2, (dialog_x + 20, dialog_y + 72))
                self.screen.blit(body_line3, (dialog_x + 20, dialog_y + 92))
                
                self.btn_tut_yes = pygame.Rect(dialog_x + 20, dialog_y + 120, 170, 26)
                self.btn_tut_no = pygame.Rect(dialog_x + 230, dialog_y + 120, 170, 26)
                
                is_hover_yes = self.btn_tut_yes.collidepoint((mx, my))
                yes_col = (30, 80, 45) if is_hover_yes else (22, 48, 36)
                pygame.draw.rect(self.screen, yes_col, self.btn_tut_yes, border_radius=4)
                yes_txt = self.font_heading.render("Commencer le guide", True, (60, 220, 130))
                self.screen.blit(yes_txt, yes_txt.get_rect(center=self.btn_tut_yes.center))
                
                is_hover_no = self.btn_tut_no.collidepoint((mx, my))
                no_col = (80, 30, 45) if is_hover_no else (42, 24, 28)
                pygame.draw.rect(self.screen, no_col, self.btn_tut_no, border_radius=4)
                no_txt = self.font_heading.render("Plus tard", True, (230, 100, 100))
                self.screen.blit(no_txt, no_txt.get_rect(center=self.btn_tut_no.center))
                
            elif self.tutorial_active:
                if self.tutorial_step == 1:
                    self.active_module = 0
                elif self.tutorial_step == 3:
                    self.active_module = 1
                elif self.tutorial_step == 4:
                    self.active_module = 2
                elif self.tutorial_step == 5:
                    self.active_module = 3
                    
                highlight_rect = None
                if self.tutorial_step == 1:
                    highlight_rect = pygame.Rect(20, 115, 210, 30)
                elif self.tutorial_step == 2:
                    rx = sw - 230
                    highlight_rect = pygame.Rect(rx, 45, 210, 300)
                elif self.tutorial_step == 3:
                    highlight_rect = pygame.Rect(20, 150, 210, 30)
                elif self.tutorial_step == 4:
                    highlight_rect = pygame.Rect(20, 185, 210, 30)
                elif self.tutorial_step == 5:
                    highlight_rect = pygame.Rect(20, 220, 210, 30)
                elif self.tutorial_step == 6:
                    highlight_rect = pygame.Rect(sw - 230, 15, 210, 25)
                    
                if highlight_rect:
                    pulse = int(127 + 127 * math.sin(time.time() * 7))
                    pygame.draw.rect(self.screen, (pulse, 200, pulse), highlight_rect, width=3, border_radius=5)
                    
                box_w, box_h = 440, 140
                box_x = (sw - box_w) // 2
                box_y = sh - 200
                box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
                
                pygame.draw.rect(self.screen, (10, 11, 16), box_rect, border_radius=8)
                pygame.draw.rect(self.screen, ACCENT_BLUE, box_rect, width=2, border_radius=8)
                
                steps_desc = [
                    ("1/8 - PLAYGROUND VFX",
                     "Bienvenue dans le guide du Playground VFX !",
                     "Déplacez l'émetteur en le glissant avec la souris.",
                     "Ctrl + Clic ajoute ou supprime des obstacles."),
                    ("2/8 - ONGLET SPAWN",
                     "ONGLET SPAWN : Règle le mode d'émission,",
                     "le taux (Spawn Rate) et la géométrie de zone",
                     "pour régler le flux et la dispersion."),
                    ("3/8 - HIÉRARCHIE (A DROITE)",
                     "HIÉRARCHIE (A Droite) : Créez et gérez vos sous-émetteurs.",
                     "Sélectionnez un sous-émetteur pour l'éditer en isolation",
                     "et le positionner indépendamment dans la scène !"),
                    ("4/8 - INITIALISATION",
                     "ONGLET INIT : Règle la durée de vie, la vitesse,",
                     "la direction, la taille et le style graphique",
                     "(Cercle, Neige, Fireball, Laser, Éclair, etc.)."),
                    ("5/8 - PHYSIQUE & COLLISIONS",
                     "ONGLET PHYSIQUE : Ajoute Gravité/Vent/Vortex/Chaos.",
                     "Configurez les collisions avec rebonds ou",
                     "déclenchez vos sous-émetteurs."),
                    ("6/8 - MODULE COULEURS",
                     "ONGLET COULEUR : Personnalise le rendu des couleurs",
                     "(Statique, Arc-en-ciel, ou dégradés)",
                     "en glissant ou ajoutant des points de couleur."),
                    ("7/8 - GALERIE PRESETS",
                     "PRESETS (Haut Droite) : Charge instantanément",
                     "des presets de base (Pluie, Lasers, Éclairs) depuis",
                     "la galerie de presets."),
                    ("8/8 - ENREGISTREMENT",
                     "C'est terminé ! Cliquez sur 'Apply to Level' en bas",
                     "pour sauvegarder l'effet et ses sous-émetteurs.",
                     "Bonne création !")
                ]
                
                title, line1, line2, line3 = steps_desc[self.tutorial_step]
                title_surf = self.font_tutorial_title.render(title, True, ACCENT_GOLD)
                l1_surf = self.font_tutorial_body.render(line1, True, (255, 255, 255))
                l2_surf = self.font_tutorial_body.render(line2, True, (255, 255, 255))
                l3_surf = self.font_tutorial_body.render(line3, True, (255, 255, 255))
                
                self.screen.blit(title_surf, (box_x + 15, box_y + 12))
                self.screen.blit(l1_surf, (box_x + 15, box_y + 38))
                self.screen.blit(l2_surf, (box_x + 15, box_y + 60))
                self.screen.blit(l3_surf, (box_x + 15, box_y + 82))
                
                self.btn_tut_next = pygame.Rect(box_x + box_w - 95, box_y + box_h - 32, 85, 24)
                is_hover_next = self.btn_tut_next.collidepoint((mx, my))
                next_col = ACCENT_GOLD if is_hover_next else (32, 45, 68)
                pygame.draw.rect(self.screen, next_col, self.btn_tut_next, border_radius=4)
                next_txt_str = "TERMINER" if self.tutorial_step == 7 else "SUIVANT >"
                next_txt_col = (15, 15, 20) if is_hover_next else ACCENT_GOLD
                next_txt = self.font_normal.render(next_txt_str, True, next_txt_col)
                self.screen.blit(next_txt, next_txt.get_rect(center=self.btn_tut_next.center))
                
                self.btn_tut_skip = pygame.Rect(box_x + 15, box_y + box_h - 32, 85, 24)
                is_hover_skip = self.btn_tut_skip.collidepoint((mx, my))
                skip_col = ACCENT_RED if is_hover_skip else (40, 24, 28)
                pygame.draw.rect(self.screen, skip_col, self.btn_tut_skip, border_radius=4)
                skip_txt = self.font_normal.render("PASSER", True, (255, 255, 255) if is_hover_skip else ACCENT_RED)
                self.screen.blit(skip_txt, skip_txt.get_rect(center=self.btn_tut_skip.center))

            dt = self.clock.tick(60) / 1000.0
            if self.nm:
                self.nm.update(dt)
                self.nm.draw(self.screen)
            pygame.display.flip()
            
        while pygame.mouse.get_pressed()[0]:
            pygame.event.pump()
            pygame.time.delay(10)
            
        pygame.event.clear([pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION])