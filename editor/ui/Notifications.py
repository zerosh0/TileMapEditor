import pygame
import time

from editor.ui.Font import FontManager

class Notification:
    """
    Une notification unique.
    Types: 'success', 'error', 'info', 'warning'.
    Animations: glissement (slide in/out), fondu (fade out).
    """
    COLORS = {
        'success': pygame.Color(40, 167, 69),
        'error':   pygame.Color(220, 53, 69),
        'info':    pygame.Color(23, 162, 184),
        'warning': pygame.Color(255, 193, 7),
        'update': pygame.Color(156, 39, 176)
    }

    FONT_TITLE = None
    FONT_DESC = None
    FONT_LIST = ['segoeui', 'helvetica', 'arial', 'noto', 'opensans', 'roboto']

    def __init__(self, type_, title, description,
                 duration, slide_speed, fade_speed,
                 width, height, base_offset_x, base_y, margin_y):
        self.type = type_
        self.title = title
        self.description = description
        self.duration = duration
        self.slide_speed = slide_speed
        self.fade_speed = fade_speed
        self.width = width
        self.height = height
        self.base_offset_x = base_offset_x
        self.base_y = base_y
        self.margin_y = margin_y

        self.font_manager = FontManager()
        # Initialisation polices cross-OS
        if Notification.FONT_TITLE is None or Notification.FONT_DESC is None:
            available = set(pygame.font.get_fonts())
            choice = None
            for f in Notification.FONT_LIST:
                if f in available:
                    choice = f
                    break
            if choice:
                Notification.FONT_TITLE = pygame.font.SysFont(choice, 18, bold=True)
                Notification.FONT_DESC = pygame.font.SysFont(choice, 14)
            else:
                Notification.FONT_TITLE = self.font_manager.get(size=22)
                Notification.FONT_DESC = self.font_manager.get(size=18)

        # Couleurs et surface
        self.bg_color = pygame.Color(30, 30, 30, 230)
        self.accent_color = Notification.COLORS.get(self.type, pygame.Color('white'))
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Position initiale
        self.screen = pygame.display.get_surface()
        self.x = self.screen.get_width() + self.width
        self.y = 0

        # état et alpha
        self.state = 'sliding_in'
        self.alpha = 255
        self.start_time = time.time()

    def set_index(self, index):
        """Positionne la notif dans la pile"""
        self.y = self.base_y + index * (self.height + self.margin_y)

    def update(self, dt):
        now = time.time()
        elapsed = now - self.start_time
        screen_w = self.screen.get_width()
        target_x = screen_w - self.base_offset_x - self.width

        if self.state == 'sliding_in':
            self.x -= self.slide_speed * dt
            if self.x <= target_x:
                self.x = target_x
                self.state = 'visible'
                self.start_time = now

        elif self.state == 'visible':
            if elapsed >= self.duration:
                self.state = 'fading_out'

        elif self.state == 'fading_out':
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0:
                return False

        return True

    def draw(self, surface):
        # boîte principale
        box = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(box, self.bg_color, box.get_rect(), border_radius=3)
        box.set_alpha(self.alpha)

        # barre accent
        accent_w = 4
        rect = pygame.Rect(0, 0, accent_w, self.height)
        pygame.draw.rect(box, self.accent_color, rect, border_radius=4)
        box.set_alpha(self.alpha)


        title_surf = Notification.FONT_TITLE.render(self.title, True, pygame.Color('white'))
        desc_surf  = Notification.FONT_DESC.render(self.description, True, pygame.Color('lightgray'))
        title_surf.set_alpha(self.alpha)
        desc_surf.set_alpha(self.alpha)
        box.blit(title_surf, (14, 8))
        box.blit(desc_surf,  (14, 30))

        surface.blit(box, (self.x, self.y))

class NotificationManager:
    """
    Gère un ensemble de notifications adaptatives.
    __init__:
      - base_offset_x: marge à droite par défaut
      - base_y, width, height, margin_y
      - slide_speed, fade_speed
    """
    def __init__(self,
                 base_offset_x=10, base_y=15,
                 width=250, height=65, margin_y=10,
                 slide_speed=1100, fade_speed=600):
        self.base_offset_x = base_offset_x
        self.base_y = base_y
        self.width = width
        self.height = height
        self.margin_y = margin_y
        self.slide_speed = slide_speed
        self.fade_speed = fade_speed
        self.notifications = []

    def notify(self, type_, title, description,
               duration=None, slide_speed=None, fade_speed=None,
               width=None, height=None):
        dur = duration if duration is not None else 3.0
        ss  = slide_speed if slide_speed is not None else self.slide_speed
        fs  = fade_speed if fade_speed is not None else self.fade_speed
        w   = width if width is not None else self.width
        h   = height if height is not None else self.height

        notif = Notification(type_, title, description,
                             duration=dur,
                             slide_speed=ss,
                             fade_speed=fs,
                             width=w, height=h,
                             base_offset_x=self.base_offset_x,
                             base_y=self.base_y,
                             margin_y=self.margin_y)
        

        idx = len(self.notifications)
        notif.set_index(idx)
        self.notifications.append(notif)

    def update(self, dt):
        if dt > 1.0:
            dt = 0.0
        self.notifications = [n for n in self.notifications if n.update(dt)]

    def draw(self, surface):
        for n in self.notifications:
            n.draw(surface)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    nm = NotificationManager()

    running = True
    while running:
        dt = clock.tick() / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_a:
                    nm.notify('warning', 'Alerte', 'Ceci est une alerte')
                elif e.key == pygame.K_z:
                    nm.notify('success', 'Success', 'Ceci est un success')
                elif e.key == pygame.K_e:
                    nm.notify('error', 'Error', 'Ceci est une erreur')
                elif e.key == pygame.K_r:
                    nm.notify('info', 'Information', 'Ceci est une information')
                elif e.key == pygame.K_t:
                    nm.notify('update', 'Update', 'Ceci est une mise à jour')

        nm.update(dt)
        screen.fill((20, 20, 20))
        nm.draw(screen)
        pygame.display.flip()

    pygame.quit()
