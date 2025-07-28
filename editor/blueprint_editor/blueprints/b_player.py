import pygame
from editor.ui.Font import FontManager
from editor.ui.Input import InputField
from editor.blueprint_editor.node import DropdownButton, Node, register_node


@register_node("Teleport", category="Player")
class TeleportPlayer(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Teleport', editor, properties)
        self.editor = editor

        # Récupère la liste des location points
        pts = list(self.editor.LevelEditor.dataManager.get_location_point_name())
        if not pts:
            # Alerte et passe en invalid state
            self.editor.LevelEditor.nm.notify(
                'warning',
                'TeleportPlayer',
                "Aucun locationPoint n'est posé : node désactivée",
                1.5
            )
            self.valid = False
            return
        # OK, on peut créer la dropdown
        self.valid = True
        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            pts,
            callback=self._on_select
        )
        # Valeur par défaut ou restaurée
        if 'choice' in self.properties and self.properties['choice'] in pts:
            self.btn.selected = self.properties['choice']
        else:
            self.properties['choice'] = pts[0]
            self.btn.selected = pts[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        if not self.valid:
            return
        self.properties['choice'] = opt

    def updateDropDownField(self):
        if not self.valid:
            return
        pts = list(self.editor.LevelEditor.dataManager.get_location_point_name())
        self.btn.options = pts
        # Si la sélection a disparu, on remet au premier élément
        if pts and self.btn.selected not in pts:
            self.btn.selected = pts[0]
            self.properties['choice'] = pts[0]

    def draw(self, surf, selected=False):
        ox, oy = self.editor.offset
        if not getattr(self, 'valid', False):
            # Dimensions et position
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)

            # Fond et bordure d'erreur
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)

            # Header
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)

            # Titre
            font_title = FontManager().get(size=18)
            title_surf = font_title.render("Teleport [Error]", True, (255, 200, 200))
            surf.blit(title_surf, (x + 6, y + 4))

            # Message dans le corps
            font_msg = FontManager().get(size=15)
            lines = [
                "Aucun point de localisation",
                "disponible !",
                "(Veuillez supprimer cette",
                "node)"
            ]
            font_msg = FontManager().get(size=15)
            base_x = x + 6
            base_y = y + self.HEADER_HEIGHT + 10
            line_height = 12

            for i, line in enumerate(lines):
                msg_surf = font_msg.render(line, True, (255, 180, 180))
                surf.blit(msg_surf, (base_x, base_y + i * line_height))
                                

            return

        self.updateDropDownField()
        super().draw(surf, selected)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)


    def execute(self, context):
        if not getattr(self, 'valid', False):
            return None
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                getter = pin.connection.node
                getter.execute(context)
                self.properties[pin.name] = getter.properties[pin.name]

        self.editor.LevelEditor.game_engine.player.update_location_by_name(
            self.btn.selected
        )
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


@register_node("Damage", category="Player")
class DamagePlayer(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Damage Player', editor)
        self.add_data_pin('amount', False, "10", 'amount')
        amount = InputField(rect=(0, 0, 120, 20), text=str(self.properties['amount']), placeholder='Amount of Damage...',
                           on_change=lambda t: self._on_change('amount', t))
        self.ui_elements.append(amount)
        amount.update_position = lambda nx, ny: setattr(amount, 'rect', pygame.Rect(nx - editor.offset[0] + 20,
                                                                                       ny - editor.offset[1] + 50,
                                                                                       120, 20))
        amount.update_position(self.x, self.y)


    def _on_change(self, key, txt):
        if key == 'amount':
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

        self.editor.LevelEditor.game_engine.player.health_system.take_damage(float(self.properties['amount']))
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        pin=next(p for p in self.inputs if p.name == "amount").connection
        super().draw(surf, selected,draw_ui=False,draw_label=pin)
        if not pin:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)
    


@register_node("Heal", category="Player")
class HealPlayer(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Heal Player', editor, properties)
        self.add_data_pin('amount', False, "10", 'amount')
        amount = InputField(rect=(0, 0, 120, 20), text=str(self.properties['amount']), placeholder='Amount of Heal...',
                           on_change=lambda t: self._on_change('amount', t))
        self.ui_elements.append(amount)
        amount.update_position = lambda nx, ny: setattr(amount, 'rect', pygame.Rect(nx - editor.offset[0] + 20,
                                                                                       ny - editor.offset[1] + 50,
                                                                                       120, 20))
        amount.update_position(self.x, self.y)


    def _on_change(self, key, txt):
        if key == 'amount':
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

        self.editor.LevelEditor.game_engine.player.health_system.heal_with_amount(float(self.properties['amount']))
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        pin=next(p for p in self.inputs if p.name == "amount").connection
        super().draw(surf, selected,draw_ui=False,draw_label=pin)
        if not pin:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)
    

@register_node("Set MaxHealth", category="Player")
class SetMaxHealth(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set MaxHealth', editor, properties)
        self.add_data_pin('health', False, str(self.editor.LevelEditor.game_engine.player.health_system.max_health), 'Max Health')
        amount = InputField(rect=(0, 0, 120, 20), text=str(self.properties['health']), placeholder='Max Health Value',
                           on_change=lambda t: self._on_change('health', t))
        self.ui_elements.append(amount)
        amount.update_position = lambda nx, ny: setattr(amount, 'rect', pygame.Rect(nx - editor.offset[0] + 20,
                                                                                       ny - editor.offset[1] + 50,
                                                                                       120, 20))
        amount.update_position(self.x, self.y)


    def _on_change(self, key, txt):
        if key == 'health':
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

        self.editor.LevelEditor.game_engine.player.health_system.max_health=float(self.properties['health'])
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        pin=next(p for p in self.inputs if p.name == "health").connection
        super().draw(surf, selected,draw_ui=False,draw_label=pin)
        if not pin:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)

@register_node("Get Player Health", category="Player")
class GetPlayerHealth(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player Health', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('health', True, '0', 'Current Health')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.health_system.health
        self.properties['health'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['health']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))

@register_node("Get Player MaxHealth", category="Player")
class GetPlayerMaxHealth(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player MaxHealth', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('max_health', True, '0', 'Max Health')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.health_system.max_health
        self.properties['max_health'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['max_health']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))


@register_node("Get Player Velocity", category="Player")
class GetPlayerVelocity(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player Velocity', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('vx', True, '0', 'Vx')
        self.add_data_pin('vy', True, '0', 'Vy')
        self.height = 80

    def execute(self, context):
        phys = self.editor.LevelEditor.game_engine.player.physics
        self.properties['vx'] = phys.entity.movement.velocity_x
        self.properties['vy'] = phys.y_velocity
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        surf.blit(font.render(f"Vx: {self.properties['vx']:.1f}", True, (220,220,220)),
                  (self.x-ox+10, self.y-oy+30))
        surf.blit(font.render(f"Vy: {self.properties['vy']:.1f}", True, (220,220,220)),
                  (self.x-ox+10, self.y-oy+50))

@register_node("Set Player Velocity", category="Player")
class SetPlayerSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set Player Velocity', editor, properties)
        self.add_data_pin('speed', False,
                         str(self.editor.LevelEditor.game_engine.player.speed),
                         'speed')
        self.height = 80

        fld = InputField(rect=(0,0,120,20),
                         text=str(self.properties['speed']),
                         placeholder='Speed...',
                         on_change=lambda t: self._on_change('speed', t))
        self.ui_elements.append(fld)
        fld.update_position = lambda nx, ny: setattr(
            fld, 'rect',
            pygame.Rect(nx-editor.offset[0]+20, ny-editor.offset[1]+50, 120,20)
        )
        fld.update_position(self.x, self.y)

    def _on_change(self, key, txt):
        try:
            self.properties[key] = float(txt)
        except ValueError:
            pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type=='data' and pin.connection:
                getter = pin.connection.node
                getter.execute(context)
                self.properties['speed'] = getter.properties[pin.connection.name]

        self.editor.LevelEditor.game_engine.player.speed = float(self.properties['speed'])
        out = next(p for p in self.outputs if p.pin_type=='exec')
        return out.connection.node if out.connection else None

    def draw(self, surf, selected=False):
        pin=next(p for p in self.inputs if p.name == "speed").connection
        super().draw(surf, selected,draw_ui=False,draw_label=pin)
        if not pin:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)


@register_node("Get Player MaxSpeed", category="Player")
class GetPlayerMaxSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player MaxSpeed', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('max_speed', True, '0', '')
        self.height = 60

    def execute(self, context):
        ms = self.editor.LevelEditor.game_engine.player.movement.max_speed
        self.properties['max_speed'] = ms
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = f"{self.properties['max_speed']:.1f}"
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x-ox+20, self.y-oy+34))

@register_node("Set Player MaxSpeed", category="Player")
class SetPlayerMaxSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set Player MaxSpeed', editor, properties)
        self.add_data_pin('max_speed', False,
                         str(self.editor.LevelEditor.game_engine.player.movement.max_speed),
                         'max speed')
        self.height = 80

        fld = InputField(
            rect=(0,0,120,20),
            text=str(self.properties['max_speed']),
            placeholder='Max Speed...',
            on_change=lambda t: self._on_change('max_speed', t)
        )
        self.ui_elements.append(fld)
        fld.update_position = lambda nx, ny: setattr(
            fld, 'rect',
            pygame.Rect(nx - editor.offset[0] + 20,
                        ny - editor.offset[1] + 50,
                        120, 20)
        )
        fld.update_position(self.x, self.y)

    def _on_change(self, key, txt):
        try:
            self.properties[key] = float(txt)
        except ValueError:
            pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type=='data' and pin.connection:
                getter = pin.connection.node
                getter.execute(context)
                self.properties['max_speed'] = getter.properties[pin.connection.name]

        self.editor.LevelEditor.game_engine.player.movement.max_speed = float(self.properties['max_speed'])
        out = next(p for p in self.outputs if p.pin_type=='exec')
        return out.connection.node if out.connection else None

    def draw(self, surf, selected=False):
        pin=next(p for p in self.inputs if p.name == "max_speed").connection
        super().draw(surf, selected,draw_ui=False,draw_label=pin)
        if not pin:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)

@register_node("Set Player Gravity", category="Player")
class SetPlayerGravity(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set Player Gravity', editor, properties)
        self.add_data_pin('gravity', False,
                         str(self.editor.LevelEditor.game_engine.player.physics.gravity),
                         'gravity')
        self.height = 80
        fld = InputField((0,0,120,20),
                         text=str(self.properties['gravity']),
                         placeholder='Gravity...',
                         on_change=lambda t: self._on_change('gravity', t))
        self.ui_elements.append(fld)
        fld.update_position = lambda nx,ny: setattr(
            fld,'rect', 
            pygame.Rect(nx-editor.offset[0]+20, ny-editor.offset[1]+50, 120,20)
        )
        fld.update_position(self.x,self.y)

    def _on_change(self, key, txt):
        try: self.properties[key] = float(txt)
        except: pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type=='data' and pin.connection:
                getter = pin.connection.node
                getter.execute(context)
                self.properties['gravity'] = getter.properties[pin.connection.name]
        self.editor.LevelEditor.game_engine.player.physics.gravity = float(self.properties['gravity'])
        out = next(p for p in self.outputs if p.pin_type=='exec')
        return out.connection.node if out.connection else None

    def draw(self, surf, selected=False):
        pin=next(p for p in self.inputs if p.name == "gravity").connection
        super().draw(surf, selected,draw_ui=False,draw_label=pin)
        if not pin:
            for el in self.ui_elements:
                el.update_position(self.x,self.y)
                el.draw(surf)

@register_node("Get Player Gravity", category="Player")
class GetPlayerGravity(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player Gravity', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('gravity', True, '0', '')
        self.height = 60

    def execute(self, context):
        g = self.editor.LevelEditor.game_engine.player.physics.gravity
        self.properties['gravity'] = g
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = f"{self.properties['gravity']:.2f}"
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 20, self.y - oy + 34))


@register_node("Is Player On Ground", category="Player")
class GetPlayerMaxHealth(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Is Player On Ground', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('ground', True, False, 'IsOnGround')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.collisions.OnGround()
        self.properties['ground'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['ground']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))



@register_node("Is Player On Wall", category="Player")
class GetPlayerMaxHealth(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Is Player On Ground', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('wall', True, False, 'IsOnWall')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.collisions.OnWall()
        self.properties['wall'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['wall']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))



@register_node("Get Player Position", category="Player")
class GetPlayerVelocity(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player Position', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('x', True, '0', 'x')
        self.add_data_pin('y', True, '0', 'y')
        self.height = 80

    def execute(self, context):
        phys = self.editor.LevelEditor.game_engine.player.rect
        self.properties['x'] = phys.x
        self.properties['y'] = phys.y
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        surf.blit(font.render(f"x: {self.properties['x']:.1f}", True, (220,220,220)),
                  (self.x-ox+10, self.y-oy+30))
        surf.blit(font.render(f"y: {self.properties['y']:.1f}", True, (220,220,220)),
                  (self.x-ox+10, self.y-oy+50))

@register_node("Get Player Direction", category="Player")
class GetPlayerDirection(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Player Direction', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('direction', True, '0', '')
        self.height = 60

    def execute(self, context):
        self.properties['direction'] = self.editor.LevelEditor.game_engine.player.direction
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = self.properties['direction']
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 20, self.y - oy + 34))


@register_node("Is Player Jumping", category="Player")
class IsPlayerJumping(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Is Player Jumping', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('jumping', True, '0', '')
        self.height = 60

    def execute(self, context):
        self.properties['jumping'] = self.editor.LevelEditor.game_engine.player.physics.is_jumping
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = str(self.properties['jumping'])
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 20, self.y - oy + 34))



@register_node("Is Player Dashing", category="Player")
class IsPlayerDashing(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Is Player Dashing', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('dashing', True, '0', '')
        self.height = 60

    def execute(self, context):
        self.properties['dashing'] = self.editor.LevelEditor.game_engine.player.movement.is_dashing
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        ox, oy = self.editor.offset
        txt = str(self.properties['dashing'])
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 20, self.y - oy + 34))
        


@register_node("Respawn Player", category="Player")
class Respawn(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Respawn Player', editor, properties)

    def execute(self, context):
        self.editor.LevelEditor.game_engine.player.reset_pos()
        out = next(p for p in self.outputs if p.pin_type=='exec')
        return out.connection.node if out.connection else None

@register_node("Set SpawnPoint", category="Player")
class SetSpawnPointPlayer(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set SpawnPoint', editor, properties)
        self.editor = editor

        # Récupère la liste des location points
        pts = list(self.editor.LevelEditor.dataManager.get_location_point_name())
        if not pts:
            # Alerte et passe en invalid state
            self.editor.LevelEditor.nm.notify(
                'warning',
                'Set SpawnPoint',
                "Aucun locationPoint n'est posé : node désactivée",
                1.5
            )
            self.valid = False
            return
        # OK, on peut créer la dropdown
        self.valid = True
        self.btn = DropdownButton(
            self,
            pygame.Rect(10, 30, 120, 24),
            pts,
            callback=self._on_select
        )
        # Valeur par défaut ou restaurée
        if 'choice' in self.properties and self.properties['choice'] in pts:
            self.btn.selected = self.properties['choice']
        else:
            self.properties['choice'] = pts[0]
            self.btn.selected = pts[0]
        self.ui_elements.append(self.btn)

    def _on_select(self, opt: str):
        if not self.valid:
            return
        self.properties['choice'] = opt

    def updateDropDownField(self):
        if not self.valid:
            return
        pts = list(self.editor.LevelEditor.dataManager.get_location_point_name())
        self.btn.options = pts
        # Si la sélection a disparu, on remet au premier élément
        if pts and self.btn.selected not in pts:
            self.btn.selected = pts[0]
            self.properties['choice'] = pts[0]

    def draw(self, surf, selected=False):
        ox, oy = self.editor.offset
        if not getattr(self, 'valid', False):
            # Dimensions et position
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)

            # Fond et bordure d'erreur
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)

            # Header
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)

            # Titre
            font_title =FontManager().get(size=18)
            title_surf = font_title.render("Set SpawnPoint [Error]", True, (255, 200, 200))
            surf.blit(title_surf, (x + 6, y + 4))

            # Message dans le corps
            font_msg = FontManager().get(size=15)
            lines = [
                "Aucun point de localisation",
                "disponible !",
                "(Veuillez supprimer cette",
                "node)"
            ]
            font_msg = FontManager().get(size=15)
            base_x = x + 6
            base_y = y + self.HEADER_HEIGHT + 10
            line_height = 12

            for i, line in enumerate(lines):
                msg_surf = font_msg.render(line, True, (255, 180, 180))
                surf.blit(msg_surf, (base_x, base_y + i * line_height))
                                

            return
        self.updateDropDownField()
        super().draw(surf, selected)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)


    def execute(self, context):
        if not getattr(self, 'valid', False):
            return None
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                getter = pin.connection.node
                getter.execute(context)
                self.properties[pin.name] = getter.properties[pin.name]

        self.editor.LevelEditor.game_engine.player.spawn_name=self.btn.selected
        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


@register_node("Apply Force", category="Physics")
class ApplyForceNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Apply Force', editor, properties)

        for key, default in (('force_x', '0.0'), ('force_y', '0.0'), ('duration', '0.0')):
            self.add_data_pin(key, False,
                              str(self.properties.get(key, default)),
                              key.replace('_', ' ').title())

        self.ui_elements = []
        for key in ('force_x', 'force_y', 'duration'):
            fld = InputField(
                rect=(0, 0, 80, 20),
                text=str(self.properties.get(key, '')),
                placeholder=key.replace('_', ' ').title(),
                on_change=lambda t, k=key: self._on_change(k, t)
            )
            fld.prop_name = key
            fld.pin = next(p for p in self.inputs if p.name == key)
            self.ui_elements.append(fld)

        self.height = 140

    def _on_change(self, key, txt):
        if key in ('force_x', 'force_y'):
            try:
                self.properties[key] = float(txt)
            except ValueError:
                pass
        elif key == 'duration':
            if txt.lower() in ('none', ''):
                self.properties[key] = None
            else:
                try:
                    self.properties[key] = int(txt)
                except ValueError:
                    pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection.node
                src.execute(context)
                self.properties[pin.name] = src.properties.get(pin.connection.name)

        fx = float(self.properties.get('force_x', 0.0))
        fy = float(self.properties.get('force_y', 0.0))
        dur = float(self.properties.get('duration', 0.0))

        player = self.editor.LevelEditor.game_engine.player
        player.movement.add_force(force_x=fx, force_y=fy, duration_ms=dur)

        out_pin = next(p for p in self.outputs if p.pin_type == 'exec')
        return out_pin.connection.node if out_pin.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected, draw_ui=False)

        margin = 6

        for fld in self.ui_elements:
            pin = next(p for p in self.inputs if p.name == fld.prop_name)
            if not pin.connection:
                px, py = pin.pos
                fld.rect.topleft = (
                    px + 4 + margin,
                    py - fld.rect.height // 2
                )
                fld.draw(surf)




@register_node("Clear Forces", category="Player")
class ClearForces(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Clear Forces', editor, properties)

    def execute(self, context):
        self.editor.LevelEditor.game_engine.player.movement.clear_forces()
        out = next(p for p in self.outputs if p.pin_type=='exec')
        return out.connection.node if out.connection else None
    

@register_node("Is Player Colliding With", category="Player")
class GetPlayerCollision(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Is Player Colliding With", editor, properties)
        self.inputs.clear()
        self.outputs.clear()

        self.rect_names = [
            cr.name for cr in editor.LevelEditor.dataManager.collisionRects
        ]

        if not self.rect_names:
            editor.LevelEditor.nm.notify(
                'warning',
                'Is Player Colliding With',
                "Aucun CollisionRect défini : node désactivée",
                1.5
            )
            self.valid = False
            self.height = 60
            self.add_data_pin('colliding', True, 'False', 'IsCol')
            return

        self.valid = True
        self.dropdown = DropdownButton(
            self,
            pygame.Rect(0, 30, 100, 24),
            self.rect_names,
            callback=self._on_select
        )

        choice = properties.get('choice')
        if choice in self.rect_names:
            self.dropdown.selected = choice
        else:
            self.dropdown.selected = self.rect_names[0]
            self.properties['choice'] = self.rect_names[0]

        self.ui_elements.append(self.dropdown)

        self.add_data_pin('colliding', True, 'False', 'IsCol')

        self.height = 80

    def _on_select(self, opt: str):
        if not getattr(self, 'valid', False):
            return
        self.properties['choice'] = opt

    def execute(self, context):
        if not getattr(self, 'valid', False):
            self.properties['colliding'] = False
            return None

        name = self.properties.get('choice', "")
        player = self.editor.LevelEditor.game_engine.player
        hit = player.collisions.checkWithByName(name)
        self.properties['colliding'] = bool(hit)
        return None

    def draw(self, surf, selected=False):
        ox, oy = self.editor.offset

        if not getattr(self, 'valid', False):
            x, y = self.x - ox, self.y - oy
            w, h = self.WIDTH, self.height
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60,20,20), rect, border_radius=4)
            pygame.draw.rect(surf, (200,50,50), rect, 2, border_radius=4)
            font = FontManager().get(size=16)
            surf.blit(font.render("No CollisionRects!", True, (255,180,180)), (x+6, y+30))
            return

        all_names = [cr.name for cr in self.editor.LevelEditor.dataManager.collisionRects]
        self.dropdown.options = all_names
        if self.dropdown.selected not in all_names and all_names:
            self.dropdown.selected = all_names[0]
            self.properties['choice'] = all_names[0]

        super().draw(surf, selected, draw_ui=False)

        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

        self.execute({})

        txt = str(self.properties.get('colliding', False))
        font = FontManager().get(size=18)
        surf.blit(font.render(txt, True, (220,220,220)),
                  (self.x - ox + 117, self.y - oy + 62))


@register_node("Get Current Animation", category="Player")
class GetCurrentAnim(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Current Animation', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('current_animation', True, 'None', 'Current Anim')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.animation.current_animation
        self.properties['current_animation'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['current_animation']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))

@register_node("Get Animation Play Count", category="Player")
class GetAnimationCount(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Animation Count', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('animation_count', True, 'None', 'Current Anim Count')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.animation.animation_count
        self.properties['animation_count'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['animation_count']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))


@register_node("Get Current Frame", category="Player")
class GetCurrentFrame(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Current Frame', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('frame', True, 'None', 'Get Current Frame')
        self.height = 60

    def execute(self, context):
        current = self.editor.LevelEditor.game_engine.player.animation.current_frame
        self.properties['frame'] = current
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['frame']}", True, (220,220,220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))



@register_node("Force Set Animation", category="Player")
class ForceSetAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Force Set Animation', editor, properties)
        self.anim_mgr = self.editor.LevelEditor.game_engine.player.animation

        self.btn_anim = DropdownButton(
            self,
            pygame.Rect(15, 30, 110, 24),
            list(self.anim_mgr.animations.keys()),
            callback=self._on_select_anim
        )
        self.btn_cancel = DropdownButton(
            self,
            pygame.Rect(15, 60, 110, 24),
            ["True", "False"],
            callback=self._on_select_cancel
        )

        if 'choice' in self.properties:
            self.btn_anim.selected = self.properties['choice']
        if 'isCancelable' in self.properties:
            self.btn_cancel.selected = str(self.properties['isCancelable'])

        self.ui_elements.extend([self.btn_anim, self.btn_cancel])

    def _on_select_anim(self, opt: str):
        self.properties['choice'] = opt

    def _on_select_cancel(self, opt: str):
        self.properties['isCancelable'] = (opt == "True")

    def updateDropDownField(self):
        opts = list(self.anim_mgr.animations.keys())
        self.btn_anim.options = opts
        if self.btn_anim.selected not in opts and opts:
            self.btn_anim.selected = opts[0]
            self.properties['choice'] = opts[0]
        if self.btn_cancel.selected not in ["True", "False"]:
            self.btn_cancel.selected = "True"
            self.properties['isCancelable'] = True

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
                src.node.execute(context)
                self.properties[pin.name] = src.node.properties[pin.name]

        anim_name = self.properties.get('choice')
        cancelable = self.properties.get('isCancelable', True)

        if anim_name in self.anim_mgr.animations:
            anim_obj = self.anim_mgr.animations[anim_name]
            anim_obj.isCancelable = cancelable
            self.anim_mgr.forceSetAnimation(anim_name)

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None


@register_node("Set Animation", category="Player")
class SetAnimation(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set Animation', editor, properties)
        self.anim_mgr = self.editor.LevelEditor.game_engine.player.animation

        self.btn_anim = DropdownButton(
            self,
            pygame.Rect(15, 30, 110, 24),
            list(self.anim_mgr.animations.keys()),
            callback=self._on_select_anim
        )
        self.btn_cancel = DropdownButton(
            self,
            pygame.Rect(15, 60, 110, 24),
            ["True", "False"],
            callback=self._on_select_cancel
        )

        if 'choice' in self.properties:
            self.btn_anim.selected = self.properties['choice']
        if 'isCancelable' in self.properties:
            self.btn_cancel.selected = str(self.properties['isCancelable'])

        self.ui_elements.extend([self.btn_anim, self.btn_cancel])

    def _on_select_anim(self, opt: str):
        self.properties['choice'] = opt

    def _on_select_cancel(self, opt: str):
        self.properties['isCancelable'] = (opt == "True")

    def updateDropDownField(self):
        opts = list(self.anim_mgr.animations.keys())
        self.btn_anim.options = opts
        if self.btn_anim.selected not in opts and opts:
            self.btn_anim.selected = opts[0]
            self.properties['choice'] = opts[0]
        if self.btn_cancel.selected not in ["True", "False"]:
            self.btn_cancel.selected = "True"
            self.properties['isCancelable'] = True

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
                src.node.execute(context)
                self.properties[pin.name] = src.node.properties[pin.name]

        anim_name = self.properties.get('choice')
        cancelable = self.properties.get('isCancelable', True)

        if anim_name in self.anim_mgr.animations:
            anim_obj = self.anim_mgr.animations[anim_name]
            anim_obj.isCancelable = cancelable
            self.anim_mgr.setAnimation(anim_name)

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

@register_node("Set Pl Anim Speed", category="Player")
class SetAnimationSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set Pl Anim Speed', editor, properties)
        # Data pin pour injecter une valeur éventuelle
        current_speed = self.editor.LevelEditor.game_engine.player.animation.getCurrentAnimation().frameRate
        self.add_data_pin('speed', False, str(current_speed), 'Speed')
        # Champ texte pour saisir manuellement
        speed_field = InputField(
            rect=(0, 0, 120, 20),
            text=str(self.properties.get('speed', current_speed)),
            placeholder='Animation Speed',
            on_change=lambda t: self._on_change('speed', t)
        )
        speed_field.update_position = lambda nx, ny: setattr(
            speed_field, 'rect',
            pygame.Rect(
                nx - editor.offset[0] + 10,
                ny - editor.offset[1] + 50,
                120, 20
            )
        )
        speed_field.update_position(self.x, self.y)
        self.ui_elements.append(speed_field)

    def _on_change(self, key, txt):
        try:
            self.properties[key] = txt
        except Exception:
            pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                src.node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]

        try:
            speed_val = float(self.properties['speed'])
        except (KeyError, ValueError):
            speed_val = self.editor.LevelEditor.game_engine.player.animation.getCurrentAnimation().frameRate

        anim_mgr = self.editor.LevelEditor.game_engine.player.animation
        anim = anim_mgr.getCurrentAnimation()
        anim.frameRate = int(speed_val)

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)


@register_node("Get Pl Anim Speed", category="Player")
class GetAnimationSpeed(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get Pl Anim Speed', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('speed', True, '0', 'Current Speed')
        self.height = 60

    def execute(self, context):
        anim_mgr = self.editor.LevelEditor.game_engine.player.animation
        current_speed = anim_mgr.getCurrentAnimation().frameRate
        self.properties['speed'] = current_speed
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['speed']}", True, (220, 220, 220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))



@register_node("Set z index", category="Player")
class SetPlayerIndex(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Set z index', editor, properties)
        current_index = self.editor.LevelEditor.game_engine.level.player_z_index
        self.add_data_pin('index', False, str(current_index), 'index')
        index_field = InputField(
            rect=(0, 0, 120, 20),
            text=str(self.properties.get('index', current_index)),
            placeholder='Pl z-index',
            on_change=lambda t: self._on_change('index', t)
        )
        index_field.update_position = lambda nx, ny: setattr(
            index_field, 'rect',
            pygame.Rect(
                nx - editor.offset[0] + 10,
                ny - editor.offset[1] + 50,
                120, 20
            )
        )
        index_field.update_position(self.x, self.y)
        self.ui_elements.append(index_field)

    def _on_change(self, key, txt):
        try:
            self.properties[key] = txt
        except Exception:
            pass

    def execute(self, context):
        for pin in self.inputs:
            if pin.pin_type == 'data' and pin.connection:
                src = pin.connection
                src.node.execute(context)
                self.properties[pin.name] = src.node.properties[src.name]

        try:
            index = int(self.properties['index'])
        except (KeyError, ValueError):
            index = self.editor.LevelEditor.game_engine.level.player_z_index

        self.editor.LevelEditor.game_engine.level.player_z_index = int(index)

        out = next((p for p in self.outputs if p.pin_type == 'exec'), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)


@register_node("Get z index", category="Player")
class GetZIndex(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, 'Get z index', editor, properties)
        self.inputs.clear()
        self.outputs.clear()
        self.add_data_pin('index', True, '0', 'Current index')
        self.height = 60

    def execute(self, context):
        self.properties['index'] = self.editor.LevelEditor.game_engine.level.player_z_index
        return None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        self.execute({})
        font = FontManager().get(size=18)
        text = font.render(f"{self.properties['index']}", True, (220, 220, 220))
        ox, oy = self.editor.offset
        x = self.x - ox + 20
        y = self.y - oy + 34
        surf.blit(text, (x, y))