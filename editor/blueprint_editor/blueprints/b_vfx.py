import pygame
from editor.blueprint_editor.node import DropdownButton, Node, register_node
from editor.ui.Font import FontManager
from editor.ui.Input import InputField

@register_node("Set Emitter Active", category="VFX")
class SetEmitterActive(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Emitter Active", editor, properties)
        self.editor = editor
        
        emitters = self.editor.LevelEditor.dataManager.emitters
        if not emitters:
            self.valid = False
            self.editor.LevelEditor.nm.notify("warning", "Set Emitter Active", "Aucun émetteur VFX défini : node désactivée", 1.5)
            self.height = 70
            return
        self.valid = True

        default_choice = properties.get("choice", emitters[0].name)
        pin_choice = self.add_data_pin("choice", False, default_choice, "", offset_y=0)
        self.properties["choice"] = default_choice

        self.dropdown = DropdownButton(
            self,
            pygame.Rect(0, 0, 120, 20),
            [e.name for e in emitters],
            callback=self._on_select
        )
        self.dropdown.update_position = lambda nx, ny: setattr(
            self.dropdown, "rect",
            pygame.Rect(*pin_choice.pos, 120, 20).move(10, -10)
        )
        self.dropdown.update_position(self.x, self.y)
        self.dropdown.pin_name = "choice"
        self.dropdown.selected = self.properties["choice"]

        default_active = properties.get("active", True)
        if isinstance(default_active, str):
            default_active = default_active.lower() == "true"
        pin_active = self.add_data_pin("active", False, default_active, "Active", offset_y=0)
        self.properties["active"] = default_active

        self.active_dropdown = DropdownButton(
            self,
            pygame.Rect(0, 0, 60, 20),
            ["True", "False"],
            callback=self._on_active_select
        )
        self.active_dropdown.update_position = lambda nx, ny: setattr(
            self.active_dropdown, "rect",
            pygame.Rect(*pin_active.pos, 60, 20).move(10, -10)
        )
        self.active_dropdown.update_position(self.x, self.y)
        self.active_dropdown.pin_name = "active"
        self.active_dropdown.selected = "True" if self.properties["active"] else "False"

        self.ui_elements = [self.dropdown, self.active_dropdown]
        self.height = 95

    def _on_select(self, choice: str):
        self.properties["choice"] = choice

    def _on_active_select(self, choice: str):
        self.properties["active"] = (choice == "True")

    def updateDropDownField(self):
        if not getattr(self, "valid", False):
            return
        emitters = self.editor.LevelEditor.dataManager.emitters
        names = [e.name for e in emitters]
        self.dropdown.options = names
        if names and self.dropdown.selected not in names:
            self.dropdown.selected = names[0]
            self.properties["choice"] = names[0]

    def handle_event(self, e: pygame.event.Event):
        if not getattr(self, "valid", False):
            return
        # Dragging logic:
        mx, my = pygame.mouse.get_pos()
        ox, oy = self.editor.offset
        hdr = pygame.Rect(self.x - ox, self.y - oy, self.WIDTH, self.HEADER_HEIGHT)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and hdr.collidepoint(mx, my):
            self.dragging = True
            self.drag_offset = (mx - (self.x - ox), my - (self.y - oy))
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.x = mx - self.drag_offset[0] + ox
            self.y = my - self.drag_offset[1] + oy
            for el in self.ui_elements:
                if hasattr(el, 'update_position'):
                    el.update_position(self.x, self.y)

        # UI interaction logic:
        pin_choice = next((p for p in self.inputs if p.name == "choice"), None)
        if not pin_choice or not pin_choice.connection:
            self.dropdown.handle_event(e)

        pin_active = next((p for p in self.inputs if p.name == "active"), None)
        if not pin_active or not pin_active.connection:
            self.active_dropdown.handle_event(e)

    def draw(self, surf, selected=False):
        if not getattr(self, "valid", False):
            ox, oy = self.editor.offset
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)
            font_t = FontManager().get(size=18)
            surf.blit(font_t.render("VFX Active [Error]", True, (255, 200, 200)), (x + 6, y + 4))
            font_m = FontManager().get(size=14)
            surf.blit(font_m.render("Aucun émetteur VFX", True, (255, 180, 180)), (x + 6, y + self.HEADER_HEIGHT + 10))
            return
            
        self.updateDropDownField()
        
        # Dynamically set pin labels based on whether their UI elements are visible
        pin_choice = next((p for p in self.inputs if p.name == "choice"), None)
        if pin_choice:
            pin_choice.label = "" if not pin_choice.connection else "Choice"

        pin_active = next((p for p in self.inputs if p.name == "active"), None)
        if pin_active:
            pin_active.label = "" if not pin_active.connection else "Active"

        super().draw(surf, selected, draw_ui=False)
        for el in self.ui_elements:
            pin_name = getattr(el, "pin_name", "")
            pin = next((p for p in self.inputs if p.name == pin_name), None)
            if pin is None or not pin.connection:
                if isinstance(el, DropdownButton) and el.is_open:
                    continue
                el.update_position(self.x, self.y)
                el.draw(surf)

    def execute(self, context):
        if not getattr(self, "valid", False):
            return None

        for pin in list(self.inputs):
            if pin.pin_type == "data" and pin.connection:
                upstream = pin.connection.node
                upstream.execute(context)
                self.properties[pin.name] = upstream.properties[pin.connection.name]

        target_name = self.properties["choice"]
        is_active = self.properties["active"]
        if isinstance(is_active, str):
            is_active = (is_active == "True" or is_active.lower() == "true")
        else:
            is_active = bool(is_active)

        for emitter in self.editor.LevelEditor.dataManager.emitters:
            if emitter.name == target_name:
                emitter.active = is_active

        if self.editor.LevelEditor.game_engine and self.editor.LevelEditor.game_engine.running:
            for emitter in self.editor.LevelEditor.game_engine.level.vfx_emitters:
                if emitter.name == target_name:
                    emitter.active = is_active

        out = next((p for p in self.outputs if p.pin_type == "exec"), None)
        return out.connection.node if out and out.connection else None


@register_node("Set Emitter Rate", category="VFX")
class SetEmitterRate(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Emitter Rate", editor, properties)
        self.editor = editor
        
        emitters = self.editor.LevelEditor.dataManager.emitters
        if not emitters:
            self.valid = False
            self.editor.LevelEditor.nm.notify("warning", "Set Emitter Rate", "Aucun émetteur VFX défini : node désactivée", 1.5)
            self.height = 70
            return
        self.valid = True

        default_choice = properties.get("choice", emitters[0].name)
        pin_choice = self.add_data_pin("choice", False, default_choice, "", offset_y=0)
        self.properties["choice"] = default_choice

        self.dropdown = DropdownButton(
            self,
            pygame.Rect(0, 0, 120, 20),
            [e.name for e in emitters],
            callback=self._on_select
        )
        self.dropdown.update_position = lambda nx, ny: setattr(
            self.dropdown, "rect",
            pygame.Rect(*pin_choice.pos, 120, 20).move(10, -10)
        )
        self.dropdown.update_position(self.x, self.y)
        self.dropdown.pin_name = "choice"
        self.dropdown.selected = self.properties["choice"]

        default_rate = str(properties.get("rate", 5.0))
        pin_rate = self.add_data_pin("rate", False, float(default_rate), "Rate", offset_y=0)
        self.properties["rate"] = float(default_rate)

        self.rate_field = InputField(
            rect=(0,0,60,18),
            text=default_rate,
            placeholder="5.0",
            on_change=lambda t: self._on_change("rate", t)
        )
        self.rate_field.update_position = lambda nx, ny: setattr(
            self.rate_field, "rect",
            pygame.Rect(*pin_rate.pos, 60, 18).move(10, -9)
        )
        self.rate_field.update_position(self.x, self.y)
        self.rate_field.pin_name = "rate"

        self.ui_elements = [self.rate_field, self.dropdown]
        self.height = 100

    def _on_select(self, choice: str):
        self.properties["choice"] = choice

    def _on_change(self, key, value):
        try:
            self.properties[key] = float(value)
        except ValueError:
            pass

    def updateDropDownField(self):
        if not getattr(self, "valid", False):
            return
        emitters = self.editor.LevelEditor.dataManager.emitters
        names = [e.name for e in emitters]
        self.dropdown.options = names
        if names and self.dropdown.selected not in names:
            self.dropdown.selected = names[0]
            self.properties["choice"] = names[0]

    def handle_event(self, e: pygame.event.Event):
        if not getattr(self, "valid", False):
            return
        # Dragging logic:
        mx, my = pygame.mouse.get_pos()
        ox, oy = self.editor.offset
        hdr = pygame.Rect(self.x - ox, self.y - oy, self.WIDTH, self.HEADER_HEIGHT)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and hdr.collidepoint(mx, my):
            self.dragging = True
            self.drag_offset = (mx - (self.x - ox), my - (self.y - oy))
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.x = mx - self.drag_offset[0] + ox
            self.y = my - self.drag_offset[1] + oy
            for el in self.ui_elements:
                if hasattr(el, 'update_position'):
                    el.update_position(self.x, self.y)

        # UI interaction logic:
        pin_choice = next((p for p in self.inputs if p.name == "choice"), None)
        if not pin_choice or not pin_choice.connection:
            self.dropdown.handle_event(e)

        pin_rate = next((p for p in self.inputs if p.name == "rate"), None)
        if not pin_rate or not pin_rate.connection:
            self.rate_field.handle_event(e)

    def draw(self, surf, selected=False):
        if not getattr(self, "valid", False):
            ox, oy = self.editor.offset
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)
            font_t = FontManager().get(size=18)
            surf.blit(font_t.render("VFX Rate [Error]", True, (255, 200, 200)), (x + 6, y + 4))
            font_m = FontManager().get(size=14)
            surf.blit(font_m.render("Aucun émetteur VFX", True, (255, 180, 180)), (x + 6, y + self.HEADER_HEIGHT + 10))
            return
            
        self.updateDropDownField()
        
        # Dynamically set pin labels based on whether their UI elements are visible
        pin_choice = next((p for p in self.inputs if p.name == "choice"), None)
        if pin_choice:
            pin_choice.label = "" if not pin_choice.connection else "Choice"

        pin_rate = next((p for p in self.inputs if p.name == "rate"), None)
        if pin_rate:
            pin_rate.label = "" if not pin_rate.connection else "Rate"

        super().draw(surf, selected, draw_ui=False)
        for el in self.ui_elements:
            pin_name = getattr(el, "pin_name", "")
            pin = next((p for p in self.inputs if p.name == pin_name), None)
            if pin is None or not pin.connection:
                if isinstance(el, DropdownButton) and el.is_open:
                    continue
                el.update_position(self.x, self.y)
                el.draw(surf)

    def execute(self, context):
        if not getattr(self, "valid", False):
            return None

        for pin in list(self.inputs):
            if pin.pin_type == "data" and pin.connection:
                upstream = pin.connection.node
                upstream.execute(context)
                self.properties[pin.name] = upstream.properties[pin.connection.name]

        target_name = self.properties["choice"]
        try:
            rate_val = max(0.0, float(self.properties["rate"]))
        except (ValueError, TypeError):
            rate_val = 5.0

        for emitter in self.editor.LevelEditor.dataManager.emitters:
            if emitter.name == target_name:
                emitter.rate = rate_val

        if self.editor.LevelEditor.game_engine and self.editor.LevelEditor.game_engine.running:
            for emitter in self.editor.LevelEditor.game_engine.level.vfx_emitters:
                if emitter.name == target_name:
                    emitter.rate = rate_val

        out = next((p for p in self.outputs if p.pin_type == "exec"), None)
        return out.connection.node if out and out.connection else None


@register_node("Trigger Emitter Burst", category="VFX")
class TriggerEmitterBurst(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Trigger Emitter Burst", editor, properties)
        self.editor = editor
        
        emitters = self.editor.LevelEditor.dataManager.emitters
        if not emitters:
            self.valid = False
            self.editor.LevelEditor.nm.notify("warning", "Trigger Emitter Burst", "Aucun émetteur VFX défini : node désactivée", 1.5)
            self.height = 70
            return
        self.valid = True

        default_choice = properties.get("choice", emitters[0].name)
        pin_choice = self.add_data_pin("choice", False, default_choice, "", offset_y=0)
        self.properties["choice"] = default_choice

        self.dropdown = DropdownButton(
            self,
            pygame.Rect(0, 0, 120, 20),
            [e.name for e in emitters],
            callback=self._on_select
        )
        self.dropdown.update_position = lambda nx, ny: setattr(
            self.dropdown, "rect",
            pygame.Rect(*pin_choice.pos, 120, 20).move(10, -10)
        )
        self.dropdown.update_position(self.x, self.y)
        self.dropdown.pin_name = "choice"
        self.dropdown.selected = self.properties["choice"]

        self.ui_elements = [self.dropdown]
        self.height = 80

    def _on_select(self, choice: str):
        self.properties["choice"] = choice

    def updateDropDownField(self):
        if not getattr(self, "valid", False):
            return
        emitters = self.editor.LevelEditor.dataManager.emitters
        names = [e.name for e in emitters]
        self.dropdown.options = names
        if names and self.dropdown.selected not in names:
            self.dropdown.selected = names[0]
            self.properties["choice"] = names[0]

    def handle_event(self, e: pygame.event.Event):
        if not getattr(self, "valid", False):
            return
        mx, my = pygame.mouse.get_pos()
        ox, oy = self.editor.offset
        hdr = pygame.Rect(self.x - ox, self.y - oy, self.WIDTH, self.HEADER_HEIGHT)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and hdr.collidepoint(mx, my):
            self.dragging = True
            self.drag_offset = (mx - (self.x - ox), my - (self.y - oy))
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.x = mx - self.drag_offset[0] + ox
            self.y = my - self.drag_offset[1] + oy
            for el in self.ui_elements:
                if hasattr(el, 'update_position'):
                    el.update_position(self.x, self.y)

        pin_choice = next((p for p in self.inputs if p.name == "choice"), None)
        if not pin_choice or not pin_choice.connection:
            self.dropdown.handle_event(e)

    def draw(self, surf, selected=False):
        if not getattr(self, "valid", False):
            ox, oy = self.editor.offset
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)
            font_t = FontManager().get(size=18)
            surf.blit(font_t.render("VFX Burst [Error]", True, (255, 200, 200)), (x + 6, y + 4))
            font_m = FontManager().get(size=14)
            surf.blit(font_m.render("Aucun émetteur VFX", True, (255, 180, 180)), (x + 6, y + self.HEADER_HEIGHT + 10))
            return
            
        self.updateDropDownField()
        
        pin_choice = next((p for p in self.inputs if p.name == "choice"), None)
        if pin_choice:
            pin_choice.label = "" if not pin_choice.connection else "Choice"

        super().draw(surf, selected, draw_ui=False)
        for el in self.ui_elements:
            pin_name = getattr(el, "pin_name", "")
            pin = next((p for p in self.inputs if p.name == pin_name), None)
            if pin is None or not pin.connection:
                if isinstance(el, DropdownButton) and el.is_open:
                    continue
                el.update_position(self.x, self.y)
                el.draw(surf)

    def execute(self, context):
        if not getattr(self, "valid", False):
            return None

        for pin in list(self.inputs):
            if pin.pin_type == "data" and pin.connection:
                upstream = pin.connection.node
                upstream.execute(context)
                self.properties[pin.name] = upstream.properties[pin.connection.name]

        target_name = self.properties["choice"]

        for emitter in self.editor.LevelEditor.dataManager.emitters:
            if emitter.name == target_name:
                emitter.burst_timer = emitter.burst_interval

        if self.editor.LevelEditor.game_engine and self.editor.LevelEditor.game_engine.running:
            for emitter in self.editor.LevelEditor.game_engine.level.vfx_emitters:
                if emitter.name == target_name:
                    emitter.burst_timer = emitter.burst_interval

        out = next((p for p in self.outputs if p.pin_type == "exec"), None)
        return out.connection.node if out and out.connection else None
