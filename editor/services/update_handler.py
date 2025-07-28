from datetime import datetime
import random
import threading
import urllib.request
import urllib.error
import json
import traceback
import pygame

from editor.core.utils import Colors

class UpdateAndCrashHandler:
    def __init__(self, repo_owner, repo_name, local_commit_file, screen,version):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.local_commit_file = local_commit_file
        self.screen = screen
        self.version = version
        self.latest_commit = None
        self.need_update = False
        

        self.notif_state = "hidden"
        self.notif_start_time = 0
        self.notif_duration = 5


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
            if self.notif_state == "hidden":
                self.notif_state = "show"
                self.notif_start_time = pygame.time.get_ticks()

        if self.notif_state == "done" and pygame.time.get_ticks() - self.notif_start_time > self.notif_duration * 1000:
            self.notif_state = "hidden"


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

    def get_worker_info(self):
        """
        Retourne l'URL chiffrée et le token pour le Worker, puis les décode en interne (systeme de backup au cas ou le premier lien ne marche pas)
        """
        # Chaînes chiffrées
        encoded_url = (
            "49-120-103-102-48-117-116-103-109-116-113-121-48-110-110-103-106-117-113-116-103-124-50-48-56-50-54-57-47-112-107-99-116-47-112-103-109-113-116-100-49-49-60-117-114-118-118-106"
        )
        encoded_token = (
            "49-58-57-56-55-54-53-52-51-50-111-102-108-49-85-117-102-115-100-102-37-122-115-53-87"
        )
        # Décodage URL: inversion des opérations (décalage puis inversion string)
        url_points = [int(n) for n in encoded_url.split('-')]
        url_chars = ''.join(chr((n - 2) % 256) for n in url_points)
        worker_url = url_chars[::-1]
        # Décodage token: inversion du décalage puis inversion string
        token_points = [int(n) for n in encoded_token.split('-')]
        token_chars = ''.join(chr((n - 1) % 256) for n in token_points)
        worker_token = token_chars[::-1]
        return worker_url, worker_token

    def send_crash_alert(self, error_msg):

        def send_alert():
            try:
                # Envoi au webhook Discord
                data = json.dumps({
                    "content": f":warning: Crash détecté (version {self.version}):\n```\n{error_msg[:1900]}\n```"
                }).encode("utf-8")
                req = urllib.request.Request(
                    self.get_url(),
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0"
                    }
                )
                urllib.request.urlopen(req, timeout=5)
                
            except Exception:
                # Si échec, fallback vers le Worker
                try:
                    worker_url, worker_token = self.get_worker_info()
                    payload = json.dumps({"content": error_msg[:1900]}).encode('utf-8')
                    req2 = urllib.request.Request(
                        worker_url,
                        data=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "CrashReporter-Worker/1.0",
                            "X-Secret-Token": worker_token
                        },
                        method="POST"
                    )
                    urllib.request.urlopen(req2, timeout=5)
                except Exception as e2:
                    print(f"Erreur fallback Worker: {e2}")
        thread = threading.Thread(target=send_alert)
        thread.daemon = True
        thread.start()

    def display_update_notification(self,nm):

        if self.notif_state == "show":
            nm.notify('update', 'Update (Github)', 'Nouvelle mise à jour Disponible !',duration=self.notif_duration)
            self.notif_start_time=pygame.time.get_ticks()
            self.notif_state="done"



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
