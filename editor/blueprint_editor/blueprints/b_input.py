import pygame

from editor.blueprint_editor.node import DropdownButton, Node, register_node
from editor.ui.Font import FontManager
from editor.ui.TextButton import Button


@register_node("Is Key Pressed", category="Input")
class IsKeyPressed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Is Key Pressed", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("pressed", True, False, "Pressed")
        self.waiting_for_key = False
        key_name = self.properties.get("key_name", "<none>")
        self.key_btn = Button(
            rect=(10, 50, 70, 20),
            text=key_name,
            action=self._start_key_capture,
            border_radius=3,
            size=17,
            bg_color=(41, 41, 41)
        )
        self.ui_elements.append(self.key_btn)
        self.height = 70

    def _start_key_capture(self):
        self.waiting_for_key = True
        self.key_btn.text = "Press a key..."

    def handle_event(self, e: pygame.event.Event):
        if self.waiting_for_key and e.type == pygame.KEYDOWN:
            key_code = e.key
            key_name = pygame.key.name(key_code)
            self.properties["key_code"] = key_code
            self.properties["key_name"] = key_name
            self.key_btn.text = key_name
            self.waiting_for_key = False
            return
        super().handle_event(e)

    def execute(self, context):
        code = self.properties.get("key_code")
        if code is None:
            self.properties["pressed"] = False
        else:
            keys = pygame.key.get_pressed()
            self.properties["pressed"] = bool(keys[code])
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        ox, oy = self.editor.offset
        btn_x = self.x - ox + 10
        btn_y = self.y - oy + 35
        self.key_btn.rect.topleft = (btn_x, btn_y)
        self.key_btn.draw(surf)
        self.execute({})
        font = FontManager().get(size=18)
        txt = font.render(str(self.properties["pressed"]), True, (220,220,220))
        surf.blit(txt, (self.x - ox + 98, self.y - oy + 50))

@register_node("Get Mouse Position", category="Input")
class GetMousePosition(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Get Mouse Position", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("x", True, 0, "X")
        self.add_data_pin("y", True, 0, "Y")
        self.height = 70

    def execute(self, context):
        mx, my = pygame.mouse.get_pos()
        self.properties["x"] = mx
        self.properties["y"] = my
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        x = self.x - ox + 10
        y = self.y - oy + 30
        txt = font.render(f"X: {self.properties['x']}  Y: {self.properties['y']}", True, (220,220,220))
        surf.blit(txt, (x, y))

@register_node("Is Mouse Button Pressed", category="Input")
class IsMouseButtonPressed(Node):
    BUTTON_NAMES = ["Left", "Middle", "Right"]
    BUTTON_MAP = {"Left": 0, "Middle": 1, "Right": 2}

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Is Mouse Button Pressed", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("pressed", True, False, "Pressed")
        opts = self.BUTTON_NAMES
        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 75, 24),
            opts,
            callback=self._on_select
        )
        choice = self.properties.get("button")
        if choice in opts:
            self.btn.selected = choice
        else:
            self.properties["button"] = opts[0]
            self.btn.selected = opts[0]

        self.ui_elements.append(self.btn)
        self.height = 80

    def _on_select(self, opt: str):
        self.properties["button"] = opt

    def execute(self, context):
        btns = pygame.mouse.get_pressed(3)
        sel = self.properties.get("button", self.BUTTON_NAMES[0])
        idx = self.BUTTON_MAP.get(sel, 0)
        self.properties["pressed"] = bool(btns[idx])
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected,False)

        ox, oy = self.editor.offset
        bx = self.x - ox + 10
        by = self.y - oy + 30
        self.btn.rect.topleft = (bx, by)
        self.btn.draw(surf)

        self.execute({})
        font = FontManager().get(size=18)
        txt = font.render(str(self.properties["pressed"]), True, (220, 220, 220))
        surf.blit(txt, (self.x - ox + 98, self.y - oy + 50))


@register_node("Set Input Active", category="Input")
class SetInputActive(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Input Active", editor, properties)
        self.editor = editor

        opts = ["True", "False"]
        default = str(properties.get("active", True))
        self.dropdown = DropdownButton(
            self,
            pygame.Rect(15, 30, 120, 20),
            opts,
            callback=self._on_select
        )
        self.properties["active"] = default == "True"
        self.dropdown.selected = default
        self.ui_elements.append(self.dropdown)

    def _on_select(self, choice: str):
        self.properties["active"] = (choice == "True")

    def draw(self, surf, selected=False):
        super().draw(surf, selected, draw_ui=False)
        for widget in self.ui_elements:
            widget.update_position(self.x, self.y)
            widget.draw(surf)

    def execute(self, context):
        is_active = self.properties.get("active", True)
        engine = self.editor.LevelEditor.game_engine
        engine.player.input_handler.disable = not is_active

        out = next((p for p in self.outputs if p.pin_type=="exec"), None)
        return out.connection.node if out and out.connection else None
