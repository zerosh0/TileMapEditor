import fnmatch
import json
import pygame
import os
import platform
from pathlib import Path
from editor.ui.DialogSystem import DialogBox
from editor.ui.Font import FontManager
from editor.ui.Notifications import NotificationManager
from editor.ui.Input import InputField

class FileDialog:
    
    """
    Pygame FileDialog with:
    - Validation button + double-click open
    - Close button
    - Search input
    - Breadcrumb clickable
    - Tree view
    - Grid view with icons, hover, single-click select
    - Scrollbar (wheel + draggable thumb)
    - Back navigation (mouse back button)
    - Access to all drives (all OS roots)
    """
    ICON_SIZE = 32
    PADDING = 8
    ITEM_W = 150
    ITEM_H = 60
    SPACING_X = 5
    SPACING_Y = 5
    OFFSET_X = 37
    OFFSET_Y = 10
    SCROLL_STEP = 20
    SCROLLBAR_W = 8
    DOUBLE_CLICK_MS = 500

    CONFIG_FILE = Path(__file__).parent / ".filedialogrc"


    @classmethod
    def _load_config(cls):
        if cls.CONFIG_FILE.exists():
            try:
                return json.loads(cls.CONFIG_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"open": None, "save": None}

    @classmethod
    def _save_config(cls, cfg):
        try:
            cls.CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception as e:
            print("⚠️ Impossible d'écrire la config :", e)



    def __init__(self, rect,notification, mode='open', start_path=None, icon_dir='icons', theme=None,
                 on_confirm=None, on_cancel=None,default_save_name=""):
        self.nm=notification
        self.rect = pygame.Rect(rect)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.mode = mode
        self.on_confirm = on_confirm or (lambda p: None)
        self.on_cancel = on_cancel or (lambda: None)
        # theme
        self.bg = theme.get('bg',(30,30,30)) if theme else (30,30,30)
        self.border = theme.get('border',(50,50,50)) if theme else (50,50,50)
        self.font_manager = FontManager()
        self.font = self.font_manager.get(size=18)
        self.font2 = self.font_manager.get(size=15)
        # header drag + close
        self.header_h = 24
        self.drag = False; self.drag_off = (0,0)
        self.close_r = 4.6
        self.close_c = (self.rect.w - 8 - self.close_r, 8 + self.close_r)

        self._appear_time     = 0.0
        self._appear_duration = 0.15
        self.surface.set_alpha(0)
        cfg = self._load_config()
        initial = start_path or cfg.get(mode) or os.getcwd()
        self.cwd = Path(initial)
        self._config = cfg

        # search input
        sb_h = 24
        self.search = InputField(
            rect=(0, 0, 200, sb_h),
            font=self.font, bg_color=(41,41,41),
            border_color=self.border, on_change=self._on_search,
            placeholder="Search..."
        )
        self.search_height = sb_h
        # breadcrumb
        self.search_rect = pygame.Rect(
            376,
            self.header_h + self.PADDING,
            self.search.rect.width,
            self.search_height
        )
        self.hover_bc = None
        self.bc_y = self.search_rect.bottom
        self.breadcrumb_segments = []

        self.dlg_confirm = DialogBox(
            rect=(self.surface.get_width()/2,self.surface.get_height()/2,300,100),
            title="Le fichier existe déjà",
            description="êtes vous sûr de vouloir l'écraser ?",
            buttons=[
                {'text':'Oui', 'callback': self.perform_save},
                {'text':'Non', 'callback': self.cancel_save}
            ],
            on_cancel=self.cancel_save,
            active=False
        )

        # panels
        left_w = int(self.rect.w * 0.3)
        top = self.bc_y + self.font.get_height() + self.PADDING
        height = self.rect.h - top - 3*self.PADDING - sb_h
        self.tree_rect = pygame.Rect(self.PADDING, top, left_w, height)
        grid_w = self.rect.w - left_w - 4*self.PADDING - self.SCROLLBAR_W
        self.grid_rect = pygame.Rect(left_w + 2*self.PADDING, top, grid_w, height)
        self.scrollbar_rect = pygame.Rect(self.grid_rect.right + self.PADDING//2,
                                          top, self.SCROLLBAR_W, height)

        # confirm button
        btn_w, btn_h = 60, 24
        self.btn_rect = pygame.Rect(self.rect.w - btn_w - self.PADDING,
                                    self.rect.h - btn_h - self.PADDING,
                                    btn_w, btn_h)
        # ————— Champ de nom de fichier en mode save —————
        if self.mode == 'save':
            # Width = largeur bouton × 2 pour laisser de la place
            input_w = self.rect.w - btn_w - 3*self.PADDING
            input_h = btn_h
            # Position : même hauteur que le bouton, à gauche
            self.filename_rect = pygame.Rect(
                self.PADDING,
                self.rect.h - btn_h - self.PADDING,
                input_w, input_h
            )
            self.filename_input = InputField(
                rect=(0,0,input_w,input_h),
                font=self.font, bg_color=(41,41,41),
                border_color=self.border,
                placeholder="Nom de fichier...",
                on_change=lambda text: self._on_save(text),
                text=default_save_name
            )

        # data
        self.entries = []
        self.filtered = []
        self.selected_idx = None
        self.hover_idx = None
        self.scroll = 0
        self.is_level = {}
        # click tracking
        self.last_click_time = 0

        # scrollbar drag
        self.drag_scroll = False; self.scroll_y0 = 0; self.scroll_start = 0
        self.EXTRA_SCROLL = 10
        # icons
        self.icon_dir = icon_dir; self._load_icons(); self._load_entries()
        
    def update_animation(self, dt):
        self._appear_time += dt
        t = min(self._appear_time / self._appear_duration, 1.0)
        alpha = int(255 * t)
        self.surface.set_alpha(alpha)



    def cancel_save(self):
        self.dlg_confirm.active=False

    def perform_save(self):
            self.dlg_confirm.active=False
            name = self.filename_input.text.strip()
            if name:
                target = str(self.cwd / name)
                self._config[self.mode] = str(self.cwd)
                self._save_config(self._config)
                self.on_confirm(target)

    def _total_content_height(self):
        cols = max(1, self.grid_rect.w // self.ITEM_W)
        content_h = ((len(self.filtered) + cols - 1) // cols) * (self.ITEM_H+5)
        return content_h + self.EXTRA_SCROLL

    def _load_icons(self):
        icon_dir = Path(self.icon_dir)
        json_path = Path("Assets/ui/fileDialog.json")
        
        # icônes « folder » et « default »
        self.icons = {}
        for key in ("folder", "default"):
            p = icon_dir / f"{key}.png"
            if p.exists():
                img = pygame.image.load(str(p)).convert_alpha()
                self.icons[key] = pygame.transform.scale(img, (self.ICON_SIZE, self.ICON_SIZE))
            else:
                self.icons[key] = None
        
        # on garde juste la table ext->fichier, sans charger les images
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                self.ext_to_icon = json.load(f)
        else:
            print("⚠️ JSON manquant :", json_path)
            self.ext_to_icon = {}
        
        self.icon_cache = {}
        self.root_icons = {}

        # charge une icône générique de drive
        drive_img = pygame.image.load("Assets/ui/icones/fileDialog/application-x-cd-image.png").convert_alpha()
        self.root_icons['drive'] = pygame.transform.scale(drive_img, (16,16))

        # charge une icône “user folder”
        user_img = pygame.image.load("Assets/ui/icones/fileDialog/user.png").convert_alpha()
        self.root_icons['user'] = pygame.transform.scale(user_img, (16,16))

        # Desktop, Downloads, Documents, etc.
        for name in ('Desktop','Downloads','Documents','Pictures','Music','Videos'):
            p = pygame.image.load(f"Assets/ui/icones/fileDialog/{name.lower()}.png").convert_alpha()
            self.root_icons[name.lower()] = pygame.transform.scale(p, (16,16))

        # icône par défaut
        default_img = pygame.image.load("Assets/ui/icones/fileDialog/folder.png").convert_alpha()
        self.root_icons['default'] = pygame.transform.scale(default_img, (16,16))


    def _get_icon(self, ext: str, path: str) -> pygame.Surface:
        ext = ext.lower().lstrip('.')

        if ext == "json" and self.is_level.get(path, False):
            return self._load_icon_by_key("level")

        key = f".{ext}"
        icon_file = self.ext_to_icon.get(key)
        if icon_file:
            return self._load_icon_by_file(icon_file, ext)

        return self.icons["default"]


    def _load_icon_by_key(self, key: str) -> pygame.Surface:
        if key in self.icon_cache:
            return self.icon_cache[key]
        icon_file = self.ext_to_icon.get(key)
        surf = self.icons.get(key)  # folder/default sont déjà préchargées
        if not surf and icon_file:
            p = Path(self.icon_dir) / icon_file
            if p.exists():
                img = pygame.image.load(str(p)).convert_alpha()
                surf = pygame.transform.scale(img, (self.ICON_SIZE, self.ICON_SIZE))
        self.icon_cache[key] = surf or self.icons["default"]
        return self.icon_cache[key]

    def _load_icon_by_file(self, icon_file: str, cache_key: str) -> pygame.Surface:
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        p = Path(self.icon_dir) / icon_file
        if p.exists():
            img = pygame.image.load(str(p)).convert_alpha()
            surf = pygame.transform.scale(img, (self.ICON_SIZE, self.ICON_SIZE))
        else:
            surf = self.icons["default"]
        self.icon_cache[cache_key] = surf
        return surf

    def _load_entries(self):
        self.entries.clear()
        self.search.text = ""
        self.is_level.clear()

        # Essayer de lister, sinon on reste dans le dossier parent
        try:
            it = list(self.cwd.iterdir())
        except (PermissionError, FileNotFoundError) as e:
            self.nm.notify('error', "Erreur", e.strerror,duration=2)
            # Impossible d'accéder à cwd : on remonte d'un cran si possible
            if self.cwd.parent != self.cwd:
                self.cwd = self.cwd.parent
                return self._load_entries()
            else:
                return

        # Trier et filtrer
        for p in sorted(it, key=lambda p: (not p.is_dir(), p.name.lower())):
            # Pour chaque entrée, ignorer si trop restreint
            try:
                is_dir = p.is_dir()
                ctime  = p.stat().st_ctime
            except (PermissionError, FileNotFoundError) as e:
                self.nm.notify('error', "Erreur", e.strerror,duration=2)
                continue

            self.entries.append((p, is_dir, ctime))

            # détection “level” pour les JSON
            if p.suffix.lower() == ".json":
                is_lvl = False
                try:
                    is_lvl = False
                    with open(p, "r", encoding="utf-8") as f:
                        line_iter = iter(f)
                        for line in line_iter:
                            if '"layers"' in line:
                                for _ in range(10):
                                    try:
                                        next_line = next(line_iter)
                                    except StopIteration:
                                        break
                                    if '"opacity"' in next_line:
                                        is_lvl = True
                                        break
                                break

                except Exception:
                    pass
                self.is_level[str(p)] = is_lvl

        self.filtered     = list(self.entries)
        self.scroll       = 0
        self.selected_idx = None

    def _on_save(self,text):
        self.selected_idx = None


    def _on_search(self, text):
        t = text.strip().lower()
        patterns = [t]  # par défaut, recherche textuelle
        is_glob = False

        # S'il y a un * ou ?, on considère que c'est un filtre de type glob
        if any(char in t for char in '*?'):
            patterns = [p.strip() for p in t.split(';') if p.strip()]
            is_glob = True

        if is_glob:
            self.filtered = [e for e in self.entries if any(fnmatch.fnmatch(e[0].name.lower(), pat) for pat in patterns)]
        else:
            self.filtered = [e for e in self.entries if t in e[0].name.lower()]

        self.scroll = 0
        self.selected_idx = None


    def _roots(self):
        roots = []
        home = Path.home()
        roots.append(home)

        classic = {
            'Desktop':       ['Desktop', 'Bureau'],
            'Downloads':     ['Downloads', 'Téléchargements'],
            'Documents':     ['Documents', 'Documents'],
            'Pictures':      ['Pictures', 'Images'],
            'Music':         ['Music', 'Musique'],
            'Videos':        ['Videos', 'Vidéos']
        }
        for eng_key, variants in classic.items():
            for name in variants:
                p = home / name
                if p.exists():
                    roots.append(p)
                    break

        # Windows
        if platform.system() == 'Windows':
            from string import ascii_uppercase
            for l in ascii_uppercase:
                drive = Path(f"{l}:/")
                if drive.exists():
                    roots.append(drive)

        # Unix (macOS / Linux)
        else:
            roots.append(Path('/'))

            # /mnt
            try:
                for m in Path('/mnt').iterdir():
                    if m.is_dir(): roots.append(m)
            except: pass

            # /Volumes (macOS)
            try:
                for vol in Path('/Volumes').iterdir():
                    if vol.is_dir() and vol != Path('/Volumes/Macintosh HD'):
                        roots.append(vol)
            except: pass

            # /media (Linux / Ubuntu)
            try:
                for user_media in Path('/media').iterdir():
                    if user_media.is_dir():
                        for vol in user_media.iterdir():
                            if vol.is_dir():
                                roots.append(vol)
            except: pass

        return roots


    def _scroll_by(self, delta):
        total_h = self._total_content_height()
        max_s = max(0, total_h-self.grid_rect.h)
        self.scroll = max(0, min(self.scroll+delta, max_s))

    def _update_hover_idx(self, mx, my):
        rx, ry = mx - self.rect.x, my - self.rect.y
        self.hover_idx = None

        if not self.grid_rect.collidepoint(rx, ry):
            return

        cols = max(1, self.grid_rect.w // self.ITEM_W)

        for idx, (p, is_dir, _) in enumerate(self.filtered):
            row, col = divmod(idx, cols)
            x = self.grid_rect.x + self.OFFSET_X + col * (self.ITEM_W + self.SPACING_X)
            y = self.grid_rect.y + self.OFFSET_Y + row * (self.ITEM_H + self.SPACING_Y) - self.scroll
            case_rect = pygame.Rect(x, y, self.ITEM_W - 4, self.ITEM_H - 4)
            if case_rect.collidepoint(rx, ry):
                self.hover_idx = idx
                break


    def handle_event(self,event):
        self.dlg_confirm.handle_event(event)
        if self.dlg_confirm.active:
            return
        # Translate event to dialog-relative coords
        if hasattr(event, 'pos'):
            mx, my = event.pos
            rx, ry = mx - self.rect.x, my - self.rect.y
        else:
            rx = ry = None

        # Forward events to search InputField
        if hasattr(event,'pos'):
            ev=pygame.event.Event(event.type,{**event.__dict__,'pos':(rx-self.search_rect.x,ry-self.search_rect.y)})
            self.search.handle_event(ev)
        else: self.search.handle_event(event)
        # — En mode save, forward events au champ filename_input —
        if self.mode == 'save':
            self.filename_input.handle_event(event)
        if self.mode == 'save' and hasattr(event, 'pos'):
            ex, ey = event.pos
            # si on clique ou on bouge la souris DANS self.filename_rect
            global_fx = self.rect.x + self.filename_rect.x
            global_fy = self.rect.y + self.filename_rect.y
            if (global_fx <= ex <= global_fx + self.filename_rect.w
                and global_fy <= ey <= global_fy + self.filename_rect.h):
                # traduire coords pour filename_input
                local = (ex - global_fx, ey - global_fy)
                ev = pygame.event.Event(event.type,
                    {**event.__dict__, 'pos': local})
                self.filename_input.handle_event(ev)
                # on ne propage **pas** plus bas pour éviter le drag
                return


        # Scroll wheel
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if self.grid_rect.collidepoint(rx, ry) or self.scrollbar_rect.collidepoint(rx, ry):
                self._scroll_by(-self.SCROLL_STEP if event.button == 4 else self.SCROLL_STEP)
                mx, my = pygame.mouse.get_pos()
                self._update_hover_idx(mx, my)
                return

        # Scrollbar drag
        if event.type == pygame.MOUSEBUTTONDOWN and self.scrollbar_rect.collidepoint(rx, ry):
            cols = max(1, self.grid_rect.w // self.ITEM_W)
            total_h = self._total_content_height()
            if total_h > self.grid_rect.h:
                thumb_h = self.grid_rect.h * self.grid_rect.h / total_h
                thumb_y = self.scrollbar_rect.y + self.scroll * self.grid_rect.h / total_h
                thumb_rect = pygame.Rect(self.scrollbar_rect.x, thumb_y, self.SCROLLBAR_W, thumb_h)
                if thumb_rect.collidepoint(rx, ry):
                    self.drag_scroll = True
                    self.scroll_y0 = ry
                    self.scroll_start = self.scroll
                return
        if event.type == pygame.MOUSEMOTION and self.drag_scroll:
            dy = ry - self.scroll_y0
            cols = max(1, self.grid_rect.w // self.ITEM_W)
            total_h = self._total_content_height()
            max_s = max(0, total_h - self.grid_rect.h)
            self.scroll = int(max(0, min(self.scroll_start + dy * total_h / self.grid_rect.h, max_s)))
            return

        # Mise à jour du hover quand la souris bouge
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._update_hover_idx(mx, my)

        # --- Hover breadcrumb ---
        if event.type == pygame.MOUSEMOTION and hasattr(event, 'pos'):
            mx, my = event.pos
            rx, ry = mx - self.rect.x, my - self.rect.y
            self.hover_bc = None
            for i, (rc, path) in enumerate(self.breadcrumb_segments):
                if rc.collidepoint(rx, ry):
                    self.hover_bc = i
                    break

        # Always reset drags on mouse up
        if event.type == pygame.MOUSEBUTTONUP:
            self.drag = False
            self.drag_scroll = False

        # Back navigation (mouse button 8)
        if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 8 or event.button == 6) and self.cwd.parent:
            self.cwd = self.cwd.parent
            self._load_entries()
            return

        # Header drag
        if event.type == pygame.MOUSEBUTTONDOWN and ry is not None and ry <= self.header_h and event.button == 1:
            self.drag = True
            self.drag_off = (rx, ry)
            return
        if event.type == pygame.MOUSEMOTION and self.drag:
            nx = event.pos[0] - self.drag_off[0]
            ny = event.pos[1] - self.drag_off[1]
            sw, sh = pygame.display.get_surface().get_size()
            w, h = self.rect.size
            self.rect.topleft = (max(0, min(nx, sw - w)), max(0, min(ny, sh - h)))
            return

        # Mouse button up actions for close/confirm
        if event.type == pygame.MOUSEBUTTONUP and hasattr(event, 'button') and event.button == 1:
            # Close button
            cx, cy = self.close_c
            if (rx - cx) ** 2 + (ry - cy) ** 2 <= self.close_r ** 2:
                self.on_cancel()
                return
            # Confirm button
            if self.btn_rect.collidepoint(rx, ry):
                # En open, comportement existant
                if self.mode == 'open' and self.selected_idx is not None:
                    p, is_dir, _ = self.filtered[self.selected_idx]
                    if is_dir:
                        self.cwd = p; self._load_entries()
                    else:
                        self._config[self.mode] = str(self.cwd)
                        self._save_config(self._config)
                        self.on_confirm(str(p))
                # En save : récupérer le texte du champ
                elif self.mode == 'save':
                    name = self.filename_input.text.strip()
                    if name:
                        target = str(self.cwd / name)
                        if (self.cwd / name).exists():
                            self.dlg_confirm.active=True
                        else:
                            self._config[self.mode] = str(self.cwd)
                            self._save_config(self._config)
                            self.on_confirm(target)
                return


        # Tree view click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.tree_rect.collidepoint(rx, ry):
                title_h = self.font.get_height()
                y0 = self.tree_rect.y + 6 + title_h + 4
                idx = (ry - y0) // (title_h + 8)
                roots = self._roots()
                if 0 <= idx < len(roots):
                    self.selected_root = idx
                    self.cwd = roots[idx]
                    self._load_entries()
                return


        # Breadcrumb click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, path in self.breadcrumb_segments:
                if rect.collidepoint(rx, ry):
                    self.cwd = path
                    self._load_entries()
                    return

        # Grid click/double-click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.grid_rect.collidepoint(rx, ry):
            cols = max(1, self.grid_rect.w // self.ITEM_W)
            # On parcourt chaque item pour retrouver celui dont la case contient (rx,ry)
            for idx, (p, is_dir, _) in enumerate(self.filtered):
                row, col = divmod(idx, cols)
                x = self.grid_rect.x + self.OFFSET_X + col * (self.ITEM_W + self.SPACING_X)
                y = self.grid_rect.y + self.OFFSET_Y + row * (self.ITEM_H + self.SPACING_Y) - self.scroll
                case_rect = pygame.Rect(x, y, self.ITEM_W - 4, self.ITEM_H - 4)
                if case_rect.collidepoint(rx, ry):
                    now = pygame.time.get_ticks()
                    # double-click ?
                    if self.selected_idx == idx and now - self.last_click_time < self.DOUBLE_CLICK_MS:
                        if is_dir:
                            self.cwd = p
                            self._load_entries()
                        else:
                            if not self.mode == 'save':
                                self._config[self.mode] = str(self.cwd)
                                self._save_config(self._config)
                                self.on_confirm(str(p))
                            else:
                                if p.exists():
                                    self.dlg_confirm.active=True
                                else:
                                    self._config[self.mode] = str(self.cwd)
                                    self._save_config(self._config)
                                    self.on_confirm(str(p))

                    else:
                        self.selected_idx = idx
                        self.last_click_time = now
                        if self.mode == 'save' and not is_dir:
                            self.filename_input.text = p.name
                        break
                    break  # on sort de la boucle dès qu'on a trouvé
            return


        # Keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.selected_idx is not None:
                p, is_dir, _ = self.filtered[self.selected_idx]
                if is_dir:
                    self.cwd = p
                    self._load_entries()
                else:
                    self._config[self.mode] = str(self.cwd)
                    self._save_config(self._config)
                    self.on_confirm(str(p))
                return
            if event.key == pygame.K_ESCAPE:
                self.on_cancel()
                return

    def draw(self, surf):
        # fond du dialog
        self.surface.fill(self.bg)

        # header + titre + close
        pygame.draw.rect(self.surface, self.border, (0,0,self.rect.w,self.header_h))
        title = "Open File" if self.mode=='open' else "Save File"
        self.surface.blit(self.font.render(title, True, (200,200,200)), (8,6))
        try:
            pygame.draw.aacircle(self.surface, (200,71,88), self.close_c, self.close_r)
        except:
            pygame.draw.circle(self.surface, (200,71,88), self.close_c, self.close_r+1)
        # Hauteur nécessaire pour le breadcrumb (paddings + hauteur de texte + paddings)
        # Rectangle de la zone
        bc_zone = pygame.Rect(
            0,                        # tout en haut de ton dialog
            self.header_h+14,            # juste sous le header
            360,              # pleine largeur
            24
        )

        # Fond de la zone (couleur un peu plus claire ou foncée que bg)
        pygame.draw.rect(self.surface, (41, 41, 41), bc_zone,border_bottom_right_radius=3,border_top_right_radius=3)

        # 1) Fil d’Ariane
        x = self.PADDING
        bc_y = self.header_h + self.PADDING + 12
        drive = self.cwd.drive
        rest  = self.cwd.parts[1:]
        parts = [drive] + list(rest)

        sep = "  >  "

        # on travaille sur la liste brute de segments
        full = self.cwd.parts

        # rendus des textes
        rendered = [self.font.render(seg, True, (180,180,180)) for seg in full]
        widths  = [surf.get_width() for surf in rendered]
        heights = [surf.get_height() for surf in rendered]
        sep_surf = self.font.render(sep, True, (180,180,180))
        sep_w = sep_surf.get_width()

        total_w = sum(widths) + sep_w*(len(parts)-1)
        max_w = self.rect.w - 2*self.PADDING - 20 - self.search_rect.width

        start_idx = 0
        if total_w > max_w:
            total = widths[-1]
            count = 1
            ell_w = self.font.size("…"+sep)[0]
            for i in range(len(parts)-2, -1, -1):
                w_seg = widths[i] + sep_w
                if total + w_seg + ell_w <= max_w:
                    total += w_seg
                    count += 1
                else:
                    break
            start_idx = len(parts) - count
            ell = self.font.render("…"+sep, True, (180,180,180))
            self.surface.blit(ell, (x, bc_y))
            x += ell.get_width()

        # affichage
        self.breadcrumb_segments.clear()

        for j, seg in enumerate(full[start_idx:]):
            # on reprend rendered[start_idx + j] pour le texte, etc
            txt_surf = rendered[start_idx + j]
            w, h = widths[start_idx + j], heights[start_idx + j]
            rect = pygame.Rect(x, bc_y, w, h)

            # hover sur segment j ?
            if j == self.hover_bc:
                pygame.draw.rect(self.surface, (70,70,70), rect, border_radius=2)

            # dessine le texte
            self.surface.blit(txt_surf, (x, bc_y))

            # mémorise le rect pour le click & hover
            cum_path = Path(*full[:start_idx + j + 1])
            self.breadcrumb_segments.append((rect, cum_path))

            x += w
            if start_idx + j < len(full)-1:
                self.surface.blit(sep_surf, (x, bc_y))
                x += sep_w

        # 2) Search input (fixe)
        sr_s = pygame.Surface(self.search_rect.size, pygame.SRCALPHA)
        self.search.surface = sr_s
        # input interne de 0,0 à w,h
        self.search.rect = pygame.Rect(0,0, self.search_rect.width, self.search_rect.height)
        self.search.draw(sr_s)
        self.surface.blit(sr_s, (self.search_rect.topleft[0],self.search_rect.topleft[1]+6))

        # === panneau de gauche “Emplacements”  ===


        # 2) titre
        title = self.font.render("Emplacements", True, (200,200,200))
        title_rect = title.get_rect(midtop=(self.tree_rect.centerx, self.tree_rect.y + 6))
        self.surface.blit(title, title_rect)

        # 3) liste des racines
        roots = self._roots()
        line_h = self.font.get_height() + 8
        y = title_rect.bottom + 4

        for idx, p in enumerate(roots):
            line_rect = pygame.Rect(
                self.tree_rect.x + 8,
                y + idx * line_h,
                self.tree_rect.width - 16,
                line_h
            )

            # hover
            mx, my = pygame.mouse.get_pos()
            rx, ry = mx - self.rect.x, my - self.rect.y
            if line_rect.collidepoint(rx, ry):
                pygame.draw.rect(self.surface, (70,70,70), line_rect, border_radius=3)
                self.hover_root = idx
            # selected (si tu gères self.selected_root)
            if getattr(self, 'selected_root', None) == idx:
                pygame.draw.rect(self.surface, (70,130,180), line_rect, border_radius=3)

            def find_icon_key(name):
                classic = {
                    'Desktop':       ['Desktop', 'Bureau'],
                    'Downloads':     ['Downloads', 'Téléchargements'],
                    'Documents':     ['Documents', 'Documents'],
                    'Pictures':      ['Pictures', 'Images'],
                    'Music':         ['Music', 'Musique'],
                    'Videos':        ['Videos', 'Vidéos']
                }
                name_l = name.lower()
                if name_l == Path.home().name.lower(): return 'user'
                if (platform.system()=='Windows' and p.anchor == p.as_posix()+"\\") \
                   or p == Path(p.anchor): return 'drive'
                for eng_key, variants in classic.items():
                    if name in variants or name_l in (v.lower() for v in variants):
                        return eng_key.lower()
                return 'default'

            key = find_icon_key(p.name)

            icon_surf = self.root_icons.get(key, self.root_icons['default'])
            ico_rect = icon_surf.get_rect()
            ico_rect.topleft = (line_rect.x, line_rect.y + (line_h - ico_rect.height)//2)
            self.surface.blit(icon_surf, ico_rect)

            # nom du dossier
            name_surf = self.font.render(p.name or str(p), True, (230,230,230))
            self.surface.blit(name_surf, (ico_rect.right + 6, line_rect.y + (line_h - name_surf.get_height())//2))

        # 4) redessiner la bordure du panneau
        pygame.draw.rect(self.surface, self.border, self.tree_rect, width=1, border_radius=3)

                # grid clipped
        pygame.draw.rect(self.surface,self.border,self.grid_rect,1,border_radius=3)
        clip=self.surface.get_clip(); self.surface.set_clip(self.grid_rect)
        x0,y0=self.grid_rect.topleft; cols=self.grid_rect.w//self.ITEM_W
        for idx,(p,is_dir,ctime) in enumerate(self.filtered):
            row, col = divmod(idx, cols)
            x = x0 + self.OFFSET_X + col*(self.ITEM_W + self.SPACING_X)
            y = y0 + self.OFFSET_Y + row*(self.ITEM_H + self.SPACING_Y) - self.scroll
            rect = pygame.Rect(x, y, self.ITEM_W-4, self.ITEM_H-4)
            if rect.bottom<self.grid_rect.top or rect.top>self.grid_rect.bottom: continue
            # background
            bg=(55,55,55) if idx==self.hover_idx else (41,41,41)
            pygame.draw.rect(self.surface,bg,rect,border_radius=3)
            # selected border (drawn after background)
            if idx==self.selected_idx:
                pygame.draw.rect(self.surface,(70,130,180),rect,2,border_radius=3)
            # icon
            if is_dir:
                icon = self.icons['folder']
            else:
                self.current_file_path = str(p)
                icon = self._get_icon(p.suffix, str(p))
            if icon: self.surface.blit(icon,(x+4,y+12))
            # name
            name=p.name
            txt=self.font.render(name,True,(200,200,200))
            max_w=self.ITEM_W-self.ICON_SIZE-16
            if txt.get_width()>max_w:
                while txt.get_width()>max_w and len(name)>3:
                    name=name[:-1]
                    txt=self.font.render(name+'…',True,(200,200,200))
            self.surface.blit(txt,(x+self.ICON_SIZE+13,y+14))
            # date
            import datetime
            d=datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%d')
            dtxt=self.font2.render(d,True,(150,150,150))
            self.surface.blit(dtxt,(x+self.ICON_SIZE+13,y+18+txt.get_height()))
        self.surface.set_clip(clip)
        # scrollbar
        total_h = self._total_content_height()
        if total_h>self.grid_rect.h:
            pygame.draw.rect(self.surface,(80,80,80),self.scrollbar_rect,border_radius=3)
            th=self.grid_rect.h*self.grid_rect.h/total_h; ty=self.scrollbar_rect.y+self.scroll*self.grid_rect.h/total_h
            pygame.draw.rect(self.surface,(160,160,160),pygame.Rect(self.scrollbar_rect.x,ty,self.SCROLLBAR_W,th),border_radius=3)
        # confirm button
        # Confirm button
        label = 'Open' if self.mode=='open' else 'Save'
        pygame.draw.rect(self.surface, (70,130,180), self.btn_rect, border_radius=4)
        txt = self.font.render(label, True, (255,255,255))
        trect = txt.get_rect(center=self.btn_rect.center)
        self.surface.blit(txt, trect)

        # En mode save : dessiner le champ de saisie
        if self.mode == 'save':
            # champ
            sf = pygame.Surface(self.filename_rect.size, pygame.SRCALPHA)
            self.filename_input.surface = sf
            self.filename_input.draw(sf)
            self.surface.blit(sf, (self.filename_rect.x,
                                   self.filename_rect.y))

        # border
        pygame.draw.rect(self.surface,(62,62,62),(0,0,self.rect.w,self.rect.h),1,4)
        surf.blit(self.surface,self.rect.topleft)
        self.dlg_confirm.draw(surf)


if __name__=='__main__':
    pygame.init()
    screen=pygame.display.set_mode((800,600),pygame.RESIZABLE)
    clock=pygame.time.Clock()
    nm = NotificationManager()
    dlg=FileDialog((100,100,600,400),nm,mode='open',on_confirm=lambda p:print('Sel',p),on_cancel=lambda:print('Cancel'),icon_dir="./Assets/ui/icones/fileDialog/")
    r=True
    while r:
        dt = clock.tick() / 1000.0
        for e in pygame.event.get():
            if e.type==pygame.QUIT: r=False
            dlg.handle_event(e)
        
        nm.update(dt)
        screen.fill((20,20,20))
        dlg.draw(screen)
        nm.draw(screen)
        pygame.display.flip()
