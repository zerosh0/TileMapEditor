import pygame
import random
import math
import time
from pathlib import Path

SPRITE_SHEET_CACHE = {}

class AnimatedSpriteSheet:
    def __init__(self, json_path, image_path, colorkey=(0, 0, 0)):
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.meta = data.get("meta", {})
        self.frame_w = self.meta.get("frameSize", {}).get("w", 32)
        self.frame_h = self.meta.get("frameSize", {}).get("h", 32)
        self.frames = []
        img = pygame.image.load(str(image_path)).convert()
        frames_dict = data.get("frames", {})
        keys = sorted(frames_dict.keys())
        for k in keys:
            fr = frames_dict[k]["frame"]
            sx, sy, sw, sh = fr["x"], fr["y"], fr["w"], fr["h"]
            surf = pygame.Surface((sw, sh))
            surf.blit(img, (0, 0), (sx, sy, sw, sh))
            surf.set_colorkey(colorkey)
            surf = surf.convert_alpha()
            self.frames.append(surf)

    def get_frame(self, idx):
        if not self.frames:
            return None
        return self.frames[int(idx) % len(self.frames)]

    def n_frames(self):
        return len(self.frames)


def get_spritesheet(json_path, image_path):
    key = (str(json_path), str(image_path))
    if key not in SPRITE_SHEET_CACHE:
        try:
            p_json = Path(json_path)
            p_img = Path(image_path)
            if p_json.exists() and p_img.exists():
                SPRITE_SHEET_CACHE[key] = AnimatedSpriteSheet(p_json, p_img)
            else:
                alt_json = Path(__file__).resolve().parents[2] / "Assets" / "particles" / p_json.name
                alt_img = Path(__file__).resolve().parents[2] / "Assets" / "particles" / p_img.name
                if alt_json.exists() and alt_img.exists():
                    SPRITE_SHEET_CACHE[key] = AnimatedSpriteSheet(alt_json, alt_img)
                else:
                    SPRITE_SHEET_CACHE[key] = None
        except Exception as e:
            print(f"Error loading spritesheet {key}: {e}")
            SPRITE_SHEET_CACHE[key] = None
    return SPRITE_SHEET_CACHE[key]


class Particle:
    def __init__(self, x, y, vx, vy, life, size, colors, style="circle", size_mode="Constant", custom_sprite="", is_sub=False):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.size = size
        self.colors = colors # List of {"pos": float, "color": [r,g,b]}
        self.style = style
        self.size_mode = size_mode
        self.custom_sprite = custom_sprite
        self.frame_index = random.uniform(0, 5)
        self.is_sub = is_sub

    def update(self, emitter_pos, active_modules, friction, parent_list=None, collision_rects=None, player_rect=None):
        ex, ey = emitter_pos
        self.vx *= friction
        self.vy *= friction
        
        gravity_val = 0.0
        chaos_val = 0.0
        vortex_val = 0.0
        wind_val = 0.0
        collision_enabled = False
        collision_target = "All"
        trail_enabled = False
        explode_enabled = False
        
        for mod in active_modules:
            if not mod.get("enabled", True):
                continue
            m_id = mod.get("id")
            if m_id == "gravity":
                gravity_val = mod.get("gravity", 0.1)
            elif m_id == "chaos":
                chaos_val = mod.get("chaos", 0.05)
            elif m_id == "vortex":
                vortex_val = mod.get("vortex", 0.05)
            elif m_id == "wind":
                wind_val = mod.get("wind", 0.05)
            elif m_id == "collision":
                collision_enabled = True
                collision_target = mod.get("target", "All")
            elif m_id == "trail":
                trail_enabled = True
            elif m_id == "explosion":
                explode_enabled = True

        # Apply chaos drift
        if chaos_val > 0.0:
            self.vx += random.uniform(-chaos_val, chaos_val)
            self.vy += random.uniform(-chaos_val, chaos_val)

        # Apply gravity & wind forces
        self.vy += gravity_val
        self.vx += wind_val
        
        # Apply vortex swirl
        if vortex_val != 0.0:
            dx = self.x - ex
            dy = self.y - ey
            dist = math.sqrt(dx*dx + dy*dy) + 0.001
            tx = -dy / dist
            ty = dx / dist
            self.vx += tx * vortex_val - (dx / dist) * 0.03
            self.vy += ty * vortex_val - (dy / dist) * 0.03

        if self.style == "snow":
            sway = math.sin(self.life * 0.05 + self.frame_index) * 0.3
            self.x += self.vx + sway
            self.y += self.vy
        else:
            self.x += self.vx
            self.y += self.vy

        if collision_enabled:
            left, right = ex - 600, ex + 600
            top, bottom = ey - 600, ey + 600
            if self.x < left:
                self.x = left
                self.vx = -self.vx * 0.6
            elif self.x > right:
                self.x = right
                self.vx = -self.vx * 0.6
            if self.y < top:
                self.y = top
                self.vy = -self.vy * 0.6
            elif self.y > bottom:
                self.y = bottom
                self.vy = -self.vy * 0.6

            if collision_target in ["All", "Collisions Only"] and collision_rects is not None:
                p_rect = pygame.Rect(self.x - 2, self.y - 2, 4, 4)
                for c_obj in collision_rects:
                    if getattr(c_obj, "type", "") != "collision":
                        continue
                    r = c_obj.rect
                    if r.colliderect(p_rect):
                        overlap_left = self.x - r.left
                        overlap_right = r.right - self.x
                        overlap_top = self.y - r.top
                        overlap_bottom = r.bottom - self.y
                        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                        if min_overlap == overlap_left:
                            self.x = r.left - 2
                            self.vx = -abs(self.vx) * 0.6
                        elif min_overlap == overlap_right:
                            self.x = r.right + 2
                            self.vx = abs(self.vx) * 0.6
                        elif min_overlap == overlap_top:
                            self.y = r.top - 2
                            self.vy = -abs(self.vy) * 0.6
                        else:
                            self.y = r.bottom + 2
                            self.vy = abs(self.vy) * 0.6
                        
                        if parent_list is not None and len(parent_list) < 600 and random.random() < 0.2:
                            parent_list.append(Particle(
                                self.x, self.y,
                                random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0),
                                random.randint(10, 20), self.size * 0.4,
                                self.colors, style="spark", size_mode="Shrink", is_sub=True
                            ))
                        break

            if collision_target in ["All", "Player Only"] and player_rect is not None:
                if player_rect.collidepoint(self.x, self.y):
                    overlap_left = self.x - player_rect.left
                    overlap_right = player_rect.right - self.x
                    overlap_top = self.y - player_rect.top
                    overlap_bottom = player_rect.bottom - self.y
                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap == overlap_left:
                        self.x = player_rect.left - 2
                        self.vx = -abs(self.vx) * 0.6
                    elif min_overlap == overlap_right:
                        self.x = player_rect.right + 2
                        self.vx = abs(self.vx) * 0.6
                    elif min_overlap == overlap_top:
                        self.y = player_rect.top - 2
                        self.vy = -abs(self.vy) * 0.6
                    else:
                        self.y = player_rect.bottom + 2
                        self.vy = abs(self.vy) * 0.6
                    
                    if parent_list is not None and len(parent_list) < 600 and random.random() < 0.3:
                        parent_list.append(Particle(
                            self.x, self.y,
                            random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5),
                            random.randint(10, 20), self.size * 0.5,
                            self.colors, style="spark", size_mode="Shrink", is_sub=True
                        ))

        self.life -= 1
        
        if self.style == "bubble":
            self.frame_index += 0.15
            
        if trail_enabled and not self.is_sub and parent_list is not None and self.life > 1:
            if len(parent_list) < 600 and random.random() < 0.2:
                parent_list.append(Particle(
                    self.x, self.y,
                    random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3),
                    random.randint(8, 15), self.size * 0.5,
                    self.colors, style="circle", size_mode="Shrink", is_sub=True
                ))
                
        if explode_enabled and not self.is_sub and parent_list is not None and self.life <= 1:
            if len(parent_list) < 600:
                for _ in range(6):
                    angle = random.uniform(0, 6.28)
                    speed = random.uniform(0.8, 2.5)
                    parent_list.append(Particle(
                        self.x, self.y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        random.randint(12, 24), self.size * 0.4,
                        self.colors, style="spark", size_mode="Shrink", is_sub=True
                    ))

    def get_interpolated_color(self):
        n = len(self.colors)
        if n == 0:
            return (255, 255, 255)
        
        stops = sorted(self.colors, key=lambda s: s["pos"])
        if n == 1:
            return tuple(stops[0]["color"])
            
        t = 1.0 - (self.life / self.max_life)
        t = max(0.0, min(1.0, t))
        
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

    def get_current_size(self):
        if self.size_mode == "Shrink":
            factor = self.life / self.max_life
            return self.size * max(0.0, factor)
        elif self.size_mode == "Grow":
            factor = 1.0 - (self.life / self.max_life)
            return self.size * max(0.0, factor)
        elif self.size_mode == "Grow & Shrink":
            t = 1.0 - (self.life / self.max_life)
            factor = math.sin(t * math.pi)
            return self.size * max(0.0, factor)
        else:
            return self.size

    def draw(self, surf, panning_offset=(0, 0), zoom=1.0):
        if self.life <= 0:
            return
        
        color = self.get_interpolated_color()
        alpha = int(255 * (self.life / self.max_life))
        alpha = max(0, min(255, alpha))
        
        cx = int(panning_offset[0] + self.x * zoom)
        cy = int(panning_offset[1] + self.y * zoom)
        
        sz = self.get_current_size()
        
        if self.style == "spark":
            sz_px = max(1, int(sz * zoom))
            dx = self.vx * 2.0
            dy = self.vy * 2.0
            p1 = (cx, cy)
            p2 = (int(cx - dx * zoom), int(cy - dy * zoom))
            pygame.draw.line(surf, color, p1, p2, sz_px)
            
        elif self.style == "bubble":
            json_path = "./Assets/particles/bubble.json"
            png_path = "./Assets/particles/bubble.png"
            if self.custom_sprite != "":
                json_path = f"./Assets/particles/{self.custom_sprite}.json"
                png_path = f"./Assets/particles/{self.custom_sprite}.png"
                
            spritesheet = get_spritesheet(json_path, png_path)
            if spritesheet:
                frame = spritesheet.get_frame(self.frame_index)
                if frame:
                    sz_px = int(sz * zoom * 1.5)
                    if sz_px < 1:
                        sz_px = 1
                    scaled_frame = pygame.transform.scale(frame, (sz_px, sz_px))
                    scaled_frame.set_alpha(alpha)
                    tint_surf = pygame.Surface(scaled_frame.get_size(), pygame.SRCALPHA)
                    tint_surf.fill((*color, 255))
                    scaled_frame.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    
                    surf.blit(scaled_frame, (cx - sz_px // 2, cy - sz_px // 2))
                else:
                    self.draw_circle_fallback(surf, color, alpha, cx, cy, sz, zoom)
            else:
                self.draw_circle_fallback(surf, color, alpha, cx, cy, sz, zoom)
                
        elif self.style == "snow":
            sz_px = max(1, int(sz * zoom))
            glow_sz = int(sz_px * 1.6)
            s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            center = glow_sz
            branch_len = int(sz_px * 1.3)
            for angle in [0, math.pi / 3, 2 * math.pi / 3]:
                dx = math.cos(angle) * branch_len
                dy = math.sin(angle) * branch_len
                pygame.draw.line(s, (*color, alpha), (center - dx, center - dy), (center + dx, center + dy), max(1, sz_px // 4))
            pygame.draw.circle(s, (255, 255, 255, alpha), (center, center), max(1, sz_px // 3))
            surf.blit(s, (cx - glow_sz, cy - glow_sz))
            
        elif self.style == "fireball":
            sz_px = max(1, int(sz * zoom))
            glow_sz = int(sz_px * 1.8)
            s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            outer_color = (255, max(0, min(255, color[1] - 50)), max(0, min(255, color[2] - 100)))
            pygame.draw.circle(s, (*outer_color, int(alpha * 0.45)), (glow_sz, glow_sz), glow_sz)
            inner_color = (255, 255, max(0, min(255, color[2] + 100)))
            pygame.draw.circle(s, (*inner_color, alpha), (glow_sz, glow_sz), int(sz_px * 0.8))
            surf.blit(s, (cx - glow_sz, cy - glow_sz))
            
        elif self.style == "star":
            sz_px = max(1, int(sz * zoom))
            glow_sz = int(sz_px * 2.0)
            s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            center = glow_sz
            pygame.draw.line(s, (*color, alpha), (center - glow_sz, center), (center + glow_sz, center), max(1, sz_px // 3))
            pygame.draw.line(s, (*color, alpha), (center, center - glow_sz), (center, center + glow_sz), max(1, sz_px // 3))
            pygame.draw.circle(s, (*color, int(alpha * 0.3)), (center, center), int(sz_px * 0.9))
            pygame.draw.circle(s, (255, 255, 255, alpha), (center, center), max(1, sz_px // 2))
            surf.blit(s, (cx - glow_sz, cy - glow_sz))
            
        else:
            self.draw_circle_fallback(surf, color, alpha, cx, cy, sz, zoom)

    def draw_circle_fallback(self, surf, color, alpha, cx, cy, sz, zoom):
        sz_px = int(sz * zoom)
        if sz_px < 1:
            sz_px = 1
        glow_sz = sz_px * 3
        s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, int(alpha * 0.25)), (glow_sz, glow_sz), glow_sz)
        pygame.draw.circle(s, (*color, alpha), (glow_sz, glow_sz), sz_px)
        surf.blit(s, (cx - glow_sz, cy - glow_sz))


class ParticleEmitter:
    def __init__(self, x, y, name="vfx_0"):
        self.name = name
        self.x, self.y = x, y
        
        self.rate = 2.0          # Spawn rate
        self.spread = 0.5        # Angle spread (radians)
        self.speed = 1.5         # Initial speed
        self.size = 5.0          # Initial size
        self.gravity = 0.0       
        self.friction = 1.0      
        self.colors = [{"pos": 0.0, "color": [0, 175, 240]}, {"pos": 1.0, "color": [0, 80, 120]}] # Default cyan/blue gradient
        self.lifetime = 60       
        self.active = True
        
        self.vortex = 0.0        
        self.color_mode = "Lerp" 
        self.spawn_mode = "Continuous" 
        self.burst_timer = 0
        
        self.particle_style = "circle" # circle, spark, bubble, snow, fireball
        self.custom_sprite = "" 
        
        self.burst_interval = 45
        self.chaos = 0.0        
        self.size_mode = "Constant" 
        self.overall_scale = 0.5
        
        self.preview_scale = 1.0
        self.is_preview = False
        self.particle_cap = 600
        
        self.active_modules = []
        
        self.color_start = [0, 175, 240]
        self.color_end = [0, 80, 120]
        self.color = [0, 175, 240]
        
        self.particles = []

    def get_screen_pos(self, panning_offset, zoom):
        cx = int(panning_offset[0] + self.x * zoom)
        cy = int(panning_offset[1] + self.y * zoom + 30)
        return cx, cy

    def update(self, collision_rects=None, player_rect=None):
        if self.active:
            num_to_spawn = 0
            if self.spawn_mode == "Continuous":
                num_to_spawn = int(self.rate)
                if random.random() < (self.rate - num_to_spawn):
                    num_to_spawn += 1
            else: # Burst
                self.burst_timer += 1
                if self.burst_timer >= self.burst_interval:
                    self.burst_timer = 0
                    num_to_spawn = int(self.rate * 8)
            
            if len(self.particles) >= self.particle_cap:
                num_to_spawn = 0
                
            scale_factor = self.preview_scale if self.is_preview else self.overall_scale
            for _ in range(num_to_spawn):
                angle = random.uniform(-self.spread, self.spread) - 1.57
                spd = self.speed * random.uniform(0.5, 1.2) * scale_factor
                
                if self.color_mode == "Rainbow":
                    hue = (time.time() * 2) % 6.28
                    r = int(127 + 127 * math.sin(hue))
                    g = int(127 + 127 * math.sin(hue + 2.09))
                    b = int(127 + 127 * math.sin(hue + 4.18))
                    active_colors = [{"pos": 0.0, "color": [r, g, b]}, {"pos": 0.5, "color": [g, b, r]}, {"pos": 1.0, "color": [b, r, g]}]
                elif self.color_mode == "Static":
                    active_colors = [{"pos": 0.0, "color": self.colors[0]["color"]}, {"pos": 1.0, "color": self.colors[0]["color"]}]
                else: # Lerp
                    active_colors = self.colors
                    
                active_style = self.particle_style
                if self.custom_sprite != "":
                    active_style = "bubble"
                    
                self.particles.append(Particle(
                    self.x, self.y,
                    math.cos(angle) * spd, math.sin(angle) * spd,
                    self.lifetime, self.size * scale_factor,
                    active_colors,
                    style=active_style,
                    size_mode=self.size_mode,
                    custom_sprite=self.custom_sprite
                ))

        for p in self.particles[:]:
            p.update((self.x, self.y), self.active_modules, self.friction, self.particles, collision_rects, player_rect)
            if p.life <= 0:
                try:
                    self.particles.remove(p)
                except ValueError:
                    pass

    def draw(self, surf, panning_offset, zoom):
        for p in self.particles:
            adjusted_offset = (panning_offset[0], panning_offset[1] + 30)
            p.draw(surf, adjusted_offset, zoom)

    def draw_in_game(self, screen, camera):
        for p in self.particles:
            color = p.get_interpolated_color()
            alpha = int(255 * (p.life / p.max_life))
            alpha = max(0, min(255, alpha))
            
            cx, cy = camera.apply_point(p.x, p.y)
            sz = p.get_current_size()
            
            if p.style == "spark":
                sz_px = max(1, int(sz))
                dx = p.vx * 2.0
                dy = p.vy * 2.0
                p1 = (cx, cy)
                p2 = (int(cx - dx), int(cy - dy))
                pygame.draw.line(screen, color, p1, p2, sz_px)
                
            elif p.style == "bubble":
                json_path = "./Assets/particles/bubble.json"
                png_path = "./Assets/particles/bubble.png"
                if self.custom_sprite != "":
                    json_path = f"./Assets/particles/{self.custom_sprite}.json"
                    png_path = f"./Assets/particles/{self.custom_sprite}.png"
                    
                spritesheet = get_spritesheet(json_path, png_path)
                if spritesheet:
                    frame = spritesheet.get_frame(p.frame_index)
                    if frame:
                        sz_px = int(sz * 1.5)
                        if sz_px < 1:
                            sz_px = 1
                        scaled_frame = pygame.transform.scale(frame, (sz_px, sz_px))
                        scaled_frame.set_alpha(alpha)
                        tint_surf = pygame.Surface(scaled_frame.get_size(), pygame.SRCALPHA)
                        tint_surf.fill((*color, 255))
                        scaled_frame.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(scaled_frame, (cx - sz_px // 2, cy - sz_px // 2))
                    else:
                        self.draw_circle_fallback_in_game(screen, color, alpha, cx, cy, sz)
                else:
                    self.draw_circle_fallback_in_game(screen, color, alpha, cx, cy, sz)
                    
            elif p.style == "snow":
                sz_px = max(1, int(sz))
                glow_sz = int(sz_px * 1.6)
                s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
                center = glow_sz
                branch_len = int(sz_px * 1.3)
                for angle in [0, math.pi / 3, 2 * math.pi / 3]:
                    dx = math.cos(angle) * branch_len
                    dy = math.sin(angle) * branch_len
                    pygame.draw.line(s, (*color, alpha), (center - dx, center - dy), (center + dx, center + dy), max(1, sz_px // 4))
                pygame.draw.circle(s, (255, 255, 255, alpha), (center, center), max(1, sz_px // 3))
                screen.blit(s, (cx - glow_sz, cy - glow_sz))
                
            elif p.style == "fireball":
                sz_px = max(1, int(sz))
                glow_sz = int(sz_px * 1.8)
                s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
                outer_color = (255, max(0, min(255, color[1] - 50)), max(0, min(255, color[2] - 100)))
                pygame.draw.circle(s, (*outer_color, int(alpha * 0.45)), (glow_sz, glow_sz), glow_sz)
                inner_color = (255, 255, max(0, min(255, color[2] + 100)))
                pygame.draw.circle(s, (*inner_color, alpha), (glow_sz, glow_sz), int(sz_px * 0.8))
                screen.blit(s, (cx - glow_sz, cy - glow_sz))
                
            else:
                self.draw_circle_fallback_in_game(screen, color, alpha, cx, cy, sz)

    def draw_circle_fallback_in_game(self, screen, color, alpha, cx, cy, size):
        sz = int(size)
        if sz < 1:
            sz = 1
        glow_sz = sz * 3
        s = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, int(alpha * 0.25)), (glow_sz, glow_sz), glow_sz)
        pygame.draw.circle(s, (*color, alpha), (glow_sz, glow_sz), sz)
        screen.blit(s, (cx - glow_sz, cy - glow_sz))

    def draw_icon(self, screen, panning_offset, zoom, is_selected):
        cx, cy = self.get_screen_pos(panning_offset, zoom)
        pulse = 1.0 + 0.15 * math.sin(time.time() * 5)
        r = int(8 * zoom * pulse)
        if r < 3:
            r = 3
            
        color = tuple(self.color_start)
        
        if is_selected:
            pygame.draw.circle(screen, (255, 215, 0), (cx, cy), r + 5, 2)
            
        points = [
            (cx, cy - r),
            (cx + r, cy),
            (cx, cy + r),
            (cx - r, cy)
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (30, 30, 42), points, 1)

    def collidePoint(self, mouse_pos, panning_offset, zoom):
        cx, cy = self.get_screen_pos(panning_offset, zoom)
        return pygame.Rect(cx - 12, cy - 12, 24, 24).collidepoint(mouse_pos)