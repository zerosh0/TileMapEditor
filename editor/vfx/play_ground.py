import pygame
import random
import math

WIDTH, HEIGHT = 1100, 700
BG_COLOR = (12, 12, 18)
ACCENT_COLOR = (0, 200, 255)


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

class Slider:
    def __init__(self, rel_x, rel_y, w, label, min_v, max_v, cur_v):
        self.rect = pygame.Rect(0, 0, w, 10)
        self.rel_x, self.rel_y = rel_x, rel_y
        self.label, self.min_v, self.max_v, self.val = label, min_v, max_v, cur_v
        self.grabbed = False

    def draw(self, surf, font, ox, oy):
        self.rect.topleft = (ox + self.rel_x, oy + self.rel_y)
        pygame.draw.rect(surf, (60, 60, 75), self.rect, border_radius=5)
        px = self.rect.x + (self.val - self.min_v) / (self.max_v - self.min_v + 0.001) * self.rect.w
        pygame.draw.circle(surf, ACCENT_COLOR, (int(px), self.rect.y + 5), 7)
        txt = font.render(f"{self.label}: {self.val:.2f}", True, (200, 200, 200))
        surf.blit(txt, (self.rect.x, self.rect.y - 18))

    def handle(self, event, ox, oy):
        self.rect.topleft = (ox + self.rel_x, oy + self.rel_y)
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.inflate(10, 20).collidepoint(event.pos):
            self.grabbed = True
        if event.type == pygame.MOUSEBUTTONUP: self.grabbed = False
        if self.grabbed:
            mx = max(self.rect.x, min(pygame.mouse.get_pos()[0], self.rect.x + self.rect.w))
            self.val = self.min_v + (mx - self.rect.x) / self.rect.w * (self.max_v - self.min_v)

class Window:
    def __init__(self, title, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.elements = []
        self.drag = False
        self.offset = (0,0)

    def draw(self, surf, font):
        pygame.draw.rect(surf, (30, 30, 40), self.rect, border_radius=8)
        pygame.draw.rect(surf, (45, 45, 55), (self.rect.x, self.rect.y, self.rect.w, 25), border_top_left_radius=8, border_top_right_radius=8)
        surf.blit(font.render(self.title, True, (255, 255, 255)), (self.rect.x + 10, self.rect.y + 4))
        for el in self.elements: el.draw(surf, font, self.rect.x, self.rect.y)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 25).collidepoint(event.pos):
                self.drag = True
                self.offset = (self.rect.x - event.pos[0], self.rect.y - event.pos[1])
                return "FOCUS"
        if event.type == pygame.MOUSEBUTTONUP: self.drag = False
        if self.drag:
            self.rect.x, self.rect.y = pygame.mouse.get_pos()[0] + self.offset[0], pygame.mouse.get_pos()[1] + self.offset[1]
        for el in self.elements: el.handle(event, self.rect.x, self.rect.y)
        return self.rect.collidepoint(pygame.mouse.get_pos())

class Particle:
    def __init__(self, x, y, vx, vy, life, size, c1, c2):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.size = size
        self.c1, self.c2 = c1, c2

    def update(self, grav, fric):
        self.vy += grav
        self.vx *= fric
        self.vy *= fric
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surf):
        t = 1.0 - (self.life / self.max_life)
        color = lerp_color(self.c1, self.c2, t)
        alpha = int(255 * (self.life / self.max_life))
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (self.size, self.size), self.size)
        surf.blit(s, (self.x - self.size, self.y - self.size))

class ParticleEditor:
    def __init__(self,screen,clock):
        self.screen=screen
        self.clock=clock
        self.font = pygame.font.SysFont("Consolas", 13)
        self.particles = []
        self.setup_ui()

    def setup_ui(self):
        self.quit_rect = pygame.Rect(self.screen.get_width() - 40, 10, 30, 30)
        self.w_spawn = Window("EMITTER: SPAWN", 20, 20, 250, 150)
        self.s_rate = Slider(20, 50, 200, "Spawn Rate", 0, 20, 5)
        self.s_spread = Slider(20, 100, 200, "Angle Spread", 0, 6.28, 1.5)
        self.w_spawn.elements += [self.s_rate, self.s_spread]

        self.w_init = Window("PARTICLE: INIT", 20, 180, 250, 150)
        self.s_speed = Slider(20, 50, 200, "Initial Speed", 0, 10, 3)
        self.s_size = Slider(20, 100, 200, "Start Size", 1, 20, 1.5)
        self.w_init.elements += [self.s_speed, self.s_size]

        self.w_phys = Window("PARTICLE: UPDATE", 20, 340, 250, 150)
        self.s_grav = Slider(20, 50, 200, "Gravity", -0.5, 0.5, 0.1)
        self.s_fric = Slider(20, 100, 200, "Friction", 0.9, 1.0, 0.97)
        self.w_phys.elements += [self.s_grav, self.s_fric]

        self.w_color = Window("PARTICLE: COLOR", 20, 500, 250, 180)
        self.s_r1 = Slider(20, 50, 200, "Start R", 0, 255, 255)
        self.s_g1 = Slider(20, 80, 200, "Start G", 0, 255, 150)
        self.s_r2 = Slider(20, 130, 200, "End R", 0, 255, 50)
        self.s_g2 = Slider(20, 160, 200, "End G", 0, 255, 255)
        self.w_color.elements += [self.s_r1, self.s_g1, self.s_r2, self.s_g2]

        self.windows = [self.w_spawn, self.w_init, self.w_phys, self.w_color]

    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                for i, w in enumerate(reversed(self.windows)):
                    res = w.handle(event)
                    if res:
                        if res == "FOCUS": self.windows.append(self.windows.pop(len(self.windows)-1-i))
                        break
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.quit_rect.collidepoint(event.pos):
                            return
                    
            if pygame.mouse.get_pressed()[0] and not any(w.rect.collidepoint(mx, my) for w in self.windows):
                for _ in range(int(self.s_rate.val)):
                    angle = random.uniform(-self.s_spread.val, self.s_spread.val) - 1.57 # -90 deg
                    spd = self.s_speed.val * random.uniform(0.5, 1.2)
                    c1 = (self.s_r1.val, self.s_g1.val, 200)
                    c2 = (self.s_r2.val, self.s_g2.val, 100)
                    self.particles.append(Particle(mx, my, math.cos(angle)*spd, math.sin(angle)*spd, 60, self.s_size.val, c1, c2))

            for p in self.particles[:]:
                p.update(self.s_grav.val, self.s_fric.val)
                if p.life <= 0: self.particles.remove(p)


            self.screen.fill(BG_COLOR)
            for x in range(0, self.screen.get_width(), 25): pygame.draw.line(self.screen, (20,20,30), (x,0), (x,HEIGHT))
            for y in range(0, HEIGHT, 25): pygame.draw.line(self.screen, (20,20,30), (0,y), (self.screen.get_width(),y))
            
            for p in self.particles: p.draw(self.screen)
            for w in self.windows: w.draw(self.screen, self.font)
            
            pygame.draw.rect(self.screen, (20,20,30), (self.screen.get_width()-150, HEIGHT-40, 140, 30), border_radius=5)
            self.screen.blit(self.font.render(f"Particles: {len(self.particles)}", True, (150,150,150)), (self.screen.get_width()-140, HEIGHT-30))
            try:
                pygame.draw.aacircle(self.screen, (200, 71, 88), self.quit_rect.center, 5)
            except:
                pygame.draw.circle(self.screen, (200, 71, 88), self.quit_rect.center, 5)
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    ParticleEditor(screen,clock).run()