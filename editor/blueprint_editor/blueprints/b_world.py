import time
from typing import Tuple
import pygame
from editor.blueprint_editor.node import DropdownButton, Node, register_node
from editor.ui.ColorButton import ColorButton
from editor.ui.Font import FontManager
from editor.ui.Input import InputField




@register_node("Get Current Background", category="World")
class GetCurrentBackground(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Get Current Background", editor, properties)
        # on enlève les pins exec hérités
        self.inputs.clear()
        self.outputs.clear()
        # pin data de sortie : on renvoie le nom du background courant
        self.add_data_pin("background_name", True, "", "Name")
        self.height = 60

    def execute(self, context):
        dm = self.editor.LevelEditor.dataManager
        bg = dm.get_current_background()
        name = bg.get("name") if bg else ""
        self.properties["background_name"] = name
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        # on met à jour l'affichage en temps réel
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = self.properties["background_name"]
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 10, self.y - oy + 34))

@register_node("Set Current Background", category="World")
class SetCurrentBackground(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Current Background", editor, properties)

        self.add_data_pin("set_background_name", False, "", "bg name")
        self.add_data_pin("duration", False, properties.get("duration", 1.0), "duration")
        self.duration_field = InputField(
            rect=(0, 0, 60, 18),
            text=str(self.properties.get("duration", 1.0)),
            placeholder="Duration",
            on_change=lambda t: self._on_change("duration", t)
        )


        self.btn = DropdownButton(
            self,
            pygame.Rect(0, 40, 140, 24),
            list(editor.LevelEditor.dataManager.settings.backgrounds),
            callback=self._on_select
        )

        if self.properties.get('set_background_name'):
            self.btn.selected = self.properties['set_background_name']
        else:
            self.properties["set_background_name"] = self.btn.options[0] if self.btn.options else ""

        def make_updater(el, pin_name, x_offset=8, y_offset=0):
            def updater(nx, ny):
                pin = next(p for p in self.inputs if p.name == pin_name)
                px, py = pin.pos
                el.rect.topleft = (px + x_offset, py + y_offset - el.rect.h // 2)
            return updater

        self.duration_field.update_position = make_updater(self.duration_field, "duration")

        self.ui_elements = [self.duration_field, self.btn]
        self.height = 100

        for el in self.ui_elements:
            el.update_position(self.x, self.y)

    def _on_select(self, choice: str):
        self.properties["set_background_name"] = choice

    def _on_change(self, key, txt):
        try:
            self.properties[key] = float(txt)
        except ValueError:
            pass
    def updateDropDownField(self):
        opts = list(self.editor.LevelEditor.dataManager.settings.backgrounds)
        self.btn.options = opts
        if self.btn.selected not in opts and opts:
            self.btn.selected = opts[0]
            self.properties["set_background_name"] = opts[0]

    def draw(self, surf, selected=False):
        self.updateDropDownField()

        pin = next(p for p in self.inputs if p.name == "set_background_name").connection
        super().draw(surf, selected, draw_ui=False, draw_label=pin)


        pin_dur = next(p for p in self.inputs if p.name == "duration")
        if not pin_dur.connection:
            self.duration_field.update_position(self.x, self.y)
            self.duration_field.draw(surf)

        if not pin:
            for el in [self.btn]:
                el.update_position(self.x, self.y)
                el.draw(surf)

    def execute(self, context):
        dm = self.editor.LevelEditor.dataManager

        for pin in self.inputs:
            if pin.pin_type == "data" and pin.connection:
                upstream = pin.connection.node
                upstream.execute(context)
                self.properties[pin.name] = upstream.properties[pin.connection.name]

        name = self.properties["set_background_name"]
        duration = float(self.properties.get("duration", 1.0))
        settings = dm.settings

        if name in settings.backgrounds:
            settings.parallax_index = settings.backgrounds.index(name)
            level = self.editor.LevelEditor.game_engine.level
            new_bg = dm.get_background_by_name(name)
            level.start_background_transition(new_bg, duration=duration)

        out = next(p for p in self.outputs if p.pin_type == "exec")
        return out.connection.node if out.connection else None



@register_node("Hide Light", category="World")
class HideLightNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Hide Light", editor, properties)
        self.editor = editor

        lights = self.editor.LevelEditor.dataManager.lights
        if not lights:
            self.valid = False
            self.editor.LevelEditor.nm.notify(
                'warning',
                'Hide Light',
                "Aucune light définie : node désactivée",
                1.5
            )
            return

        # Sinon on est valide
        self.valid = True
        names = [getattr(l, 'name', f"Light{idx}") for idx, l in enumerate(lights)]
        self.btn = DropdownButton(
            self,
            pygame.Rect(0, 40, 140, 24),
            names,
            callback=self._on_select
        )
        if self.properties.get('choice') in names:
            self.btn.selected = self.properties['choice']
        else:
            self.properties['choice'] = names[0]
            self.btn.selected = names[0]

        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        if not getattr(self, 'valid', False):
            return
        self.properties['choice'] = opt

    def updateDropDownField(self):
        if not getattr(self, 'valid', False):
            return
        lights = self.editor.LevelEditor.dataManager.lights
        names = [getattr(l, 'name', f"Light{idx}") for idx, l in enumerate(lights)]
        self.btn.options = names
        if names and self.btn.selected not in names:
            self.btn.selected = names[0]
            self.properties['choice'] = names[0]

    def draw(self, surf, selected=False):
        ox, oy = self.editor.offset
        if not getattr(self, 'valid', False):
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)

            font_t = FontManager().get(size=18)
            surf.blit(font_t.render("Hide Light [Error]", True, (255, 200, 200)), (x + 6, y + 4))

            lines = [
                "Aucune light définie",
                "Veuillez en ajouter une au",
                "niveau !",
                "(supprimez cette node)"
            ]
            font_m = FontManager().get(size=15)
            base_x = x + 6
            base_y = y + self.HEADER_HEIGHT + 10
            line_h = 14
            for i, line in enumerate(lines):
                surf.blit(font_m.render(line, True, (255,180,180)), (base_x, base_y + i*line_h))
            return

        # cas normal
        self.updateDropDownField()
        super().draw(surf, selected,False)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        if not getattr(self, 'valid', False):
            return None

        # récupère d'éventuels inputs data
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter = src.node
                getter.execute(context)
                self.properties[pin.name] = getter.properties[src.name]

        # cache la light sélectionnée
        choice = self.properties.get('choice')
        for i, light in enumerate(self.editor.LevelEditor.dataManager.lights):
            name = getattr(light, 'name', f"Light{i}")
            if name == choice:
                light.visible = False
                break

        # applique au moteur
        lvl = self.editor.LevelEditor.game_engine.level
        lvl.lights = self.editor.LevelEditor.dataManager.lights.copy()
        lvl.init_lightning()

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


@register_node("Show Light", category="World")
class ShowLightNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Show Light", editor, properties)
        self.editor = editor

        lights = self.editor.LevelEditor.dataManager.lights
        if not lights:
            self.valid = False
            self.editor.LevelEditor.nm.notify(
                'warning',
                'Show Light',
                "Aucune light définie : node désactivée",
                1.5
            )
            return

        self.valid = True
        names = [getattr(l, 'name', f"Light{idx}") for idx, l in enumerate(lights)]
        self.btn = DropdownButton(
            self,
            pygame.Rect(0, 40, 140, 24),
            names,
            callback=self._on_select
        )

        if self.properties.get('choice') in names:
            self.btn.selected = self.properties['choice']
        else:
            self.properties['choice'] = names[0]
            self.btn.selected = names[0]

        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        if not getattr(self, 'valid', False):
            return
        self.properties['choice'] = opt

    def updateDropDownField(self):
        if not getattr(self, 'valid', False):
            return
        lights = self.editor.LevelEditor.dataManager.lights
        names = [getattr(l, 'name', f"Light{idx}") for idx, l in enumerate(lights)]
        self.btn.options = names
        if names and self.btn.selected not in names:
            self.btn.selected = names[0]
            self.properties['choice'] = names[0]

    def draw(self, surf, selected=False):
        ox, oy = self.editor.offset
        if not getattr(self, 'valid', False):
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)

            font_t = FontManager().get(size=18)
            surf.blit(font_t.render("Show Light [Error]", True, (255, 200, 200)), (x + 6, y + 4))

            lines = [
                "Aucune light définie",
                "Veuillez en ajouter une au",
                "niveau !",
                "(supprimez cette node)"
            ]
            font_m = FontManager().get(size=15)
            base_x = x + 6
            base_y = y + self.HEADER_HEIGHT + 10
            line_h = 14
            for i, line in enumerate(lines):
                surf.blit(font_m.render(line, True, (255,180,180)), (base_x, base_y + i * line_h))
            return

        self.updateDropDownField()
        super().draw(surf, selected,False)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        if not getattr(self, 'valid', False):
            return None
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter = src.node
                getter.execute(context)
                self.properties[pin.name] = getter.properties[src.name]

        choice = self.properties.get('choice')
        for i, light in enumerate(self.editor.LevelEditor.dataManager.lights):
            name = getattr(light, 'name', f"Light{i}")
            if name == choice:
                light.visible = True
                break
        lvl = self.editor.LevelEditor.game_engine.level
        lvl.lights = self.editor.LevelEditor.dataManager.lights.copy()
        lvl.init_lightning()

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

@register_node("Set Global Illumination", category="World")
class SetGlobalIllumination(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Global Illumination", editor, properties)

        self.add_data_pin("illum", False,
                          str(self._get_default_illum()),
                          "GI")

        illum = self.properties.get("illum", "0")
        self.value_field = InputField(
            rect=(0, 0, 60, 18),
            text=str(round(float(illum),2)),
            placeholder="0.0",
            on_change=lambda t: self._on_illum_change(t)
        )

        self.height = 80

    def _get_default_illum(self):
        dm = self.editor.LevelEditor.dataManager
        return getattr(dm.settings, "global_illum", 0.0)

    def _on_illum_change(self, txt):
        self.properties["illum"] = txt


    def _get_input_value(self, context):
        pin = next(p for p in self.inputs if p.name == "illum")
        if pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            return getter.properties[pin.connection.name]
        else:
            raw = self.properties.get("illum", "0")
            try:
                return float(raw)
            except ValueError:
                return raw

    def handle_event(self, e: pygame.event.Event):
        super().handle_event(e)
        pin = next(p for p in self.inputs if p.name == "illum")
        if not pin.connection:
            self.value_field.handle_event(e)

    def draw(self, surf, selected=False):
        super().draw(surf, selected, draw_ui=False)

        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy

        pin = next(p for p in self.inputs if p.name == "illum")
        if not pin.connection:
            px, py = pin.pos
            self.value_field.rect.topleft = (
                px + 8 - ox,
                py - self.value_field.rect.h//2 - oy
            )
            self.value_field.draw(surf)

    def execute(self, context):
        dm = self.editor.LevelEditor.dataManager

        pin = next(p for p in self.inputs if p.name == "illum")
        if pin.connection:
            upstream = pin.connection.node
            upstream.execute(context)
            self.properties["illum"] = upstream.properties[pin.connection.name]

        try:
            val = float(self.properties["illum"])
        except ValueError:
            val = 0.0
        dm.settings.global_illum = min(max(val,0),1)
        
        out = next(p for p in self.outputs if p.pin_type == "exec")
        return out.connection.node if out.connection else None

@register_node("Get Global Illumination", category="World")
class GetGlobalIllumination(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Global Illumination", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("GI", True, "", "GI")
        self.height = 60

    def execute(self, context):
        dm = self.editor.LevelEditor.dataManager
        self.properties["GI"] = round(dm.settings.global_illum,2)
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = str(self.properties["GI"])
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 10, self.y - oy + 34))
        


@register_node("Set Bubble Text", category="World")
class SetBubbleText(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Bubble Text", editor, properties)
        self.editor = editor

        rect_names = [cr.name for cr in editor.LevelEditor.dataManager.collisionRects]
        if not rect_names:
            self.valid = False
            editor.LevelEditor.nm.notify(
                "warning",
                "Set Bubble Text",
                "Aucun CollisionRect défini : node désactivée",
                1.5
            )
            self.height = 40
            return
        self.valid = True

        default_choice = properties.get("choice", rect_names[0])
        pin_choice = self.add_data_pin("choice", False, default_choice, "", offset_y=0)
        self.properties["choice"] = default_choice
        
        self.dropdown = DropdownButton(
            self,
            pygame.Rect(0, 0, 120, 20),
            rect_names,
            callback=self._on_select
        )
        self.dropdown.update_position = lambda nx, ny: setattr(
            self.dropdown, "rect",
            pygame.Rect(
                *pin_choice.pos, 120, 20
            ).move(10, -10)
        )
        self.dropdown.update_position(self.x, self.y)
        self.dropdown.pin_name="choice"
        self.dropdown.selected=self.properties['choice']
        
        default_text = properties.get("text", "Bubble…")
        pin_text = self.add_data_pin("text", False, default_text, "Text", offset_y=0)
        self.properties["text"] = default_text

        self.text_field = InputField(
            rect=(0,0,120,18),
            text=default_text,
            placeholder="Bubble…",
            on_change=lambda t: self._on_change("text", t)
        )
        self.text_field.update_position = lambda nx, ny: setattr(
            self.text_field, "rect",
            pygame.Rect(
                *pin_text.pos, 120, 18
            ).move(10, -9)
        )
        self.text_field.update_position(self.x, self.y)
        self.text_field.pin_name="text"

        default_size = str(properties.get("font_size", 14))
        pin_size = self.add_data_pin("font_size", False, default_size, "FontSize", offset_y=0)
        self.properties["font_size"] = int(default_size)

        self.size_field = InputField(
            rect=(0,0,40,18),
            text=default_size,
            placeholder="14",
            on_change=lambda t: self._on_change("font_size", t)
        )
        self.size_field.update_position = lambda nx, ny: setattr(
            self.size_field, "rect",
            pygame.Rect(
                *pin_size.pos, 70, 18
            ).move(10, -9)
        )
        self.size_field.update_position(self.x, self.y)
        self.size_field.pin_name="font_size"





        default_speed = str(properties.get("speed", 0.0))
        pin_speed = self.add_data_pin("speed", False, default_speed, "Speed", offset_y=0)
        self.properties["speed"] = float(default_speed)

        self.speed_field = InputField(
            rect=(0,0,70,18),
            text=default_speed,
            placeholder="spd",
            on_change=lambda t: self._on_change("speed", t)
        )
        self.speed_field.update_position = lambda nx, ny: setattr(
            self.speed_field, "rect",
            pygame.Rect(
                *pin_speed.pos, 70, 18
            ).move(10, -9)
        )
        self.speed_field.update_position(self.x, self.y)
        self.speed_field.pin_name="speed"

        default_dur = str(properties.get("duration", -1.0))
        pin_dur = self.add_data_pin("duration", False, default_dur, "Duration", offset_y=0)
        self.properties["duration"] = float(default_dur)

        self.duration_field = InputField(
            rect=(0,0,70,20),
            text=default_dur,
            placeholder="dur",
            on_change=lambda t: self._on_change("duration", t)
        )
        self.duration_field.update_position = lambda nx, ny: setattr(
            self.duration_field, "rect",
            pygame.Rect(
                *pin_dur.pos, 70, 20
            ).move(10, -9)
        )
        self.duration_field.update_position(self.x, self.y)
        self.duration_field.pin_name="duration"


        default_color = properties.get("text_color", (255,255,255))
        pin_color = self.add_data_pin("text_color", False, default_color, "Color", offset_y=0)
        self.properties["text_color"] = default_color

        self.color_button = ColorButton(
            rect=(0,0,40,18),
            initial_color=default_color,
            action=lambda c: self._on_change("text_color", c)
        )
        self.color_button.update_position = lambda nx, ny: setattr(
            self.color_button, "rect",
            pygame.Rect(
                *pin_color.pos, 40, 18
            ).move(10, -10)
        )
        self.color_button.update_position(self.x, self.y)
        self.color_button.pin_name="text_color"
        self.ui_elements = [
            self.text_field,
            self.size_field,
            self.speed_field,
            self.duration_field,
            self.dropdown,
            self.color_button
        ]

        self.height = max(24 + len(self.inputs)*25, 140)

    def _on_select(self, choice: str):
        self.properties["choice"] = choice

    def _on_change(self, key, value):
        if key in ("font_size",):
            try:    self.properties[key] = max(1, int(value))
            except: pass
        elif key in ("speed","duration"):
            try:    self.properties[key] = float(value)
            except: pass
        else:
            self.properties[key] = value


    def draw(self, surf, selected=False):
        super().draw(surf, selected, draw_ui=False)

        for widget in self.ui_elements:
            pin_name = widget.pin_name
            pin = next((p for p in self.inputs if p.name == pin_name), None)
            if pin is None or not pin.connection:
                widget.update_position(self.x, self.y)
                widget.draw(surf)


    def execute(self, context):
        if not self.valid:
            return None

        for pin in list(self.inputs):
            if pin.pin_type=="data" and pin.connection:
                upstream = pin.connection.node
                upstream.execute(context)
                self.properties[pin.name] = upstream.properties[pin.connection.name]

        level = self.editor.LevelEditor.game_engine.level
        for cr in level.collision_rects:
            if cr.name == self.properties["choice"]:
                cr.text        = str(self.properties["text"])
                cr.font_size   = int(self.properties["font_size"])
                cr.text_color  = tuple(self.properties["text_color"])
                cr.bubble_speed   = float(self.properties["speed"])
                cr.bubble_duration= float(self.properties["duration"])
                cr.bubble_start_time  = time.time()

                break
        out = next((p for p in self.outputs if p.pin_type=="exec"), None)
        return out.connection.node if out and out.connection else None
