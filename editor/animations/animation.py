from typing import Dict, Optional, Tuple
from editor.ui.CheckBox import Checkbox
from editor.ui.DialogSystem import DialogBox
from editor.ui.DropDownMenu import MenuButton, MenuItem
from editor.ui.ImageButton import ImageButton
from editor.ui.Notifications import NotificationManager
from editor.animations.timeLine import Timeline
from editor.core.utils import AnimatedTile, Tools
import pygame
import copy
import sys

class Animation:
    def __init__(self,on_click, name: str, start: float, end: float, speed: float = 1.0):
        self.name = name
        self.timeline = Timeline(on_click,start, end)
        self.timeline.active = False
        self.display_keyframes = False
        self.speed = speed

    def play(self, loop: bool = False):
        self.timeline.playing = True
        self.timeline.loop = loop
        if self.timeline.current >= self.timeline.end:
            self.timeline.current = self.timeline.start

    def pause(self):
        self.timeline.playing = False

    def stop(self):
        self.timeline.playing = False
        self.timeline.current = self.timeline.start

    def update(self, dt: float):
        self.timeline.update(dt * self.speed)

    def rename(self, new_name: str):
        self.name = new_name

    def get_current_states(self):
        return self.timeline.get_animation_states()

    def draw(self, screen: pygame.Surface):
        self.timeline.draw(screen)

    def record(self, tile: AnimatedTile,data_manager):
        tile.time = self.timeline.current
        data_manager.history.RegisterAddKeyframe(
            animation_name=self.name,
            new_kf=copy.deepcopy(tile),
            anim=self
        )
        self.timeline.add_keyframe(tile)


class AnimationManager:
    def __init__(self, screen: pygame.Surface, notification: NotificationManager,timeline_click):
        self.screen       = screen
        self.nm           = notification
        self.timeline_click = timeline_click

        # --- Panel settings ---
        self.panel_w      = 250
        self.panel_h      = 230
        self.panel_rect   = pygame.Rect(
            self.screen.get_width() - 230, 30,
            210, 200
        )
        self.hide_rect = pygame.Rect(0, 0, 20, 20)
        self.hide_rect.topleft = (
            self.panel_rect.right - self.hide_rect.width - 8,
            self.panel_rect.y + 14
        )
        self.panel_bg_color = (47, 47, 47)
        self.panel_border_radius = 3
        self.panel_visible = False

        

        # --- Animations data ---
        self.animations: Dict[str, Animation] = {}
        self.current_name: Optional[str] = None

        # Fonts
        self.button_font = pygame.font.Font(None, 18)
        self.item_font  = pygame.font.Font(None, 16)
        self.label_font = pygame.font.Font(None, 23)
        self.x_font = pygame.font.Font(None, 27)

        # Dropdown menu (centré)
        dropdown_w, dropdown_h = 120, 25
        dropdown_x = self.panel_rect.centerx - dropdown_w // 2
        dropdown_y = self.panel_rect.y + 10
        self.anim_menu = MenuButton(
            rect=(dropdown_x, dropdown_y, dropdown_w, dropdown_h),
            text="Aucune",
            submenu_items=[],
            font=self.button_font,
            border_radius=2
        )
        self.anim_menu.dropdown.width_multiplier=1.25

        # ImageButtons
        btn_size = 24
        margin_left = 175
        # Delete
        self.delete_btn = ImageButton(
            rect=(self.panel_rect.x + margin_left, dropdown_y + 60, btn_size, btn_size),
            image_path="./Assets/ui/icones/delete.png",
            action=self._ask_delete_current
        )
        # Edit
        self.edit_btn = ImageButton(
            rect=(self.panel_rect.x + margin_left, dropdown_y + 100, btn_size, btn_size),
            image_path="./Assets/ui/icones/edit.png",
            action=self._open_edit_dialog
        )
        # Keyframes Toggle
        self.keyframe_btn = Checkbox(
            rect=(self.panel_rect.x + margin_left, dropdown_y + 140, btn_size, btn_size),
            checked_image_path="./Assets/ui/icones/eyesopen.png",
            unchecked_image_path="./Assets/ui/icones/eyesclose.png",
            initial_state=False,
            action=self._toggle_keyframes
        )

        self.dialog: Optional[DialogBox] = None

    def _toggle_keyframes(self,status):
        self.get_current_anim().display_keyframes = status

    def _toggle_panel(self):
        self.panel_visible = not self.panel_visible

    def _ask_delete_current(self):
        if self.current_name is None:
            return
        if len(self.animations)==1:
            self.nm.notify('warning', 'Attention', f"Une animation est au moins nécessaire.", duration=1.5)
            return
        if self.ask_confirmation(f"Etes vous sûr de vouloir suprimmer \" {self.current_name} \" ?"):
            self._delete_current()

    def _delete_current(self):
        name = self.current_name
        del self.animations[name]
        self.nm.notify('success', 'Succès',f"Animation \"{name}\" supprimée.", duration=1.5)

        if self.animations:
            new_current = next(iter(self.animations))
            self.current_name = new_current
            self.set_current(new_current)
        else:
            self.current_name = None
            self.anim_menu.text = "Aucune"
            self.anim_menu.text_surf = self.button_font.render(
                "Aucune", True, self.anim_menu.text_color
            )
            self.anim_menu.dropdown.items = []

    
    def ask_confirmation(self, message: str) -> bool:
        result = {'ok': False}

        def on_yes():
            result['ok'] = True
            dialog.active = False

        def on_no():
            dialog.active = False

        dialog = DialogBox(
            rect=(self.screen.get_width()/2 - 150,
                  self.screen.get_height()/2 - 50,
                  300, 100),
            title="Confirmation",
            description=message,
            buttons=[
                {'text': 'Oui', 'callback': on_yes},
                {'text': 'Non', 'callback': on_no},
            ],
            on_cancel=on_no,
            font=pygame.font.Font(None, 18)
        )

        clock = pygame.time.Clock()
        bg = self.screen.copy()
        while dialog.active:
            dt = clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                dialog.handle_event(e)

            self.screen.blit(bg, (0, 0))
            dialog.draw(self.screen)
            pygame.display.flip()

        return result['ok']


    def sync(self):
        for animation in self.animations.values():
            if animation.timeline.playing:
                animation.timeline.current=0.0
        self.nm.notify('success', 'Success',f"Animations synchronisées avec succès.",duration=1.5)

    def _on_select_animation(self, anim_name: str):
        self.set_current(anim_name)

    def mouse_on_timeline(self):
        return self.current_name and self.animations[self.current_name].timeline.mouse_on()

    def create(self, name: str, end: float,on_load=False):
        if name in self.animations:
            print(f"Animation '{name}' existe déjà.")
            self.nm.notify('error', 'Erreur', f"Animation '{name}' existe déjà.",duration=2)
            return
        self.animations[name] = Animation(self.timeline_click,name, 0.0, end)

        if self.current_name is None:
            self.current_name = name
            self.animations[name].timeline.active = True

        self.set_current(name)
        if name!="animation_1" and not on_load:
            self.nm.notify('success', 'Success',f"Nouvelle animation \"{name}\" créée.",duration=1.5)
        else:
            self.toogleTimeline()

    def set_current(self, name: str):
        if name not in self.animations:
            print(f"Animation '{name}' introuvable.")
            self.nm.notify('error', 'Erreur', f"Animation '{name}' introuvable.",duration=2)
            return
        if self.current_name is not None:
            self.animations[self.current_name].timeline.active = False

        self.current_name = name
        self.animations[name].timeline.active = True

        # mettre à jour l’étiquette du bouton principal
        self.anim_menu.text = name
        self.anim_menu.text_surf = self.button_font.render(name, True, self.anim_menu.text_color)

        self.keyframe_btn.state=self.get_current_anim().display_keyframes
        # reformater le menu
        self._rebuild_anim_menu()

        self.get_current_anim().timeline.update_rect()

    def _rebuild_anim_menu(self):
        items = [(anim_name, lambda nm=anim_name: self.set_current(nm))
                 for anim_name in self.animations]

        menu_items = [MenuItem(text, action, self.item_font)
                      for text, action in items]

        self.anim_menu.dropdown.items = menu_items
        self.anim_menu.dropdown._layout_items()


    def handle_event(self, event):
        if self.dialog:
            return self.dialog.handle_event(event)
        if not self.panel_visible:
            return

        self.anim_menu.handle_event(event)
        if self.anim_menu.dropdown.is_open:
            return
        self.delete_btn.handle_event(event)
        self.edit_btn.handle_event(event)
        self.keyframe_btn.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hide_rect.collidepoint(event.pos):
                self.panel_visible = False

    def update_rect(self):
        self.panel_rect   = pygame.Rect(
            self.screen.get_width() - 230, 30,
            210, 200
        )
        self.hide_rect.topleft = (
            self.panel_rect.right - self.hide_rect.width - 8,
            self.panel_rect.y + 14
        )
        dropdown_w, dropdown_h = 120, 25
        dropdown_x = self.panel_rect.centerx - dropdown_w // 2
        dropdown_y = self.panel_rect.y + 10
        self.anim_menu.rect=pygame.Rect(dropdown_x, dropdown_y, dropdown_w, dropdown_h)
        self.anim_menu.dropdown._layout_items()
        btn_size = 24
        margin_left = 175
        self.delete_btn.rect=pygame.Rect(self.panel_rect.x + margin_left, dropdown_y + 60, btn_size, btn_size)
        self.edit_btn.rect=pygame.Rect(self.panel_rect.x + margin_left, dropdown_y + 100, btn_size, btn_size)
        self.keyframe_btn.rect=pygame.Rect(self.panel_rect.x + margin_left, dropdown_y + 140, btn_size, btn_size)
        


    def get_current_anim(self):
        return self.animations.get(self.current_name)

    def play(self, loop: bool = False):
        if self.current_name is None:
            return
        self.animations[self.current_name].play(loop)

    def pause(self):
        if self.current_name is None:
            return
        self.animations[self.current_name].pause()

    def stop(self):
        if self.current_name is None:
            return
        self.animations[self.current_name].stop()

    def record_tile(self, tile: AnimatedTile,datamanager):
        if self.current_name is None:
            return
        self.animations[self.current_name].record(tile,datamanager)

    def update(self, dt: float,dataManager):
        for anim in self.animations.values():
            anim.update(dt)
        if self.dialog and dataManager.currentTool:
            dataManager.currentTool=Tools.Selection

    def draw(self):
        if self.current_name:
            self.animations[self.current_name].draw(self.screen)

        if not self.panel_visible:
            return

        pygame.draw.rect(
            self.screen,
            self.panel_bg_color,
            self.panel_rect,
            border_radius=self.panel_border_radius
        )
        x_surf = self.x_font.render("x", True, (220,220,220))
        x_rect = x_surf.get_rect(center=self.hide_rect.center)
        self.screen.blit(x_surf, x_rect)

        lbl_x = self.panel_rect.x + 10
        suppr_lbl = self.label_font.render("Supprimer :", True, (255,255,255))
        self.screen.blit(suppr_lbl, (lbl_x, self.panel_rect.y + 75))
        self.delete_btn.draw(self.screen)

        edit_lbl = self.label_font.render("Modifier :", True, (255,255,255))
        self.screen.blit(edit_lbl, (lbl_x, self.panel_rect.y + 115))
        self.edit_btn.draw(self.screen)

        key_lbl = self.label_font.render("Afficher keyframes :", True, (255,255,255))
        self.screen.blit(key_lbl, (lbl_x, self.panel_rect.y + 155))
        self.keyframe_btn.draw(self.screen)

        self.anim_menu.draw(self.screen)
        
        if self.dialog:
            self.dialog.draw(self.screen)

    def get_current_states(self) -> Dict[str, Dict[Tuple[int, int, int], AnimatedTile]]:
        """
        Retourne un dict dont chaque clé est le nom d'une animation,
        et chaque valeur est le mapping { (x,y,layer): AnimatedTile }
        pour l'état courant (ou pour 'time' si fourni).
        """
        all_states: Dict[str, Dict[Tuple[int,int,int], AnimatedTile]] = {}
        for name, anim in self.animations.items():
            states = anim.get_current_states()  
            all_states[name] = states
        return all_states

    def _open_edit_dialog(self):
        anim = self.get_current_anim()
        if anim is None:
            return

        self._old_speed = anim.speed
        self._old_end   = anim.timeline.end
        self._old_name  = self.current_name

        inputs = [
            {'label': 'Nom :',         'placeholder': 'idle', 'text': str(self.current_name),
             'rules': [lambda ch: ch.isalnum() or ch == '_']},
            {'label': 'Fin   (s) :',   'placeholder': '0.0',  'text': str(anim.timeline.end),
             'rules': [lambda ch: ch.isdigit() or ch == '.']},
            {'label': 'Vitesse   :',   'placeholder': '1.0',  'text': str(anim.speed),
             'rules': [lambda ch: ch.isdigit() or ch == '.']}
        ]

        buttons = [
            {'text': 'Valider', 'callback': self._apply_edit}
        ]

        self.dialog = DialogBox(
            rect=(self.panel_rect.x + 20,
                  self.panel_rect.y + 50,
                  250, 220),
            title="Éditer Animation",
            description="",
            buttons=buttons,
            inputs=inputs,
            on_cancel=self._cancel_edit,
            font=pygame.font.Font(None, 18)
        )

        # override live-change sur la vitesse comme avant
        for kind, widget, _ in self.dialog._renderables:
            if kind == 'input' and widget.placeholder == '1.0':
                speed_field = widget
                break
        else:
            speed_field = None

        if speed_field:
            def on_speed_change(txt, ip_ref=speed_field, anim=anim):
                try:
                    anim.speed = float(txt) if txt else 0.0
                except ValueError:
                    pass
                ip_ref.text = txt
            speed_field.on_change = on_speed_change


    def _apply_edit(self):
        anim = self.get_current_anim()
        if anim is None:
            return

        name_if, end_if, speed_if = self.dialog.inputs


        try:
            new_end   = float(end_if.text)
            new_speed = float(speed_if.text)
        except ValueError:
            self.nm.notify('warning', 'Attention',
                           'La durée et la vitesse doivent être des nombres.', duration=1.5)
            return

        new_name = name_if.text.strip()


        if not new_name:
            self.nm.notify('warning', 'Attention',
                           'Le nom ne peut pas être vide.', duration=1.5)
            return

        if new_name != self._old_name and new_name in self.animations:
            self.nm.notify('warning', 'Attention',
                           f"Le nom \" {new_name} \" existe déjà.", duration=1.5)
            return
        if new_end < 0.01:
            self.nm.notify('warning', 'Attention',
                           'La durée doit être ≥ 0.01 s.', duration=1.5)
            return
        if new_end > 1000:
            self.nm.notify('warning', 'Attention',
                           'La durée doit être ≤ 1000 s.', duration=1.5)
            return
        if new_speed <= 0:
            self.nm.notify('warning', 'Attention',
                           'La vitesse doit être > 0.', duration=1.5)
            return


        anim.timeline.end = new_end
        anim.timeline.compute_scale()
        anim.speed = new_speed

        if new_name != self._old_name:
            self.animations[new_name] = self.animations.pop(self._old_name)
            anim.name = new_name
            self.current_name = new_name


        self.anim_menu.text = self.current_name
        self.anim_menu.text_surf = self.button_font.render(
            self.current_name, True, self.anim_menu.text_color
        )
        self._rebuild_anim_menu()

        self.dialog = None
        self.nm.notify('success', 'Succès',
                       f"Animation \"{anim.name}\" mise à jour.", duration=1.5)



    def _cancel_edit(self):
        if self.current_name:
            anim = self.animations[self.current_name]
            anim.speed          = self._old_speed
            anim.timeline.end   = self._old_end
            anim.timeline.compute_scale()
        self.nm.notify('info', 'Information', "Édition de l'animation annulée.", duration=1.5)
        self.dialog = None


    def toogleTimeline(self):
        self.get_current_anim().timeline.active=not self.get_current_anim().timeline.active