import json
import os
import pygame
from enum import Enum, auto
from editor.core.utils import LocationPoint
from editor.ui.CheckBox import Checkbox
from editor.ui.ColorButton import ColorButton
from editor.ui.DropDownMenu import MenuButton
from editor.ui.Font import FontManager
from editor.ui.ImageButton import ImageButton
from editor.ui.Notifications import NotificationManager
from editor.ui.Selector import TextSelector
from typing import TYPE_CHECKING, Any, List, Tuple
from editor.ui.Slider import Slider
from editor.ui.TextButton import Button
if TYPE_CHECKING:
    from data_manager import DataManager

class Section(Enum):
    WORLD          = auto()
    PLAYER_PROFILE = auto()
    INTERFACE      = auto()
    ADVANCED       = auto()
    HIDDEN         = auto()

class SettingsManager:
    def __init__(self, screen: pygame.Surface, json_file: str,nm : NotificationManager):
        # Display panel setup
        self.screen = screen
        self.panel_w = 250
        self.panel_rect = pygame.Rect(
            screen.get_width() - self.panel_w, 0,
            self.panel_w, screen.get_height()
        )
        self.bg_color = (36, 36, 36)
        self.active_section: Section = Section.HIDDEN
        self.font_manager = FontManager()
        self.font = self.font_manager.get(size=24)
        self.font2 = self.font_manager.get(size=28)
        base, _ = os.path.splitext(json_file)
        self.settings_file = base + ".settings"


        # Configuration attributes
        self.global_illum: float = 0
        self.parallax_index: int = 0
        self.player_speed: float = 3.0
        self.gravity: float = 0.6
        self.jump_force: float = -10.0
        self.double_jump: bool = False
        self.ui_font_color: Tuple[int,int,int] = (255,255,255)
        self.panel_bg_color: Tuple[int,int,int] = (36,36,36)
        self.ui_scale: float = 1.0
        self.start_mode: int = 0
        self.display_lights: bool = True
        self.show_collisions: bool = True
        self.show_location_points: bool = True
        self.is_grid_visible: bool = True
        self.fps: bool = False
        self.drawn: bool = False
        self.keyframe_overlay: bool = True
        self.player_spawn_point: str | None = None
        self.can_fly: bool = False
        # Widgets container per section:
        # Section -> List of tuples(label, widget, setting, base_rect)
        self.widgets: dict[Section, List[Tuple[str, Any, str, pygame.Rect]]] = {
            sec: [] for sec in Section
        }
        self.backgrounds = []
        self.json_file=json_file
        self.nm=nm
        self.dataManager: DataManager = None
        self.hide_rect = pygame.Rect(0, 0, 20, 20)
        self.game_engine=None
        self.path=None
        self._load_saved_settings()

    def _load_saved_settings(self):
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "fps" in data:
                self.fps = bool(data["fps"])
            if "start_mode" in data:
                self.start_mode = int(data["start_mode"])
            if "last_path" in data:
                self.last_path = data["last_path"]
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[SettingsManager] Erreur en chargeant {self.settings_file}: {e}")

    def _save_settings(self):
        data = {
            "fps": int(self.fps),
            "start_mode": int(self.start_mode),
            "last_path":self.path
        }
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SettingsManager] Impossible de sauvegarder {self.settings_file}: {e}")


    def load_settings(self):
        self.widgets: dict[Section, List[Tuple[str, Any, str, pygame.Rect]]] = {
            sec: [] for sec in Section
        }
        with open(self.json_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        for section_block in config:
            sec_name = section_block.get("section")
            try:
                sec = Section[sec_name]
            except KeyError:
                continue

            y_offset = 50
            for widget_def in section_block.get("widgets", []):
                wtype    = widget_def.get("type")
                label    = widget_def.get("label", "")
                setting  = widget_def.get("setting")
                orig_rect = widget_def.get("rect", [0,0,0,0])
                base_rect = pygame.Rect(*orig_rect)

                base_rect.x = orig_rect[0]
                base_rect.y = y_offset + orig_rect[1]
                widget = None

                if wtype in ("Text", "Title"):
                    text = widget_def.get("text", label)
                    self.widgets[sec].append((text, None, None, base_rect.copy()))
                    # on incrémente le y_offset de façon dynamique
                    y_offset += base_rect.height + 35
                    continue

                # --- création des widgets interactifs ---
                if wtype == "Slider":
                    widget = Slider(
                        rect=base_rect.copy(),
                        min_value=widget_def.get("min_value", 0),
                        max_value=widget_def.get("max_value", 1),
                        initial_value=getattr(self, setting, 0),
                        progress_color=(109, 132, 165),
                        bar_color=(83, 89, 98)
                    )
                    widget.on_change = lambda v, s=setting: setattr(self, s, v)

                elif wtype == "Dropdown":
                    items = widget_def.get("items", [])
                    submenu = []
                    for item in items:
                        val = item.get("value")
                        submenu.append((item.get("text", ""), lambda v=val, s=setting: setattr(self, s, v)))
                    widget = MenuButton(
                        rect=base_rect.copy(),
                        text=widget_def.get("label", ""),
                        submenu_items=submenu,
                        font=self.font,
                        bg_color=tuple(widget_def.get("bg_color", (50,50,50))),
                        border_radius=2
                    )

                elif wtype == "Button":
                    widget = Button(
                        rect=base_rect.copy(),
                        text=widget_def.get("label", ""),
                        action=lambda s=setting: self._toggle_bool(s),
                        bg_color=(50,50,50)
                    )

                elif wtype == "ImageButton":
                    widget = ImageButton(
                        rect=base_rect.copy(),
                        image_path=widget_def.get("image_path"),
                        hover_image_path=widget_def.get("hover_image_path"),
                        action= (lambda: self.set_spawn_point()) if label == "Set Spawn Point:" else (lambda: self._toggle_bool(setting))

                    )

                elif wtype == "Checkbox":
                    widget = Checkbox(
                        rect=base_rect.copy(),
                        checked_image_path=widget_def.get("checked_image_path","./Assets/ui/icones/checked.png"),
                        unchecked_image_path=widget_def.get("unchecked_image_path","./Assets/ui/icones/unchecked.png"),
                        initial_state=getattr(self, setting, False),
                        action=lambda _, s=setting: self._toggle_bool(s)
                    )

                elif wtype == "ColorPicker":
                    widget = ColorButton(
                        rect=base_rect.copy(),
                        initial_color=getattr(self, setting, (0,0,0)),
                        action=lambda c, s=setting: setattr(self, s, c)
                    )

                elif wtype == "Selector":
                    default_idx = widget_def.get("default_index", 0)
                    if label=="Parallax":
                        items = self.backgrounds
                        default_idx = self.parallax_index
                    else:
                        items = widget_def.get("items", [])
                    
                    widget = TextSelector(
                        rect=base_rect.copy(),
                        options=items,
                        arrow_left=widget_def.get("arrow_left_path","./Assets/ui/icones/arrow_left.png"),
                        arrow_right=widget_def.get("arrow_right_path","./Assets/ui/icones/arrow_right.png"),
                        font=self.font,
                        on_change=lambda v, s=setting: setattr(self, s, v),
                        default_index=default_idx
                    )


                if widget:
                    self.widgets[sec].append((label, widget, setting, base_rect.copy()))
                    y_offset += base_rect.height + 25
        self.update_rect()


    def set_spawn_point(self):
        if isinstance(self.dataManager.selectedElement,LocationPoint):
            self.player_spawn_point=self.dataManager.selectedElement.name
            self.game_engine.player.rect.centerx,self.game_engine.player.rect.bottom=self.dataManager.selectedElement.rect[0],self.dataManager.selectedElement.rect[1]
            self.nm.notify('success', 'Success', f'{self.dataManager.selectedElement.name} défini comme Point de Spawn !',duration=1.0)
        else:
            self.nm.notify('warning', 'Attention', 'Veuillez d\'abord choisir un LocationPoint.', duration=1.5)

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        words = text.split()
        lines = []
        current_words: List[str] = []
        for word in words:
            test_words = current_words + [word]
            test_line = ' '.join(test_words)
            if self.font.size(test_line)[0] <= max_width:
                current_words = test_words
            else:
                if current_words:
                    lines.append(' '.join(current_words))
                current_words = [word]
        if current_words:
            lines.append(' '.join(current_words))
        return lines

    def update_rect(self):
        self.panel_rect = pygame.Rect(self.screen.get_width()-self.panel_w,0,self.panel_w,self.screen.get_height())
        self.hide_rect.topleft = (
            self.panel_rect.right - self.hide_rect.width - 8,
            self.panel_rect.y + 38
        )
        for widget_list in self.widgets.values():
            for _, widget, _, base_rect in widget_list:
                if widget is None:
                    continue
                widget.rect.topleft = (self.panel_rect.x + base_rect.x, base_rect.y)
                if hasattr(widget, 'dropdown'):
                    widget.dropdown._layout_items()

    def _toggle_bool(self, setting: str):
        current = getattr(self, setting, False)
        setattr(self, setting, not current)

    def change_section(self, section: Section):
        self.active_section = Section.HIDDEN if self.active_section == section else section

    def get_startmode_str(self,index):
        return ["NewEx","OldEx","Empty","LastLvl"][index]

    def update_startmode_dropdown(self):
        for widget in self.widgets[Section.ADVANCED]:
            if widget[2]=="start_mode":
               widget[1].text=self.get_startmode_str(self.start_mode)
               widget[1].text_surf = widget[1].font.render(widget[1].text, True, widget[1].text_color)

    def draw(self):
        if self.active_section == Section.HIDDEN:
            return

        # Fond du panel et titre
        pygame.draw.rect(self.screen, self.bg_color, self.panel_rect)
        y = 40
        title_surf = self.font.render(self.active_section.name.title(), True, (255,255,255))
        self.screen.blit(title_surf, (self.panel_rect.x + 10, y))

        x_surf = self.font2.render("x", True, (220,220,220))
        x_rect = x_surf.get_rect(center=self.hide_rect.center)
        self.screen.blit(x_surf, x_rect)

        title_bottom = y + title_surf.get_height() + 5
        start_x = self.panel_rect.x + 10
        end_x = self.panel_rect.right - 10

        pygame.draw.line(self.screen, (100, 100, 100), (start_x, title_bottom), (end_x, title_bottom), width=1)

        y = title_bottom + 10

        for label, widget, _, base_rect in self.widgets[self.active_section]:
            # 1) Texte statique (Text/Title)
            if widget is None:
                max_w = self.panel_w - (base_rect.x + 10)
                for i, line in enumerate(self._wrap_text(label, max_w)):
                    txt_surf = self.font.render(line, True, (200,200,200))
                    self.screen.blit(txt_surf, (self.panel_rect.x + base_rect.x,
                                                base_rect.y + i * self.font.get_linesize()))
                continue

            # 2) Positionnement absolu du widget
            widget.rect.topleft = (self.panel_rect.x + base_rect.x, base_rect.y)
            widget.draw(self.screen)

            # 3) Affichage du label
            if label == "Gravity":
                label+=f": {round(self.gravity,2)}"
            elif label == "Jump Force":
                label+=f": {round(self.jump_force,2)}"
            elif label == "Player Speed":
                label+=f": {round(self.player_speed,2)}"
            lbl_surf = self.font.render(label, True, (200,200,200))

            # Si c'est un slider ou un menu déroulant, on le place au-dessus
            if isinstance(widget, (Slider, MenuButton)):
                label_x = widget.rect.x
                label_y = widget.rect.y - lbl_surf.get_height() - 4
            elif isinstance(widget, TextSelector):
                label_x = widget.rect.x-34
                label_y = widget.rect.y - lbl_surf.get_height() - 4                
            else:
                # Ancien comportement : à gauche du widget
                label_x = widget.rect.x - lbl_surf.get_width() - 8
                label_y = widget.rect.y + (widget.rect.height - lbl_surf.get_height()) // 2
            
            self.screen.blit(lbl_surf, (label_x, label_y))




    def handle_event(self, event: pygame.event.Event):
        """Forward events to active section widgets."""
        if self.active_section == Section.HIDDEN:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (self.active_section != Section.HIDDEN
                    and self.hide_rect.collidepoint(event.pos)):
                self.change_section(self.active_section)
                return
            
        for _, widget, _, _ in self.widgets[self.active_section]:
            if widget is None:
                continue
            widget.handle_event(event)
