import random
import pygame
from editor.ui.Font import FontManager
from editor.ui.Input import InputField
from editor.blueprint_editor.node import DropdownButton, Node, Pin, register_node
from editor.ui.TextButton import Button



@register_node("If", category="Logic")
class IfNode(Node):
    OPERATORS = ["==", "!=", "<", ">", "<=", ">="]

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "If", editor, properties)

        # --- Exec pins ---
        self.outputs.clear()
        self.outputs.append(Pin(self, "true",  "exec", True, "True"))
        self.outputs.append(Pin(self, "false", "exec", True, "False"))

        # --- Data pins A et B ---
        self.add_data_pin("A", False, "0", "A")
        self.add_data_pin("B", False, "0", "B")

        # --- UI : opérateur ---
        self.op_btn = DropdownButton(
            self,
            pygame.Rect(0, 0, 60, 20),
            self.OPERATORS,
            callback=self._on_op_select
        )
        if self.properties.get('operator'):
            self.op_btn.selected=self.properties['operator']
        else:
            self.properties['operator']="=="
        # on garde **seulement** le bouton dans ui_elements
        self.ui_elements.append(self.op_btn)

        # --- UI fields pour A et B (***pas*** ajoutés dans ui_elements) ---
        self.A_field = InputField(
            rect=(0,0,50,18),
            text=str(self.properties["A"]),
            placeholder="A",
            on_change=lambda t: self._on_change("A", t)
        )
        self.B_field = InputField(
            rect=(0,0,50,18),
            text=str(self.properties["B"]),
            placeholder="B",
            on_change=lambda t: self._on_change("B", t)
        )

        # Ajuste la hauteur pour laisser de la place
        self.height = 120

    def _on_op_select(self, choice: str):
        self.properties["operator"] = choice

    def _on_change(self, key, txt):
        # met à jour la propriété littérale si pas de connexion
        self.properties[key] = txt

    def _get_value(self, pin_name: str, context):
        pin = next(p for p in self.inputs if p.name == pin_name)
        if pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            return getter.properties[pin.connection.name]
        else:
            raw = self.properties[pin_name]
            try:
                return float(raw)
            except ValueError:
                return str(raw)

    def handle_event(self, e: pygame.event.Event):

        super().handle_event(e)

        for field, pin_name in [
            (self.A_field, "A"),
            (self.B_field, "B"),
        ]:
            pin = next(p for p in self.inputs if p.name == pin_name)
            if not pin.connection:
                field.handle_event(e)

    def execute(self, context):
        a = self._get_value("A", context)
        b = self._get_value("B", context)

        if isinstance(a, bool) and isinstance(b, str):
            b = b.lower() == 'true'
        elif isinstance(b, bool) and isinstance(a, str):
            a = a.lower() == 'true'

        op = self.properties["operator"]

        # calcul du résultat
        if   op == "==" : res = (a == b)
        elif op == "!=" : res = (a != b)
        elif op == "<"  : res = (a < b)
        elif op == ">"  : res = (a > b)
        elif op == "<=" : res = (a <= b)
        elif op == ">=" : res = (a >= b)
        else            : res = False

        out = next(p for p in self.outputs if p.name == ("true" if res else "false"))
        return out.connection.node if out.connection else None

    def draw(self, surf, selected=False):
        operator=self.properties["operator"]
        self.title=f"If               A {operator} B"
        super().draw(surf, selected,draw_ui=False)

        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy


        MARGIN = 8
        for field, pin_name in [
            (self.A_field, "A"),
            (self.B_field, "B"),
        ]:
            pin = next(p for p in self.inputs if p.name == pin_name)
            # on **ne dessine** que si le pin **n'est pas** connecté
            if pin.connection:
                continue
            px, py = pin.pos
            field.rect.topleft = (
                px + MARGIN,
                py - field.rect.h // 2
            )
            field.draw(surf)
        self.op_btn.update_position(self.x, self.y)
        self.op_btn.rect.topleft = (nx + Node.WIDTH//2 - 30, ny + 30)
        self.op_btn.draw(surf)

@register_node("Random", category="Logic")
class RandomNode(Node):
    SPACING_Y = 24

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Random", editor, properties)
        self.outputs.clear()
        self._next_idx = 0
        self.add_btn = Button(
            rect=(0, 0, 20, 20),
            text="+",
            action=self._add_exec_pin,
            border_radius=3
        )
        self.ui_elements.append(self.add_btn)

        self.height = 80


    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        ox, oy = self.editor.offset
        nx, ny = self.x-ox, self.y-oy
        self.add_btn.rect.topleft = (nx + self.WIDTH//2 - 10, ny + 40)
        self.add_btn.draw(surf)
        font = FontManager().get(size=20)
        for pin in self.outputs:
            px, py = pin.pos
            lbl = font.render(pin.label, True, (200,200,200))
            lbl_x = px - Pin.RADIUS - 4 - lbl.get_width()
            lbl_y = py - lbl.get_height()//2
            surf.blit(lbl, (lbl_x, lbl_y))

    def _add_exec_pin(self):
        name  = f"out{self._next_idx}"
        label = str(self._next_idx)
        pin = Pin(self, name, pin_type="exec", is_output=True, label=label)
        self.outputs.append(pin)
        self._next_idx += 1

        needed = 40 + len(self.outputs) * self.SPACING_Y
        if needed > self.height:
            self.height = needed

    def get_pin_pos(self, pin: Pin):
        if pin.pin_type == "exec" and pin.is_output and pin in self.outputs:
            ox, oy = self.editor.offset
            x = self.x - ox + self.WIDTH
            idx = self.outputs.index(pin)
            y = self.y - oy + self.HEADER_HEIGHT + 16 + idx * self.SPACING_Y
            return int(x), int(y)
        return super().get_pin_pos(pin)

    def execute(self, context):
        if not self.outputs:
            return None
        choice = random.choice(self.outputs)
        return choice.connection.node if choice.connection else None

    def handle_event(self, e: pygame.event.Event):
        super().handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = pygame.mouse.get_pos()
            for pin in self.outputs:
                px, py = pin.pos
                if (mx - px)**2 + (my - py)**2 <= Pin.RADIUS**2:
                    if pin.connection:
                        pin.disconnect()
                        self.editor.connections = [
                            (o,i) for (o,i) in self.editor.connections
                            if o is not pin
                        ]
                    else:
                        self.editor.start_connection(pin)
                    return






@register_node("For", category="Logic")
class ForNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "For", editor, properties)
        self.outputs.clear()
        self.outputs.append(Pin(self, "loop", "exec", True,  "Loop"))
        self.outputs.append(Pin(self, "next", "exec", True,  "Next"))

        self.add_data_pin("count", False, "0", "")
        self.count_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties["count"]),
            placeholder="Count",
            on_change=lambda t: self._on_count_change(t)
        )
        self.ui_elements.append(self.count_field)
        self.add_data_pin("index", True,  "0", "i")
        self.height = 100

    def _on_count_change(self, txt):
        try: self.properties["count"] = int(txt)
        except: pass

    def _get_count(self, context):
        pin = next(p for p in self.inputs if p.name=="count")
        if pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            return int(getter.properties[pin.connection.name])
        try:
            return int(self.properties["count"])
        except:
            return 0


    def execute(self, context):
        out = next(p for p in self.outputs if p.name=="next")
        return out.connection.node if out.connection else None


    def draw(self, surf, selected=False):
        super().draw(surf, selected,draw_ui=False)
        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy

        pin = next(p for p in self.inputs if p.name=="count")
        if not pin.connection:
            self.count_field.rect.topleft = (nx + 10, ny + 30)
            self.count_field.draw(surf)

        font = FontManager().get(size=18)
        idx = self.properties.get("index", 0)
        surf.blit(font.render(f"i = {idx}", True, (220,220,220)),
                  (nx + 10, ny + 60))

@register_node("Sequence", category="Logic")
class SequenceNode(Node):
    SPACING_Y = 24

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Sequence", editor, properties)
        self.outputs.clear()
        self._next_idx = 0
        self.add_btn = Button(
            rect=(0,0,20,20),
            text="+",
            action=self._add_exec_pin,
            border_radius=3
        )
        self.ui_elements.append(self.add_btn)
        self.height = 80

    def _add_exec_pin(self):
        name  = f"out{self._next_idx}"
        label = str(self._next_idx)
        pin = Pin(self, name, pin_type="exec", is_output=True, label=label)
        self.outputs.append(pin)
        self._next_idx += 1
        needed = 40 + len(self.outputs) * self.SPACING_Y
        if needed > self.height:
            self.height = needed

    def get_pin_pos(self, pin: Pin):
        if pin.pin_type=="exec" and pin.is_output and pin in self.outputs:
            ox, oy = self.editor.offset
            x = self.x - ox + self.WIDTH
            idx = self.outputs.index(pin)
            y = self.y - oy + self.HEADER_HEIGHT + 16 + idx*self.SPACING_Y
            return int(x), int(y)
        return super().get_pin_pos(pin)

    def execute(self, context):
        for pin in self.outputs:
            if pin.connection:
                start = pin.connection.node
                self.editor.run_logic_from_event(start)
        return None

    def handle_event(self, e):
        super().handle_event(e)
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            mx, my = pygame.mouse.get_pos()
            for pin in self.outputs:
                px, py = pin.pos
                if (mx-px)**2 + (my-py)**2 <= Pin.RADIUS**2:
                    if pin.connection:
                        pin.disconnect()
                        self.editor.connections = [
                            (o,i) for (o,i) in self.editor.connections
                            if o is not pin
                        ]
                    else:
                        self.editor.start_connection(pin)
                    return

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        ox, oy = self.editor.offset
        nx, ny = self.x-ox, self.y-oy
        self.add_btn.rect.topleft = (nx + self.WIDTH//2 - 10, ny + 40)
        self.add_btn.draw(surf)
        font = FontManager().get(size=20)
        for pin in self.outputs:
            px, py = pin.pos
            lbl = font.render(pin.label, True, (200,200,200))
            lbl_x = px - Pin.RADIUS - 4 - lbl.get_width()
            lbl_y = py - lbl.get_height()//2
            surf.blit(lbl, (lbl_x, lbl_y))


@register_node("FlipFlop", category="Logic")
class FlipFlopNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "FlipFlop", editor, properties)
        self.outputs.clear()
        self.outputs.append(Pin(self, "A", "exec", True, "A"))
        self.outputs.append(Pin(self, "B", "exec", True, "B"))
        self.properties.setdefault("state", 0)
        self.properties.setdefault("last", "A")
        self.height = 80

    def execute(self, context):
        current = int(self.properties["state"])
        out_state = "A" if current == 0 else "B"
        self.properties["last"] = out_state
        self.properties["state"] = 1 - current
        pin = next(p for p in self.outputs if p.name == out_state)
        return pin.connection.node if pin.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy
        font = FontManager().get(size=18)
        txt = f"Last: {self.properties.get('last', 'A')}"
        surf.blit(font.render(txt, True, (220,220,220)), (nx + 10, ny + 30))


@register_node("Once", category="Logic")
class OnceNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Once", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.inputs.append(Pin(self, "in", "exec", False, "In"))
        self.outputs.append(Pin(self, "out", "exec", True, "Out"))

        triggered = self.properties.get("triggered", False)
        self.properties["triggered"] = bool(triggered)
        self.height = 70

    def execute(self, context):
        if not self.properties.get("triggered", False):
            self.properties["triggered"] = True
            out = next(p for p in self.outputs if p.name == "out")
            return out.connection.node if out and out.connection else None
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        font = FontManager().get(size=18)
        status = "Done" if self.properties["triggered"] else "Ready"
        txt_surf = font.render(status, True, (220, 220, 220))

        ox, oy = self.editor.offset
        x = self.x - ox + (self.WIDTH - txt_surf.get_width()) // 2
        y = self.y - oy + self.HEADER_HEIGHT + 10
        surf.blit(txt_surf, (x, y))


@register_node("Set Variable", category="Logic")
class SetVariableNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Variable", editor, properties)

        self.add_data_pin("value", False, "0", "Value")
        self.inputs[-1].offset_y=10
        var_name = self.properties.get("var_name", "")
        self.name_field = InputField(
            rect=(0, 0, 70, 18),
            text=var_name,
            placeholder="var name",
            on_change=lambda t: self._on_name_change(t)
        )
        self.ui_elements.append(self.name_field)

        val = self.properties.get("value", "0")
        self.value_field = InputField(
            rect=(0, 0, 70, 18),
            text=str(val),
            placeholder="Value",
            on_change=lambda t: self._on_value_change(t)
        )

        self.height = 100

    def _on_name_change(self, txt):
        self.properties["var_name"] = txt

    def _on_value_change(self, txt):
        self.properties["value"] = txt

    def _get_input_value(self, context):
        pin = next(p for p in self.inputs if p.name == "value")
        if pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            return getter.properties[pin.connection.name]
        else:
            raw = self.properties["value"]
            try:
                return float(raw)
            except ValueError:
                return raw

    def handle_event(self, e: pygame.event.Event):
        super().handle_event(e)
        pin = next(p for p in self.inputs if p.name == "value")
        if not pin.connection:
            self.value_field.handle_event(e)

    def execute(self, context):
        name = self.properties.get("var_name", "")
        if name:
            self.editor.variable_store[name] = self._get_input_value(context)
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


    def draw(self, surf, selected=False):
        self.title = "Set Var"
        super().draw(surf, selected, draw_ui=False)
        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy

        self.name_field.rect.topleft = (nx + 10, ny + 30)
        self.name_field.draw(surf)
        pin = next(p for p in self.inputs if p.name == "value")
        if not pin.connection:
            px, py = pin.pos
            # positionner à droite du pin
            self.value_field.rect.topleft = (px + 8, py - self.value_field.rect.h // 2)
            self.value_field.draw(surf)



@register_node("Get Variable", category="Logic")
class GetVariableNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Get Variable", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("value", True, "0", "Value")
        var_name = self.properties.get("var_name", "")
        self.name_field = InputField(
            rect=(0, 0, 70, 18),
            text=var_name,
            placeholder="var name",
            on_change=lambda t: self._on_name_change(t)
        )
        self.ui_elements.append(self.name_field)

        self.height = 60

    def _on_name_change(self, txt):
        self.properties["var_name"] = txt

    def execute(self, context):
        name = self.properties.get("var_name", "")
        val = self.editor.variable_store.get(name, None)
        self.properties["value"] = val
        return  None



    def draw(self, surf, selected=False):
        self.title = f"Get Var"
        super().draw(surf, selected, draw_ui=False)

        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy
        self.name_field.rect.topleft = (nx + 10, ny + 30)
        self.name_field.draw(surf)
