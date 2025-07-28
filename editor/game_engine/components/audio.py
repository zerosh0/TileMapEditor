import math
import pygame
from editor.blueprint_editor.blueprints.b_audio import SpatialSoundNode

class AudioManager:
    def __init__(self, player, unload_factor=1.5, fade_ms=200, default_smooth=0.05):
        self.player         = player
        self.emitters       = []
        self.unload_factor  = unload_factor
        self.fade_ms        = fade_ms
        self.default_smooth = default_smooth
        self._cache         = {}

    def load_sound(self, fname):
        if fname not in self._cache:
            self._cache[fname] = SpatialSoundNode._load_sound(fname)
        return self._cache[fname]

    def add_emitter(self, fname, loc_name, radius, smooth=None, volume=1.0):
        total_ch = pygame.mixer.get_num_channels()
        busy_ch  = sum(1 for e in self.emitters if e["channel"].get_busy())

        if busy_ch >= total_ch:
            farthest, max_dist = None, -1
            px, py = self.player.rect.center
            for e in self.emitters:
                lx, ly = self.player.level.get_location_by_name(e["loc"])
                d = math.hypot(lx - px, ly - py)
                if d > max_dist:
                    max_dist, farthest = d, e
            if farthest:
                farthest["channel"].fadeout(self.fade_ms)
                self.emitters.remove(farthest)
            else:
                self.player.nm.notify(
                    'warning', 'AudioManager',
                    "Plus aucun canal libre et impossible de libérer un émetteur !",
                    duration=2.0
                )
                return


        snd     = self.load_sound(fname)
        ch      = pygame.mixer.find_channel(force=True)
        ch.play(snd, loops=-1)

        px, py = self.player.rect.center
        lx, ly = self.player.level.get_location_by_name(loc_name)
        dx, dy = lx - px, ly - py
        dist   = math.hypot(dx, dy)
        if dist <= radius:
            init_vol = max(0.0, 1.0 - dist / radius)
        else:
            init_vol = 0.0

        pan  = max(-1.0, min(1.0, dx / radius))
        base = init_vol * volume
        left  = min(1.0, max(0.0, base * (1 - pan) / 2))
        right = min(1.0, max(0.0, base * (1 + pan) / 2))
        ch.set_volume(left, right)

        self.emitters.append({
            "sound":    snd,
            "loc":      loc_name,
            "radius":   radius,
            "smooth":   smooth if smooth is not None else self.default_smooth,
            "gain":     volume,
            "channel":  ch,
            "vol":      init_vol,
            "removing": False,
            "unloaded": False,
        })

    def remove_emitter(self, loc_name):
        for e in self.emitters:
            if e["loc"] == loc_name and not e["removing"]:
                e["removing"] = True

    def clear_sounds(self):
        for e in list(self.emitters):
            e["channel"].fadeout(self.fade_ms)
        self.emitters.clear()

    def update_all(self):
        px, py = self.player.rect.center

        for e in list(self.emitters):
            lx, ly = self.player.level.get_location_by_name(e["loc"])
            dx, dy = lx - px, ly - py
            dist    = math.hypot(dx, dy)
            r_full  = e["radius"]
            r_unld  = r_full * self.unload_factor

            if e["removing"]:
                target_vol = 0.0
            elif dist > r_unld:
                e["unloaded"] = True
                target_vol = 0.0
            else:
                if e["unloaded"]:
                    e["unloaded"] = False
                target_vol = 0.0 if dist >= r_full else (1.0 - dist / r_full)


            e["vol"] += (target_vol - e["vol"]) * e["smooth"]


            if e["removing"] and e["vol"] < 0.01:
                e["channel"].fadeout(self.fade_ms)
                self.emitters.remove(e)
                continue

            pan  = max(-1.0, min(1.0, dx / r_full))
            base = e["vol"] * e["gain"]
            left  = min(1.0, max(0.0, base * (1 - pan) / 2))
            right = min(1.0, max(0.0, base * (1 + pan) / 2))
            e["channel"].set_volume(left, right)
