import pygame
from editor.ui.Input import InputField
from editor.blueprint_editor.node import DropdownButton, Node, register_node



@register_node("Print Console", category="Debug")
class PrintString(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Print Console', editor, properties)
        self.height=90
        self.add_data_pin('value', False, "Hello World", '    String')
        string = InputField(rect=(0, 0, 120, 20), text=str(self.properties['value']), placeholder='Message...',
                           on_change=lambda t: self._on_change('value', t))
        self.ui_elements.append(string)
        string.update_position = lambda nx, ny: setattr(string, 'rect', pygame.Rect(nx - editor.offset[0] + 20,
                                                                                       ny - editor.offset[1] + 50,
                                                                                       120, 20))
        string.update_position(self.x, self.y)

    def _on_change(self, key, txt):
        if key == 'value':
            self.properties[key] = txt
        else:
            try:
                self.properties[key] = float(txt)
            except ValueError:
                pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter_node  = src.node
                getter_node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]

        print(self.properties['value'])

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected,draw_ui=False)
        pin = next(p for p in self.inputs if p.name=="value")
        if not pin.connection:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)

@register_node("Print Notify", category="Debug")
class PrintNotify(Node):
    TYPES = ["info", "warning", "error", "success", "update"]

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Print Notify", editor, properties)

        # --- Pins ---
        self.add_data_pin("type", False, "info", "")
        self.add_data_pin("title", False, "Title", "")
        self.add_data_pin("description", False, "Message…", "")
        self.add_data_pin("duration", False, 2.0, "")

        # --- UI Elements ---
        self.type_btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            self.TYPES,
            callback=self._on_type_select
        )
        
        if self.properties.get('type'):
            self.type_btn.selected=self.properties['type']
        else:
            self.properties['type']="info"
        self.title_field = InputField(
            rect=(20, 60, 120, 20),
            text=str(self.properties["title"]),
            placeholder="Title…",
            on_change=lambda t: self._on_change("title", t)
        )
        self.ui_elements.append(self.title_field)

        self.desc_field = InputField(
            rect=(20, 90, 120, 20),
            text=str(self.properties["description"]),
            placeholder="Description…",
            on_change=lambda t: self._on_change("description", t)
        )
        self.ui_elements.append(self.desc_field)

        self.dur_field = InputField(
            rect=(20, 150, 120, 20),
            text=str(self.properties["duration"]),
            placeholder="Durée",
            on_change=lambda t: self._on_change("duration", t)
        )
        self.ui_elements.append(self.dur_field)
        self.ui_elements.append(self.type_btn)

        self.height = 150

    def _on_type_select(self, choice: str):
        self.properties["type"] = choice

    def _on_change(self, key, txt):
        if key == "duration":
            try:
                self.properties[key] = float(txt)
            except ValueError:
                pass
        else:
            self.properties[key] = txt

    def execute(self, context):
        # évaluer upstream getters
        for pin in self.inputs:
            if pin.pin_type == "data" and pin.connection:
                getter = pin.connection.node
                getter.execute(context)
                self.properties[pin.name] = getter.properties[pin.connection.name]

        # appeler notify
        nm = self.editor.LevelEditor.nm
        nm.notify(
            str(self.properties["type"]),
            str(self.properties["title"]),
            str(self.properties["description"]),
            duration=float(self.properties["duration"])
        )

        # flot exec
        out = next((p for p in self.outputs if p.pin_type == "exec"), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected,draw_ui=False)
        # repositionne manuellement chaque UI element
        nx, ny = self.x - self.editor.offset[0], self.y - self.editor.offset[1]
        # Dropdown
        self.type_btn.update_position(self.x, self.y)
        # InputFields : on modifie direct le rect
        self.title_field.rect.topleft = (nx + 20, ny + 60)
        self.desc_field.rect.topleft  = (nx + 20, ny + 90)
        self.dur_field.rect.topleft   = (nx + 20, ny + 120)

        if not next(p for p in self.inputs if p.name=="type").connection:
            self.type_btn.draw(surf)
        if not next(p for p in self.inputs if p.name=="title").connection:
            self.title_field.draw(surf)
        if not next(p for p in self.inputs if p.name=="description").connection:
            self.desc_field.draw(surf)
        if not next(p for p in self.inputs if p.name=="duration").connection:
            self.dur_field.draw(surf)
        self.type_btn.draw(surf)