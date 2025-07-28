
import pygame
from editor.blueprint_editor.blueprints.b_logic import ForNode
from editor.ui.Font import FontManager
from editor.ui.Input import InputField
from editor.blueprint_editor.node import Node, Pin, register_node
from editor.ui.TextButton import Button


@register_node("Screen Shake", category="Camera")
class ScreenShakeNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Screen Shake", editor, properties)
        self.add_data_pin("intensity", False, "0", "Intensity")
        self.add_data_pin("duration",  False, "0", "Duration")

        self.int_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties["intensity"]),
            placeholder="Intensity",
            on_change=lambda t: self._on_change("intensity", t)
        )
        self.dur_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties["duration"]),
            placeholder="Duration",
            on_change=lambda t: self._on_change("duration", t)
        )
        self.ui_elements.extend([self.int_field, self.dur_field])

        self.outputs.clear()
        self.outputs.append(Pin(self, "out", "exec", True, "Exec"))

        self.height = 110

        self._update_field_positions()

    def _on_change(self, key, txt):
        try:
            self.properties[key] = float(txt)
        except ValueError:
            pass

    def _get_value(self, name, context):
        pin = next(p for p in self.inputs if p.name == name)
        if pin.connection:
            upstream = pin.connection.node
            upstream.execute(context)
            return float(upstream.properties[pin.connection.name])
        return float(self.properties.get(name, 0))

    def _update_field_positions(self):
        for field, name in [(self.int_field, "intensity"), (self.dur_field, "duration")]:
            pin = next(p for p in self.inputs if p.name == name)
            px, py = pin.pos
            field.rect.topleft = (
                px + 8,
                py - field.rect.h // 2
            )


    def execute(self, context):
        intensity = self._get_value("intensity", context)
        duration  = self._get_value("duration", context)

        cam = self.editor.LevelEditor.game_engine.camera
        cam.shake(int(duration), int(intensity))

        out = next(p for p in self.outputs if p.pin_type=="exec")
        return out.connection.node if out.connection else None



    def draw(self, surf, selected=False):
        self._update_field_positions()
        super().draw(surf, selected,draw_ui=False)

        for field, name in [(self.int_field, "intensity"), (self.dur_field, "duration")]:
            pin = next(p for p in self.inputs if p.name == name)
            if not pin.connection:
                field.draw(surf)


@register_node("Get Time", category="Utility")
class GetTimeNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Get Time", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("time", True, 0.0, "t")
        self.height = 60

    def execute(self, context):
        ms = pygame.time.get_ticks()
        t = ms / 1000.0
        self.properties["time"] = t
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        t = self.properties["time"]
        txt = font.render(f"{t:.2f}s", True, (220, 220, 220))
        ox, oy = self.editor.offset
        x = self.x - ox + (self.WIDTH - txt.get_width()) // 2
        y = self.y - oy + self.HEADER_HEIGHT + 10
        surf.blit(txt, (x, y))

@register_node("Delay", category="Utility")
class DelayNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Delay", editor, properties)
        self.add_data_pin("duration", False, "1.0", "Seconds")
        self.outputs.clear()
        self.outputs.append(Pin(self, "done", "exec", True, "Done"))

        self.field = InputField(
            rect=(0, 0, 80, 20),
            text=str(self.properties.get("duration", "1.0")),
            placeholder="Delay (s)",
            on_change=lambda t: self._on_change("duration", t)
        )
        self.ui_elements = [self.field]
        self.height = 80
        self.valid = True
        self._update_field_position()

    def _on_change(self, key, txt):
        self.properties[key] = txt

    def _update_field_position(self):
        pin = next(p for p in self.inputs if p.pin_type == "exec")
        px, py = pin.pos
        self.field.rect.topleft = (px + 10, py - self.field.rect.h // 2)

    def _check_validity(self):
        def upstream_has_loop(exec_in_pin: Pin) -> bool:
            if not exec_in_pin.connection:
                return False
            src_pin = exec_in_pin.connection
            src_node = src_pin.node
            if isinstance(src_node, ForNode) and src_pin.name == "loop":
                return True
            prev_in = next((p for p in src_node.inputs if p.pin_type == "exec"), None)
            if prev_in:
                return upstream_has_loop(prev_in)
            return False

        exec_in = next(p for p in self.inputs if p.pin_type == "exec")
        self.valid = not upstream_has_loop(exec_in)

    def _get_duration(self, context):
        pin = next(p for p in self.inputs if p.name == "duration")
        if pin.connection:
            upstream = pin.connection.node
            upstream.execute(context)
            return float(upstream.properties.get(pin.connection.name, 0.0))
        try:
            return float(self.properties.get("duration", 0.0))
        except ValueError:
            return 0.0

    def execute(self, context):
        self._check_validity()
        if not self.valid:
            done = next(p for p in self.outputs if p.name == "done")
            return done.connection.node if done.connection else None

        delay = self._get_duration(context)
        resume_at = pygame.time.get_ticks() + int(delay * 1000)
        self.editor.delayed_tasks.append({
            "node": self,
            "context": dict(context),
            "resume_at": resume_at
        })
        return None

    def draw(self, surf, selected=False):
        self._check_validity()
        self._update_field_position()
        if not self.valid:
            ox, oy = self.editor.offset
            x, y = self.x - ox, self.y - oy
            w, h = self.WIDTH, self.height
            pygame.draw.rect(surf, (80,20,20), (x, y, w, h), border_radius=4)
            pygame.draw.rect(surf, (200,50,50), (x, y, w, h), 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150,0,0), hdr, border_top_left_radius=4, border_top_right_radius=4)

            font = FontManager().get(size=18)
            surf.blit(font.render("Delay [Invalid]", True, (255,180,180)), (x+6, y+4))
            font2 = FontManager().get(size=14)
            surf.blit(font2.render("Ne pas placer Après un pin loop !", True, (255,180,180)), (x+6, y+32))
            return

        super().draw(surf, selected, draw_ui=False)
        pin = next(p for p in self.inputs if p.name == "duration")
        if not pin.connection:
            self.field.draw(surf)
