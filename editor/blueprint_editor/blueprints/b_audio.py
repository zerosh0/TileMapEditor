import os
import pygame
from editor.blueprint_editor.node import DropdownButton, Node, register_node
from editor.ui.Font import FontManager
from editor.ui.Input import InputField

@register_node("Play Sound", category="Audio")
class PlaySoundNode(Node):
    SOUND_DIR = os.path.join("editor", "game_engine", "Assets", "sounds_effects")
    _sound_cache = {}

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Play Sound", editor, properties)
        self.editor = editor
        if self.editor.LevelEditor.dataManager.settings.path is None or not "/Exemples/new_exemple.json" in self.editor.LevelEditor.dataManager.settings.path:
            self.SOUND_DIR = os.path.join("Ressources", "audio_files")
        try:
            files = [
                f for f in os.listdir(self.SOUND_DIR)
                if os.path.splitext(f)[1].lower() in (".wav", ".mp3", ".ogg")
            ]
        except FileNotFoundError:
            files = []

        if not files:
            self.valid = False
            self.editor.LevelEditor.nm.notify(
                'warning',
                'Play Sound',
                "Aucun fichier son trouvé dans sounds_effects/",
                1.5
            )
            self.height = 70
            return

        self.valid = True
        self.btn = DropdownButton(
            self,
            pygame.Rect(0, 40, 140, 24),
            files,
            callback=self._on_select
        )
        choice = self.properties.get("choice")
        if choice in files:
            self.btn.selected = choice
        else:
            self.btn.selected = files[0]
            self.properties["choice"] = files[0]

        self.ui_elements.append(self.btn)
        self.height = 80

    def _on_select(self, opt: str):
        if not getattr(self, "valid", False):
            return
        self.properties["choice"] = opt

    def updateDropDownField(self):
        if not getattr(self, "valid", False):
            return
        
        try:
            files = [
                f for f in os.listdir(self.SOUND_DIR)
                if os.path.splitext(f)[1].lower() in (".wav", ".mp3", ".ogg")
            ]
        except FileNotFoundError:
            files = []
        self.btn.options = files
        if files and self.btn.selected not in files:
            self.btn.selected = files[0]
            self.properties["choice"] = files[0]

    def draw(self, surf, selected=False):
        ox, oy = self.editor.offset
        if not getattr(self, "valid", False):
            w, h = self.WIDTH, self.height
            x, y = self.x - ox, self.y - oy
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(surf, (60, 20, 20), rect, border_radius=4)
            pygame.draw.rect(surf, (200, 50, 50), rect, 2, border_radius=4)
            hdr = pygame.Rect(x, y, w, self.HEADER_HEIGHT)
            pygame.draw.rect(surf, (150, 0, 0), hdr, border_top_left_radius=4, border_top_right_radius=4)

            font_t = FontManager().get(size=18)
            surf.blit(font_t.render("Play Sound [Error]", True, (255,200,200)), (x+6, y+4))

            font_m = FontManager().get(size=14)
            msg = "Aucun son disponible"
            surf.blit(font_m.render(msg, True, (255,180,180)), (x+6, y+self.HEADER_HEIGHT+10))
            msg2 = "(supprimer cette node)"
            surf.blit(font_m.render(msg2, True, (255,180,180)), (x+6, y+self.HEADER_HEIGHT+26))
            return

        self.updateDropDownField()
        super().draw(surf, selected)
        for el in self.ui_elements:
            el.update_position(self.x, self.y)
            el.draw(surf)

    def execute(self, context):
        if not getattr(self, "valid", False):
            return None

        fname = self.properties.get("choice")
        if fname:
            full_path = os.path.join(self.SOUND_DIR, fname)
            cache = PlaySoundNode._sound_cache
            if fname not in cache:
                cache[fname] = pygame.mixer.Sound(full_path)
            cache[fname].play()

        out = next((p for p in self.outputs if p.pin_type=="exec"), None)
        return out.connection.node if out and out.connection else None

@register_node("Set Volume", category="Audio")
class SetVolumeNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Set Volume", editor, properties)
        self.add_data_pin("volume", False, self.properties.get("volume", 1.0), "Vol")
        self.volume_field = InputField(
            rect=(10, 30, 60, 18),
            text=str(self.properties.get("volume", 1.0)),
            placeholder="0.0-1.0",
            on_change=lambda t: self._on_volume_change(t)
        )
        self.ui_elements.append(self.volume_field)
        self.height = 80

    def _on_volume_change(self, txt):
        try:
            v = float(txt)
            v = max(0.0, min(1.0, v))
            self.properties["volume"] = v
        except ValueError:
            pass

    def execute(self, context):
        pin = next((p for p in self.inputs if p.name=="volume"), None)
        if pin and pin.connection:
            getter = pin.connection.node
            getter.execute(context)
            try:
                self.properties["volume"] = float(getter.properties[pin.name])
            except:
                pass

        vol = self.properties.get("volume", 1.0)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.set_volume(vol)
        pygame.mixer.set_num_channels(pygame.mixer.get_num_channels())
        out = next((p for p in self.outputs if p.pin_type=="exec"), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        ox, oy = self.editor.offset
        x = self.x - ox + 10
        y = self.y - oy + 30
        self.volume_field.rect.topleft = (x, y)
        self.volume_field.draw(surf)
        vol = self.properties.get("volume", 1.0)
        font = FontManager().get(size=18)
        txt = font.render(f"{vol:.2f}", True, (220, 220, 220))
        surf.blit(txt, (self.x - ox + 80, self.y - oy + 32))


@register_node("Stop All Sounds", category="Audio")
class StopAllSoundsNode(Node):
    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Stop All Sounds", editor, properties)
        self.height = 60

    def execute(self, context):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.stop()
        pygame.mixer.music.stop()
        out = next((p for p in self.outputs if p.pin_type=="exec"), None)
        return out.connection.node if out and out.connection else None

    def draw(self, surf, selected=False):
        super().draw(surf, selected)
        font = FontManager().get(size=16)
        ox, oy = self.editor.offset
        txt = font.render("all stopped", True, (200,200,200))
        surf.blit(txt, (self.x - ox + 10, self.y - oy + 30))


@register_node("Emit Sound From", category="Audio")
class SpatialSoundNode(Node):
    SOUND_DIR = os.path.join("editor", "game_engine", "Assets", "sounds_effects")
    
    _sound_cache = {}

    @staticmethod
    def _load_sound(fname):
        full = os.path.join(SpatialSoundNode.SOUND_DIR, fname)
        if fname not in SpatialSoundNode._sound_cache:
            SpatialSoundNode._sound_cache[fname] = pygame.mixer.Sound(full)
        return SpatialSoundNode._sound_cache[fname]

    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Emit Sound From", editor, properties)
        if self.editor.LevelEditor.dataManager.settings.path is None or not "/Exemples/new_exemple.json" in self.editor.LevelEditor.dataManager.settings.path:
            self.SOUND_DIR = os.path.join("Ressources", "audio_files")
        self.add_data_pin("volume", False, properties.get("volume", 1.0), "volume")
        self.add_data_pin("radius", False, properties.get("radius", 200.0), "radius")
        self.add_data_pin("smooth", False, properties.get("smooth", 0.1), "smooth")

        self.vol_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties.get("volume",1.0)),
            placeholder="0.0-1.0",
            on_change=lambda t: self._on_change("volume", t)
        )
        self.rad_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties.get("radius",200.0)),
            placeholder="Radius",
            on_change=lambda t: self._on_change("radius", t)
        )
        self.smo_field = InputField(
            rect=(0,0,60,18),
            text=str(self.properties.get("smooth",0.1)),
            placeholder="Smooth",
            on_change=lambda t: self._on_change("smooth", t)
        )

        files = [
            f for f in os.listdir(self.SOUND_DIR)
            if os.path.splitext(f)[1].lower() in (".wav", ".mp3", ".ogg")
        ]
        self.btn_sound = DropdownButton(
            self, pygame.Rect(0,0,140,24),
            files,
            callback=lambda f: self.properties.__setitem__("choice", f)
        )
        pts = list(editor.LevelEditor.dataManager.get_location_point_name())
        self.btn_loc = DropdownButton(
            self, pygame.Rect(0,0,140,24),
            pts,
            callback=lambda l: self.properties.__setitem__("loc", l)
        )

        def make_updater(el, pin_name, x_offset=8, y_offset=0):
            def updater(nx, ny):
                # Récupère directement la position écran du pin
                pin = next(p for p in self.inputs if p.name == pin_name)
                px, py = pin.pos
                el.rect.topleft = (
                    px + x_offset,
                    py + y_offset - el.rect.h // 2
                )
            return updater


        self.vol_field.update_position = make_updater(self.vol_field, "volume")
        self.rad_field.update_position = make_updater(self.rad_field, "radius")
        self.smo_field.update_position = make_updater(self.smo_field, "smooth")
        self.add_data_pin("__sound_ui__", False, 0, "",6)  
        self.add_data_pin("__loc_ui__",   False, 0, "",12)
        self.btn_sound.update_position = make_updater(self.btn_sound, "__sound_ui__", x_offset=10, y_offset=0)
        self.btn_loc.update_position   = make_updater(self.btn_loc,   "__loc_ui__",   x_offset=10, y_offset=0)

        self.ui_elements.extend([
            self.vol_field, self.rad_field, self.smo_field,
            self.btn_loc, self.btn_sound
        ])
        self.height = 200

        default_sound = properties.get("choice", files[0])
        self.properties["choice"] = default_sound
        self.btn_sound.selected = default_sound

        default_loc = properties.get("loc", pts[0] if pts else None)
        self.properties["loc"] = default_loc
        self.btn_loc.selected = default_loc

        for el in self.ui_elements:
            el.update_position(self.x, self.y)

    def _on_change(self, key, txt):
        try:
            self.properties[key] = float(txt)
        except ValueError:
            pass

    def draw(self, surf, selected=False):
        super().draw(surf, selected, draw_ui=False)
        pin_vol = next(p for p in self.inputs if p.name == "volume")
        if not pin_vol.connection:
            self.vol_field.update_position(self.x, self.y)
            self.vol_field.draw(surf)

        pin_rad = next(p for p in self.inputs if p.name == "radius")
        if not pin_rad.connection:
            self.rad_field.update_position(self.x, self.y)
            self.rad_field.draw(surf)

        pin_smo = next(p for p in self.inputs if p.name == "smooth")
        if not pin_smo.connection:
            self.smo_field.update_position(self.x, self.y)
            self.smo_field.draw(surf)

        pin_loc = next(p for p in self.inputs if p.name == "__loc_ui__")
        if not pin_loc.connection:
            self.btn_loc.update_position(self.x, self.y)
            self.btn_loc.draw(surf)

        pin_sound = next(p for p in self.inputs if p.name == "__sound_ui__")
        if not pin_sound.connection:
            self.btn_sound.update_position(self.x, self.y)
            self.btn_sound.draw(surf)

    def execute(self, context):
        # récupère pin ou propriété
        def get_val(nm):
            pin = next(p for p in self.inputs if p.name == nm)
            if pin.connection:
                upstream = pin.connection.node
                upstream.execute(context)
                return float(upstream.properties[pin.connection.name])
            return float(self.properties.get(nm, 0))

        fname   = self.properties["choice"]
        loc     = self.properties["loc"]
        vol     = get_val("volume")
        radius  = get_val("radius")
        smooth  = get_val("smooth")

        pl = self.editor.LevelEditor.game_engine.player
        pl.audio_manager.add_emitter(fname, loc, radius, smooth, volume=vol)

        out = next(p for p in self.outputs if p.name=="out")
        return out.connection.node if out and out.connection else None


@register_node("StopEmission", category="Audio")
class StopEmission(Node):


    def __init__(self, pos, editor, properties):
        super().__init__(pos, "Stop Emission From", editor, properties)
        pts = list(editor.LevelEditor.dataManager.get_location_point_name())
        self.btn_loc = DropdownButton(
            self, pygame.Rect(0,0,140,24),
            pts,
            callback=lambda l: self.properties.__setitem__("loc", l)
        )

        def make_updater(el, pin_name, x_offset=8, y_offset=0):
            def updater(nx, ny):
                pin = next(p for p in self.inputs if p.name == pin_name)
                px, py = pin.pos
                el.rect.topleft = (
                    px + x_offset,
                    py + y_offset - el.rect.h // 2
                )
            return updater


        self.add_data_pin("__loc_ui__",   False, 0, "",12)
        self.btn_loc.update_position   = make_updater(self.btn_loc,   "__loc_ui__",   x_offset=10, y_offset=0)

        self.ui_elements.append(self.btn_loc)
        self.height = 120


        default_loc = properties.get("loc", pts[0] if pts else None)
        self.properties["loc"] = default_loc
        self.btn_loc.selected = default_loc

        for el in self.ui_elements:
            el.update_position(self.x, self.y)

    def _on_change(self, key, txt):
        try:
            self.properties[key] = float(txt)
        except ValueError:
            pass

    def draw(self, surf, selected=False):
        super().draw(surf, selected, draw_ui=False)

        pin_loc = next(p for p in self.inputs if p.name == "__loc_ui__")
        if not pin_loc.connection:
            self.btn_loc.update_position(self.x, self.y)
            self.btn_loc.draw(surf)


    def execute(self, context):
        loc = self.properties["loc"]
        pl = self.editor.LevelEditor.game_engine.player
        pl.audio_manager.remove_emitter(loc)

        out = next(p for p in self.outputs if p.name=="out")
        return out.connection.node if out and out.connection else None
