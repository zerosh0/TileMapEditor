import pygame
from editor.ui.Font import FontManager
from editor.ui.Input import InputField
from editor.blueprint_editor.node import DropdownButton, Node, register_node


@register_node("Play Animation", category="Animation")
class PlayAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Play Animation', editor, properties)
        self.editor=editor
        self.btn = DropdownButton(self, pygame.Rect(10, 30, 120, 24),
                             list(self.editor.LevelEditor.animations.animations.keys()), callback=self._on_select)
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        self.properties['choice'] = opt

    def updateDropDownField(self):
        self.btn.options=list(self.editor.LevelEditor.animations.animations.keys())
        if not self.btn.selected in self.btn.options and self.btn.options:
            self.btn.selected=self.btn.options[0]

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter_node  = src.node
                getter_node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]
        anim=self.editor.LevelEditor.animations.animations[self.btn.selected]
        anim.timeline.current=0.0
        anim.play(anim.timeline.loop)

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

@register_node("Get Animation Speed", category="Animation")
class GetAnimationSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Get Animation Speed", editor, properties)
        # on enlève les pins hérités
        self.inputs.clear()
        self.outputs.clear()
        # on expose une data-pin 'speed'
        self.add_data_pin("speed", True, "0", "")

        # dropdown pour choisir l'animation
        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            list(self.editor.LevelEditor.animations.animations.keys()),
            callback=self._on_select
        )
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        self.ui_elements.append(self.btn)
        

    def _on_select(self, opt: str):
        self.properties["choice"] = opt

    def updateDropDownField(self):
        opts = list(self.editor.LevelEditor.animations.animations.keys())
        self.btn.options = opts
        if self.btn.selected not in opts and opts:
            self.btn.selected = opts[0]
            self.properties["choice"] = opts[0]

    def execute(self, context):
        anims = self.editor.LevelEditor.animations.animations
        choice = self.properties.get("choice", "")
        if choice in anims:
            s = anims[choice].speed
        else:
            s = 0.0
        self.properties["speed"] = round(s, 2)
        return None

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        self.execute({})  # mise à jour en temps réel
        super().draw(surf, selected)

        # affichage de la valeur
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = f"{float(self.properties['speed']):.2f}"
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 10, self.y - oy + 65))

        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

@register_node("Set Animation Speed", category="Animation")
class SetAnimationSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Animation Speed", editor, properties)
        # data-in speed
        self.add_data_pin("speed", False, "0", "speed",offset_y=20)
        # dropdown pour choisir l'anim
        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            list(self.editor.LevelEditor.animations.animations.keys()),
            callback=self._on_select
        )
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties['choice']=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)
        
        self.height = 110

        # champ inline pour speed si non branché
        self.speed_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties["speed"]),
            placeholder="Speed",
            on_change=lambda t: self._on_speed_change(t)
        )


    def _on_select(self, opt: str):
        self.properties["choice"] = opt

    def _on_speed_change(self, txt: str):
        try:
            self.properties["speed"] = float(txt)
        except ValueError:
            pass

    def updateDropDownField(self):
        opts = list(self.editor.LevelEditor.animations.animations.keys())
        self.btn.options = opts
        if self.btn.selected not in opts and opts:
            self.btn.selected = opts[0]
            self.properties["choice"] = opts[0]

    def _get_speed(self, context):
        pin = next(p for p in self.inputs if p.name=="speed")
        if pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            return float(getter.properties[pin.connection.name])
        return float(self.properties.get("speed", 0.0))

    def execute(self, context):
        choice = self.properties.get("choice", "")
        s = self._get_speed(context)
        anims = self.editor.LevelEditor.animations.animations
        if choice in anims:
            anims[choice].speed = s

        out = next(p for p in self.outputs if p.pin_type=="exec")
        return out.connection.node if out.connection else None

    def handle_event(self, e):
        super().handle_event(e)
        # ne gérer le champ inline que si non branché
        pin = next(p for p in self.inputs if p.name=="speed")
        if not pin.connection:
            self.speed_field.handle_event(e)

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected)

        # champ inline à droite du pin 'speed'
        pin = next(p for p in self.inputs if p.name=="speed")
        if not pin.connection:
            px, py = pin.pos
            self.speed_field.rect.topleft = (px + 8, py - self.speed_field.rect.h//2)
            self.speed_field.draw(surf)

        # dropdown
        for el in self.ui_elements:
            if isinstance(el, DropdownButton):
                el.update_position(self.x, self.y)
                el.draw(surf)

@register_node("Get Animation Time", category="Animation")
class GetAnimationTime(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Get Animation Time", editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin("time", True, "0", "")

        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            list(self.editor.LevelEditor.animations.animations.keys()),
            callback=self._on_select
        )
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties["choice"]=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        self.properties["choice"] = opt

    def updateDropDownField(self):
        opts = list(self.editor.LevelEditor.animations.animations.keys())
        self.btn.options = opts
        if self.btn.selected not in opts and opts:
            self.btn.selected = opts[0]
            self.properties["choice"] = opts[0]

    def execute(self, context):
        anims = self.editor.LevelEditor.animations.animations
        choice = self.properties.get("choice", "")
        if choice in anims:
            t = round(anims[choice].timeline.current,2)
        else:
            t = 0.0
        self.properties["time"] = t
        return None

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        self.execute({})
        super().draw(surf, selected,draw_ui=False)

        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = f"{float(self.properties['time'])}"
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 10, self.y - oy + 65))
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

@register_node("Set Animation Time", category="Animation")
class SetAnimationTime(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Animation Time", editor, properties)
        self.add_data_pin("time", False, "0", "Time",offset_y=20)
        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            list(self.editor.LevelEditor.animations.animations.keys()),
            callback=self._on_select
        )
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties['choice']=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)
        
        self.height = 110
        self.time_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties["time"]),
            placeholder="Time",
            on_change=lambda t: self._on_time_change(t)
        )
        self.ui_elements.append(self.time_field)

    def _on_select(self, opt: str):
        self.properties["choice"] = opt

    def _on_time_change(self, txt: str):
        try:
            self.properties["time"] = float(txt)
        except ValueError:
            pass

    def updateDropDownField(self):
        opts = list(self.editor.LevelEditor.animations.animations.keys())
        self.btn.options = opts
        if self.btn.selected not in opts and opts:
            self.btn.selected = opts[0]
            self.properties["choice"] = opts[0]

    def _get_time(self, context):
        pin = next(p for p in self.inputs if p.name=="time")
        if pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            return float(getter.properties[pin.connection.name])
        return float(self.properties.get("time", 0.0))

    def execute(self, context):
        choice = self.properties.get("choice", "")
        t = self._get_time(context)
        anims = self.editor.LevelEditor.animations.animations
        if choice in anims:
            anim = anims[choice]
            anim.timeline.current = t

        out = next(p for p in self.outputs if p.pin_type=="exec")
        return out.connection.node if out.connection else None


    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected,draw_ui=False)

        # champ time
        pin = next(p for p in self.inputs if p.name=="time")
        ox, oy = self.editor.offset
        nx, ny = self.x - ox, self.y - oy
        if not pin.connection:
            # positionné à droite du pin 'time'
            px, py = pin.pos
            self.time_field.rect.topleft = (px + 8, py - self.time_field.rect.h//2)
            self.time_field.draw(surf)

        # dropdown
        for el in self.ui_elements:
            if isinstance(el, DropdownButton):
                el.update_position(self.x, self.y)
                el.draw(surf)

@register_node("Stop Animation", category="Animation")
class StopAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Stop Animation', editor, properties)
        self.editor=editor
        self.btn = DropdownButton(self, pygame.Rect(10, 30, 120, 24),
                             list(self.editor.LevelEditor.animations.animations.keys()), callback=self._on_select)
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties['choice']=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        self.properties['choice'] = opt

    def updateDropDownField(self):
        self.btn.options=list(self.editor.LevelEditor.animations.animations.keys())
        if not self.btn.selected in self.btn.options and self.btn.options:
            self.btn.selected=self.btn.options[0]

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected,draw_ui=False)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter_node  = src.node
                getter_node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]
        anim=self.editor.LevelEditor.animations.animations[self.btn.selected]
        anim.stop()

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


@register_node("Pause Animation", category="Animation")
class PauseAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Pause Animation', editor, properties)
        self.editor=editor
        self.btn = DropdownButton(self, pygame.Rect(10, 30, 120, 24),
                             list(self.editor.LevelEditor.animations.animations.keys()), callback=self._on_select)
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties['choice']=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        self.properties['choice'] = opt

    def updateDropDownField(self):
        self.btn.options=list(self.editor.LevelEditor.animations.animations.keys())
        if not self.btn.selected in self.btn.options and self.btn.options:
            self.btn.selected=self.btn.options[0]

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected,draw_ui=False)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter_node  = src.node
                getter_node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]
        anim=self.editor.LevelEditor.animations.animations[self.btn.selected]
        anim.pause()

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


@register_node("Loop Animation", category="Animation")
class LoopAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Loop Animation', editor, properties)
        self.editor=editor
        self.btn = DropdownButton(self, pygame.Rect(10, 30, 120, 24),
                             list(self.editor.LevelEditor.animations.animations.keys()), callback=self._on_select)
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties['choice']=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        self.properties['choice'] = opt

    def updateDropDownField(self):
        self.btn.options=list(self.editor.LevelEditor.animations.animations.keys())
        if not self.btn.selected in self.btn.options and self.btn.options:
            self.btn.selected=self.btn.options[0]

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected,draw_ui=False)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter_node  = src.node
                getter_node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]
        anim=self.editor.LevelEditor.animations.animations[self.btn.selected]
        anim.timeline.loop=True

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None
    


@register_node("Unloop Animation", category="Animation")
class UnLoopAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Unloop Animation', editor, properties)
        self.editor=editor
        self.btn = DropdownButton(self, pygame.Rect(10, 30, 120, 24),
                             list(self.editor.LevelEditor.animations.animations.keys()), callback=self._on_select)
        if self.properties.get('choice'):
            self.btn.selected=self.properties['choice']
        else:
            self.properties['choice']=list(self.editor.LevelEditor.animations.animations.keys())[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        self.properties['choice'] = opt

    def updateDropDownField(self):
        self.btn.options=list(self.editor.LevelEditor.animations.animations.keys())
        if not self.btn.selected in self.btn.options and self.btn.options:
            self.btn.selected=self.btn.options[0]

    def draw(self, surf, selected=False):
        self.updateDropDownField()
        super().draw(surf, selected,draw_ui=False)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                getter_node  = src.node
                getter_node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]
        anim=self.editor.LevelEditor.animations.animations[self.btn.selected]
        anim.timeline.loop=False

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None