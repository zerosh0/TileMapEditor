import pygame
from editor.ui.Font import FontManager
from editor.ui.Input import InputField
from editor.blueprint_editor.node import Node, register_node

@register_node("Add", category="Operators")
class AddNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Add", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("A", False, "0", "A")
        self.add_data_pin("B", False, "0", "B")
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
        self.ui_elements.extend([self.A_field, self.B_field])
        self.add_data_pin("result", True, "0", "A+B")
        self.height = 100

    def _on_change(self, key, txt):
        self.properties[key] = txt

    def _get_value(self, name, context):
        pin = next(p for p in self.inputs if p.name==name)
        if pin.connection:
            node = pin.connection.node
            node.execute(context)
            try:
                return float(node.properties[pin.connection.name])
            except:
                return 0.0
        try:
            return float(self.properties[name])
        except:
            return 0.0

    def execute(self, context):
        a = self._get_value("A", context)
        b = self._get_value("B", context)
        self.properties["result"] = a + b
        return None


    def draw(self, surf, selected=False):
        super().draw(surf, selected,draw_ui=False)
        self.execute({})
        for field, name in [(self.A_field, "A"), (self.B_field, "B")]:
            pin = next(p for p in self.inputs if p.name==name)
            px, py = pin.pos
            field.rect.topleft = (px + 8, py - field.rect.h//2)
            if not pin.connection:
                field.draw(surf)
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = f"{float(self.properties.get('result',0)):.2f}"
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 10, self.y - oy + self.height - 24))


@register_node("Subtract", category="Operators")
class SubtractNode(AddNode):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, editor, properties)
        self.title = "Subtract"
        out_pin = next(p for p in self.outputs if p.name=="result")
        out_pin.label = "A-B"

    def execute(self, context):
        a = self._get_value("A", context)
        b = self._get_value("B", context)
        self.properties["result"] = a - b
        return None


@register_node("Multiply", category="Operators")
class MultiplyNode(AddNode):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, editor, properties)
        self.title = "Multiply"
        out_pin = next(p for p in self.outputs if p.name=="result")
        out_pin.label = "AxB"

    def execute(self, context):
        a = self._get_value("A", context)
        b = self._get_value("B", context)
        self.properties["result"] = a * b
        return None


@register_node("Divide", category="Operators")
class DivideNode(AddNode):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, editor, properties)
        self.title = "Divide"
        out_pin = next(p for p in self.outputs if p.name=="result")
        out_pin.label = "A/B"

    def execute(self, context):
        a = self._get_value("A", context)
        b = self._get_value("B", context)
        self.properties["result"] = a / b if b != 0 else 0.0
        return None
