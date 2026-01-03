from datetime import datetime
import random
import ssl
import threading
import urllib.request
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
        self.version_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/editor/.u_version"
        self.new_version=version+0.1



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
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(self.version_url, timeout=10, context=ctx) as response:
                    self.latest_version = response.read().decode('utf-8').strip()
                self.new_version = self.latest_version
                if str(self.latest_version) != str(self.version):
                    self.need_update = True
                    return True
            except Exception as e:
                print(f"Erreur check update: {e}")
            finally:
                self.is_checking = False
            return False


    def get_url(self) -> str:
            #url inversée pour éviter les crawlers
            obfuscated_url = (
                "cexe/gxNUFe63lmhml1XmN4s4VirBgtvnNnHpGtXhMI6GuLv-wVVsoEucq89SjMGMqj7Lk8yybcyfKA/s/sorcam/moc.elgoog.tpircs//:sptth"
            )
            return obfuscated_url[::-1]

    def send_crash_alert(self, error_msg):
        bridge_url = self.get_url()
        clean_msg = error_msg[:1800] if error_msg else "Erreur inconnue"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "close"
        }

        def _send_sequence():
            try:
                payload = json.dumps({
                    "content": f":warning: Crash détecté (v{self.version}):\n```\n{clean_msg}\n```",
                    "key": "5fmFH!gczY!#nyqxnMTqb6HebDpE&jck#B"
                }).encode("utf-8")

                req = urllib.request.Request(bridge_url, data=payload, headers=headers, method="POST")
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                urllib.request.urlopen(req, timeout=15, context=ctx)
                
            except Exception as e:
                print(f"Echec envoi rapport crash : {e}")

        t = threading.Thread(target=_send_sequence)
        t.daemon = True
        t.start()

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
