import json
from typing import Dict, List, Tuple, Optional
import pygame


class Animation:

    def __init__(self, name: str, frames: List[pygame.Surface], frameRate: int,
                 offset: List[Tuple[int, int]], isCancelable: bool,
                 sound: Optional[pygame.mixer.Sound] = None):

        self.name: str = name
        self.frames: List[pygame.Surface] = frames
        self.frameRate: int = frameRate
        self.frameOffset: List[Tuple[int, int]] = offset
        self.isCancelable: bool = isCancelable
        self.sound: Optional[pygame.mixer.Sound] = sound


class AnimationManager:

    def __init__(self, spritesheet: str, colorkey, initial_animation: str, clock: pygame.time.Clock,entity: None):

        self.animations: Dict[str, Animation] = {}
        self.spritesheet = pygame.image.load(spritesheet).convert()
        self.colorkey = colorkey
        self.clock = clock
        self.current_animation = initial_animation
        self.current_frame = 0
        self.isAnimationAllowed = True
        self.last_update = pygame.time.get_ticks()
        self.accumulated_time = 0
        self.animation_count=0

        self.flash_active = False
        self.flash_color = (255, 255, 255,128)
        self.flash_duration = 0
        self.flash_start_time = 0
        self.flash_blend_mode = pygame.BLEND_RGBA_ADD
        self.entity=entity

    def start_flash_effect(self, color: tuple, duration: int, alpha: int = 128):
            self.flash_color = (*color, alpha)
            self.flash_duration = duration
            self.flash_start_time = pygame.time.get_ticks()
            self.flash_active = True

    def flipFrames(self):
        for anim_name, animation in self.animations.items():
            animation.frames = [
                pygame.transform.flip(frame, True, False) for frame in animation.frames
            ]

    def getCurrentFrame(self) -> pygame.Surface:
        frame = self.animations[self.current_animation].frames[self.current_frame]
        
        if self.flash_active:
            # Assure-toi que la frame possède un canal alpha
            tinted_frame = frame.copy().convert_alpha()
            
            # Crée une copie que l'on va teinter
            colored_sprite = tinted_frame.copy()
            # Applique le flash_color en multipliant les couleurs,
            # ce qui ne modifiera que les pixels non transparents
            colored_sprite.fill(self.flash_color, special_flags=pygame.BLEND_RGBA_MULT)
            
            # Ajoute la version teintée sur l'original en conservant la transparence
            tinted_frame.blit(colored_sprite, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            
            return tinted_frame
        
        return frame



    def getCurrentAnimation(self) -> Animation:
        return self.animations[self.current_animation]

    def getFrame(self, x: int, y: int, width: int, height: int, scale: float) -> pygame.Surface:
        image = pygame.Surface((width, height)).convert()
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image.set_colorkey(self.colorkey)
        if scale != 1.0:
            image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        return image

    def addAnimation(self, name: str, frames_data: List[Tuple], sound: Optional[pygame.mixer.Sound],
                     scale: float = 2.0, frameRate: int = 60, isCancelable: bool = True):
        frames: List[pygame.Surface] = []
        offsets: List[Tuple[int, int]] = []

        for frame_data in frames_data:
            if len(frame_data) == 4:
                x, y, width, height = frame_data
                offset = (0, 0)
            elif len(frame_data) == 6:
                x, y, width, height, offset_x, offset_y = frame_data
                offset = (offset_x, offset_y)
            else:
                raise ValueError("Chaque frame_data doit contenir 4 ou 6 valeurs.")
            
            frames.append(self.getFrame(x, y, width, height, scale))
            offsets.append(offset)

        self.animations[name] = Animation(name, frames, frameRate, offsets, isCancelable, sound)

    def getAnimation(self, name: str) -> Optional[Animation]:
        return self.animations.get(name)


    def addAutoAnimationsFromFile(self, file: str, scale: float = 2.0):
        try:
            with open(file, "r") as f:
                data = json.load(f)
                animations_data = data.get("animations", {})

                for anim_name, anim in animations_data.items():
                    spritesheet_path = anim.get("spritesheet")
                    frame_size = anim.get("frame_size")
                    frame_width, frame_height = frame_size
                    frame_duration = anim.get("frame_duration", 100)

                    if not spritesheet_path:
                        print(f"Pas de spritesheet pour l'animation {anim_name}.")
                        continue

                    try:
                        self.spritesheet = pygame.image.load(spritesheet_path).convert()
                    except Exception as e:
                        print(f"Erreur lors du chargement de la spritesheet {spritesheet_path} : {e}")
                        continue

                    # Découper toutes les frames depuis la spritesheet
                    frames = []
                    offsets = []
                    spritesheet_width, spritesheet_height = self.spritesheet.get_size()

                    for y in range(0, spritesheet_height, frame_height):
                        for x in range(0, spritesheet_width, frame_width):
                            frame = self.getFrame(x, y, frame_width, frame_height, scale)
                            frames.append(frame)
                            offsets.append((0, 0))  # Pas d'offset dans ce format

                    if frames:
                        self.animations[anim_name] = Animation(anim_name, frames, frame_duration, offsets, True, None)
                    else:
                        print(f"Aucune frame chargée pour l'animation {anim_name}.")

        except Exception as e:
            print(f"Erreur lors du chargement du fichier d'animations (nouveau format) : {e}")

    def addAnimationsFromFile(self, file: str):
        try:
            with open(file, "r") as f:
                data = json.load(f)
                for anim in data.get("animations", []):
                    name = anim["name"]
                    anim_sound = None
                    if anim.get("sound"):
                        try:
                            anim_sound = pygame.mixer.Sound(anim["sound"])
                        except Exception as e:
                            print(f"Erreur lors du chargement du son {anim['sound']} : {e}")

                    if "frames" in anim:
                        if anim.get("spritesheet"):
                            try:
                                self.spritesheet = pygame.image.load(anim["spritesheet"]).convert_alpha()
                            except Exception as e:
                                print(f"Erreur chargement spritesheet {anim['spritesheet']}: {e}")
                        self.addAnimation(
                            name,
                            anim["frames"],
                            anim_sound,
                            scale=anim.get("scale", 1.0),
                            frameRate=anim.get("frameRate", 60),
                            isCancelable=anim.get("isCancelable", True)
                        )

                    elif anim.get("spritesheet") and anim.get("frame_size"):
                        spritesheet_path = anim["spritesheet"]
                        frame_w, frame_h = anim["frame_size"]
                        try:
                            sheet = pygame.image.load(spritesheet_path).convert_alpha()
                        except Exception as e:
                            print(f"Erreur chargement spritesheet {spritesheet_path}: {e}")
                            continue

                        frames = []
                        offsets = []
                        sheet_w, sheet_h = sheet.get_size()
                        scale = anim.get("scale", 1.0)
                        for y in range(0, sheet_h, frame_h):
                            for x in range(0, sheet_w, frame_w):
                                img = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                                img.blit(sheet, (0, 0), (x, y, frame_w, frame_h))
                                if scale != 1.0:
                                    img = pygame.transform.scale(
                                        img,
                                        (int(frame_w * scale), int(frame_h * scale))
                                    )
                                frames.append(img)
                                offsets.append((0, 0))

                        if frames:
                            self.animations[name] = Animation(
                                name,
                                frames,
                                anim.get("frameRate", 90),
                                offsets,
                                anim.get("isCancelable", True),
                                anim_sound
                            )
                        else:
                            print(f"Aucune frame chargée pour {name} (sleeping).")

                    else:
                        print(f"Format inconnu pour l'animation {name}, ni 'frames' ni 'frame_size'.")
        except Exception as e:
            print(f"Erreur lors du chargement du fichier d'animations: {e}")



    def playAnimationSound(self):
        sound = self.getCurrentAnimation().sound
        if sound and ((self.current_animation=="run" and self.entity and self.entity.collisions.OnGround()) or self.current_animation!="run"):
            sound.play()

    def forceSetAnimation(self, animation_name: str):

        if animation_name in self.animations:
            self.current_animation = animation_name
            self.current_frame = 0
            self.accumulated_time = 0
            self.last_update = pygame.time.get_ticks()
            self.animation_count = 0
            # Bloque l'interruption si l'animation n'est pas annulable
            self.isAnimationAllowed = self.getCurrentAnimation().isCancelable
            self.playAnimationSound()

    def setAnimation(self, animation_name: str):

        if (animation_name in self.animations and
            animation_name != self.current_animation and
            self.isAnimationAllowed):
            self.current_animation = animation_name
            self.current_frame = 0
            self.accumulated_time = 0
            self.last_update = pygame.time.get_ticks()
            self.animation_count = 0
            # Bloque l'interruption si l'animation n'est pas annulable
            self.isAnimationAllowed = self.getCurrentAnimation().isCancelable
            self.playAnimationSound()

    def updateAnimation(self):
        current_anim = self.getCurrentAnimation()
        if not current_anim or len(current_anim.frames) == 0:
            return

        now = pygame.time.get_ticks()
        delta_time = now - self.last_update
        self.last_update = now

        self.accumulated_time += delta_time
        frame_duration = current_anim.frameRate

        # Avance de plusieurs frames si besoin (en cas de baisse de fps)
        frames_to_advance = self.accumulated_time // frame_duration
        if frames_to_advance > 0:
            self.accumulated_time %= frame_duration

            previous_frame = self.current_frame
            self.current_frame += frames_to_advance

            total_frames = previous_frame + frames_to_advance
            loops = total_frames // len(current_anim.frames)
            self.current_frame %= len(current_anim.frames)

            # Relance le son pour chaque boucle complète
            if loops>0:
                self.animation_count+=1
                if current_anim.sound:
                    current_anim.sound.stop()
                    current_anim.sound.play()

            # Si l'animation n'est pas annulable, autorise le changement uniquement une fois la dernière frame atteinte
            if not current_anim.isCancelable:
                if total_frames >= len(current_anim.frames) - 1:
                    self.isAnimationAllowed = True
            
        if self.flash_active:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.flash_start_time

            if elapsed >= self.flash_duration:
                self.flash_active = False


        # Protection supplémentaire : si on est à la dernière frame d'une animation non cancelable, débloque le changement
        if not current_anim.isCancelable and self.current_frame >= len(current_anim.frames) - 1:
            self.isAnimationAllowed = True
