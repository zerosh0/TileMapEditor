from datetime import datetime
import random
import threading
import urllib.request
import urllib.error
import json
import traceback
import pygame

from editor.utils import Colors

class UpdateAndCrashHandler:
    def __init__(self, repo_owner, repo_name, local_commit_file, screen):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.local_commit_file = local_commit_file
        self.screen = screen
        self.latest_commit = None
        self.need_update = False

        self.notif_state = "hidden"
        self.notif_alpha = 0
        self.notif_start_time = 0
        self.notif_duration = 5000
        self.fade_duration = 600

        self.update_interval = 3600

    def get_latest_commit(self):
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/commits"
            with urllib.request.urlopen(url) as response:
                data = json.load(response)
                self.latest_commit = data[0]['sha']
                return self.latest_commit
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print("Rate limit exceeded. Skipping update check for now.")
                return None
            else:
                self.send_crash_alert(f"Erreur get_latest_commit:\n{str(e)}")
                return None
        except Exception as e:
            self.send_crash_alert(f"Erreur get_latest_commit:\n{str(e)}")
            return None

    def read_local_commit(self):
        try:
            with open(self.local_commit_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def write_local_commit(self, sha):
        with open(self.local_commit_file, 'w') as f:
            f.write(sha)

    def schedule_update_check(self):
        if self.check_for_update():
            self.need_update = True
            if self.notif_state == "hidden":
                self.notif_state = "fading_in"
                self.notif_start_time = pygame.time.get_ticks()
        threading.Timer(self.update_interval, self.schedule_update_check).start()

    def check_for_update(self):
        latest = self.get_latest_commit()
        local = self.read_local_commit()
        if latest and latest != local:
            self.write_local_commit(latest)
        if local is None:
            return False
        return latest and latest != local


    def get_url(self) -> str:
        """
        Retourne une URL encodée pour éviter sa détection en clair
        par des crawlers, indexeurs ou bots.
        cette fonction ne vise pas la sécurité, mais sert uniquement à éviter 
        que l'URL soit lisible ou détectable automatiquement.
        Type de chiffrement : Inversion + Décalage (type Caesar) + Encodage numérique
        """
        encoded_data = (
            "123-69-117-114-55-119-84-118-91-69-124-100-70-100-56-101-60-101-84-48-70-"
            "101-119-120-74-54-119-89-89-90-119-93-69-105-113-60-119-92-110-51-108-86-"
            "109-72-109-57-92-104-119-69-57-80-58-108-76-75-101-115-82-82-55-71-57-70-"
            "100-82-102-118-50-53-60-53-51-58-59-53-57-54-54-52-60-57-53-51-53-57-54-"
            "52-50-118-110-114-114-107-101-104-122-50-108-115-100-50-112-114-102-49-103-"
            "117-114-102-118-108-103-50-50-61-118-115-119-119-107"
        )
        code_points = [int(num) for num in encoded_data.split('-')]
        shifted_chars = ''.join(chr((num - 3) % 256) for num in code_points)
        decoded_url = shifted_chars[::-1]
        return decoded_url

    def send_crash_alert(self, error_msg):
        def send_alert():
            try:
                data = json.dumps({
                    "content": f":warning: Crash détecté :\n```\n{error_msg[:1900]}\n```"
                }).encode("utf-8")
                # crash webhook
                req = urllib.request.Request(
                    self.get_url(),
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    }
                )
                urllib.request.urlopen(req)
            except Exception as e:
                print(f"Erreur webhook: {e}")

        thread = threading.Thread(target=send_alert)
        thread.start()

    def display_update_notification(self):
        now = pygame.time.get_ticks()

        if self.notif_state == "fading_in":
            elapsed = now - self.notif_start_time
            progress = elapsed / self.fade_duration
            if progress >= 1:
                self.notif_alpha = 255
                self.notif_state = "visible"
                self.notif_start_time = now
            else:
                self.notif_alpha = int(progress * 255)

        elif self.notif_state == "visible":
            self.notif_alpha = 255
            if now - self.notif_start_time >= self.notif_duration:
                self.notif_state = "fading_out"
                self.notif_start_time = now

        elif self.notif_state == "fading_out":
            elapsed = now - self.notif_start_time
            progress = elapsed / self.fade_duration
            self.notif_alpha = int(255 * (1 - progress))
            if progress >= 1:
                self.notif_state = "hidden"
                self.notif_alpha = 0
                self.need_update = False

        if self.notif_alpha > 0:
            font = pygame.font.SysFont(None, 28)
            message = "Mise à jour dispo sur GitHub !"
            text_surf = font.render(message, True, (255, 255, 255))
            width = text_surf.get_width() + 20
            height = text_surf.get_height() + 10
            notif_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            notif_color = (200, 50, 50, int(self.notif_alpha))
            notif_surface.fill(notif_color)
            text_surf.set_alpha(int(self.notif_alpha))
            notif_surface.blit(text_surf, (10, 5))
            self.screen.blit(notif_surface, (0, self.screen.get_height()-47))

    def handle_crash(self, func, editor):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                error = traceback.format_exc()
                self.send_crash_alert(error)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                random_id = random.randint(1000, 9999)
                save_name = f"SecureSave_{timestamp}_{random_id}.json"
                # Sauvegarde d'urgence
                editor.saveLoadManager.save(editor, save_name)
                
                print(f"\n{Colors.RED}╔═══════════════════════════════════════════════════╗")
                print(f"║ {Colors.YELLOW}CRASH DE L'EDITEUR ! {Colors.RED}")
                print(f"╠═══════════════════════════════════════════════════╣")
                print(f"║ {Colors.YELLOW}Erreur : {Colors.RESET}{str(e)}{Colors.RED}")
                print(f"║ {Colors.YELLOW}Type : {Colors.RESET}{type(e).__name__}{Colors.RED}")
                print(f"╠═══════════════════════════════════════════════════╣")
                print(f"║ {Colors.GREEN}Une sauvegarde de secours a été créée :{Colors.RED}")
                print(f"║ {Colors.BLUE}{save_name}{Colors.RED}")
                print(f"╚═══════════════════════════════════════════════════╝{Colors.RESET}\n")
                
                raise
        return wrapper
