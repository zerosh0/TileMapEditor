import json
from pathlib import Path
import traceback
from typing import List
import pygame
from editor.Parallax import ParallaxBackground
from editor.Updater import UpdateAndCrashHandler
from editor.ui import Button, ColorButton, ImageButton, Slider
from editor.DataManager import DataManager, Tile,Tools
from editor.TilePalette import TilePalette
from editor.utils import Light
from editor.viewport import ViewPort

class DrawManager:
    def __init__(self, screen: pygame.surface.Surface,actions,update: UpdateAndCrashHandler):
        self.screen=screen
        self.viewport=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-45))
        self.light_mask = pygame.Surface((self.screen.get_width() - 250,self.screen.get_height()-45), flags=pygame.SRCALPHA)
        self.shadow_alpha=0
        self.light_mask.fill((0,0,0,self.shadow_alpha))
        self.viewportRect = self.viewport.get_rect()
        self.viewportRect.top = 30
        self.TilePalette=pygame.surface.Surface((210, 230))
        self.TilePaletteSurfaceZoom=1
        self.buttons: List[Button] = []
        self.bg_color = (200, 200, 200)
        self.actions=actions
        self.TilePreview=False
        self.PaletteSelectionPreview=False
        self.viewportSelectionPreview=False
        self.drawVGrid=True
        self.tile_cache = {}
        self.update=update
        self.parallax_bg: ParallaxBackground | None = None
        self.last_bg_index: int | None = None
        self.loadAssets()

    def loadAssets(self):
        self.bar = pygame.image.load('./Assets/ui/travaux.png')
        self.bar = pygame.transform.scale(self.bar, (self.screen.get_width(), 17))
        self.font = pygame.font.Font(None, 26)
        self.layerText=self.font.render("Layer: 0", True, (255, 255, 255))
        self.GlobalIllumination=self.font.render("Global Illumination", True, (255, 255, 255))
        self.MapText=self.font.render("Map:", True, (255, 255, 255))
        self.collisionsText=self.font.render("Références", True, (255, 255, 255))
        self.NameText=self.font.render("Name: ", True, (255, 255, 255))
        self.TypeText=self.font.render("Type: ", True, (255, 255, 255))
        self.ColorText=self.font.render("Color: ", True, (255, 255, 255))
        self.slider = Slider(rect=(self.screen.get_width() - 220, 70, 185, 13), 
                             min_value=0, max_value=1, initial_value=1,
                             progress_color=(198, 128, 93),bar_color=(159, 167, 198))
        self.colorPick=ColorButton(rect=(self.screen.get_width() - 70, 195, 40, 20),initial_color=(255, 0, 0),action=self.actions.get("editColor"))
        self.locationPointImage=pygame.image.load('./Assets/ui/LocationPoint.png')
        self.DottedlocationPointImage=pygame.image.load('./Assets/ui/DottedLocationPoint.png')
        self.load_buttons("./Asset/ui/ui.json")
        # === SETTINGS PANEL ===
        self.settings_bg_name = "default_bg"
        self.font_settings = pygame.font.Font(None, 24)

        # Flèches pour changer le background
        x0 = self.screen.get_width() - 240
        self.btn_bg_prev = ImageButton(rect=(x0, 60, 24, 24),
                                       image_path="./Assets/ui/icones/arrow_left.png",
                                       action=self.actions.get("bg_prev"))
        self.btn_bg_next = ImageButton(rect=(x0+210-20, 60, 24, 24),
                                       image_path="./Assets/ui/icones/arrow_right.png",
                                       action=self.actions.get("bg_next"))
        self.btn_close = ImageButton(
            rect=(0, 0, 24, 24),
            image_path="./Assets/ui/icones/close.png",
            action=self.actions.get("toggle_settings")
        )
        # Slider Global Illumination
        self.slider_gi = Slider(rect=(self.screen.get_width() - 230, 120, 200, 12),
                                min_value=0.0, max_value=1.0, initial_value=self.shadow_alpha/255,
                                progress_color=(198,128,93), bar_color=(159,167,198))
        # Boutons “Update Schedule”
        self.schedule_intervals = [
            ("Never", 0), ("30 min", 30), ("1 h", 60), ("On Start", -1)
        ]
        self.schedule_buttons = []
        # état interne
        self.current_schedule = 0  # par défaut "Never"
        
        sx = self.screen.get_width() - 230
        sy = 180
        for i, (label, interval) in enumerate(self.schedule_intervals):
            # on fait une closure capturant `interval`
            def make_action(val=interval):
                return lambda: self._set_schedule(val)
            btn = Button(rect=(sx + i*55, sy, 60, 25),
                         text=label,
                         action=make_action(),
                         bg_color=(36, 43, 59), size=20)
            self.schedule_buttons.append(btn)

        # Checkboxes pour lights, collisions, location points
        self.chk_labels = ["Lights", "Collisions", "Location points"]
        self.chk_states = [True, True, True]
        self.chk_buttons = []
        cx = self.screen.get_width() - 230
        cy = 220
        line_height = 40
        for i, label in enumerate(self.chk_labels):
            # petite case à cocher
            rect = (cx, cy + i * line_height, 20, 20)
            btn = Button(rect=rect, text="",
                         action=lambda idx=i: self._toggle_chk(idx),
                         bg_color=(50,50,50))
            self.chk_buttons.append(btn)

        self.icon_checked   = pygame.image.load("./Assets/ui/icones/checked.png").convert_alpha()
        self.icon_unchecked = pygame.image.load("./Assets/ui/icones/unchecked.png").convert_alpha()
        self.UpdateRect()



    def _set_schedule(self, interval_minutes):
        self.current_schedule = interval_minutes
        # si vous avez un callback externe pour appliquer ce choix :
        if "apply_schedule" in self.actions:
            self.actions["apply_schedule"](interval_minutes)

    def _toggle_chk(self, idx):
        self.chk_states[idx] = not self.chk_states[idx]
        # appliquer l’affichage dans ViewPort ou DataManager
        if idx == 0:
            self.viewportData.displayLights = self.chk_states[idx]
        elif idx == 1:
            self.dataManager.showCollisions = self.chk_states[idx]
        else:
            self.dataManager.showLocationPoints = self.chk_states[idx]

    def updateLayerText(self,layer):
        self.layerText=self.font.render(f"Layer: {layer}", True, (255, 255, 255))
    
    def updateMapText(self,map):
        if map:
            self.MapText=self.font.render(f"Map: {map.name}", True, (255, 255, 255))

    def load_buttons(self,json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                self.data = json.load(file)
        except Exception as e:
            error = traceback.format_exc()
            self.update.send_crash_alert(error)
            with open(Path.cwd() / "Assets" / "ui" / "ui.json", "r", encoding="utf-8") as file:
                self.data = json.load(file)

        for bouton in self.data:
            action = self.actions.get(bouton["action"], lambda: print(f"Action {bouton['action']} non définie"))
            if bouton["type"] == "Button":
                self.buttons.append(Button(bouton["rect"], bouton["text"], action,bg_color= bouton.get("bg_color", (255, 255, 255)),size=bouton.get("size", 20)))
            elif bouton["type"] == "ImageButton":
                bouton["rect"][0]=self.screen.get_width()-bouton["rect"][0]-1000
                self.buttons.append(ImageButton(bouton["rect"], bouton["image"], action,hover_image_path=bouton.get("hover_image")))

    def draw(self,viewport: ViewPort,dataManager: DataManager,tilePalette: TilePalette):
        self.tilePaletteData=tilePalette
        self.activeTileMap=self.tilePaletteData.GetCurrentTileMap()
        self.viewportData=viewport
        self.dataManager=dataManager
        self.viewportData.screen_pos = (self.viewportRect.x, self.viewportRect.y)
        self.updateMapText(self.tilePaletteData.GetCurrentTileMap())
        self.UpdateCollisionText()
        self.drawViewport()
        self.drawViewportGrid()
        self.drawTilePreview()
        self.drawMainUI()
        self.drawTilePalette()
        self.drawSettings()
        self.drawSelectionPreview()
        self.drawLight()
        self.update.display_update_notification()

    def drawSettings(self):
        if self.dataManager.show_settings:
            panel_rect = (self.screen.get_width() - 250, 0, 250, self.screen.get_height()-40)
            pygame.draw.rect(self.screen, (36, 43, 59), panel_rect)

            # — Fond de niveau —
            # Label centré
            title_surf = self.font_settings.render("Background:", True, (255,255,255))
            tx = panel_rect[0] + (panel_rect[2] - title_surf.get_width())//2
            self.screen.blit(title_surf, (tx, 30))

            # Nom du bg
            bg = self.dataManager.get_current_background()
            name = bg["name"] if bg else "None"
            name_surf = self.font_settings.render(name, True, (200,200,200))
            nx = panel_rect[0] + (panel_rect[2] - name_surf.get_width())//2
            self.screen.blit(name_surf, (nx, 65))

            # Flèches
            self.btn_bg_prev.draw(self.screen)
            self.btn_bg_next.draw(self.screen)

            # — Global Illumination —
            gi_label = self.font_settings.render("Global Illumination", True, (255,255,255))
            self.screen.blit(gi_label, (panel_rect[0]+10, 90))
            self.slider_gi.draw(self.screen)
            # appliquer la valeur au shadow_alpha
            self.shadow_alpha = int(self.slider_gi.value * 255)

            # — Update Schedule —
            sched_label = self.font_settings.render("Update Schedule", True, (255,255,255))
            self.screen.blit(sched_label, (panel_rect[0]+10, 150))
            for i, btn in enumerate(self.schedule_buttons):
                # on compare à l’état interne
                if self.current_schedule == self.schedule_intervals[i][1]:
                    btn.bg_color = (159, 167, 198)
                else:
                    btn.bg_color = (36, 43, 59)
                btn.draw(self.screen)

            # — Checkboxes —
            for i, label in enumerate(self.chk_labels):
                btn = self.chk_buttons[i]
                # choisir l'icône
                icon = self.icon_checked if self.chk_states[i] else self.icon_unchecked
                # dessiner l'icône
                self.screen.blit(icon, btn.rect.topleft)
                # texte à droite, vertical centré
                lbl_surf = self.font_settings.render(label, True, (255,255,255))
                text_x = btn.rect.right + 8
                text_y = btn.rect.y + (btn.rect.height - lbl_surf.get_height()) // 2+3
                self.screen.blit(lbl_surf, (text_x, text_y))
            self.btn_close.draw(self.screen)



    def drawLight(self):
        if self.viewportData.light_preview and self.viewportData.light_origin:
            ox, oy = self.viewportData.light_origin
            cx, cy = self.viewportData.light_current
            radius = int(((cx-ox)**2 + (cy-oy)**2)**0.5)
            pygame.draw.circle(self.screen, (255, 255, 0), (ox, oy), radius, 2)
        
    def UpdateCollisionText(self):
        if self.dataManager.selectedElement:
            if not isinstance(self.dataManager.selectedElement,Light):
                self.NameText=self.font.render(f"Name: {self.dataManager.selectedElement.name}", True, (255, 255, 255))
                self.TypeText=self.font.render(f"Type: {self.dataManager.selectedElement.type}", True, (255, 255, 255))
            else:
                self.TypeText=self.font.render(f"Blink", True, (255, 255, 255))
                self.NameText=self.font.render(f"Radius: {round(self.dataManager.selectedElement.radius,1)}", True, (255, 255, 255))
            self.ColorText=self.font.render("Color: ", True, (255, 255, 255))
            self.colorPick.color=self.dataManager.selectedElement.color
        else:
            self.NameText=self.font.render("", True, (255, 255, 255))
            self.TypeText=self.font.render("", True, (255, 255, 255))
            self.ColorText=self.font.render("", True, (255, 255, 255))

    def drawElements(self):
        if not self.viewportData.displayRect:
            return
        if self.chk_states[1]:
            for CollisionRect in self.dataManager.collisionRects:
                CollisionRect.draw(self.screen,self.viewportData.panningOffset,self.viewportData.zoom,CollisionRect==self.dataManager.selectedElement)
        if self.chk_states[2]:
            for locationPoint in self.dataManager.locationPoints:
                image=self.locationPointImage
                if locationPoint==self.dataManager.selectedElement:
                    image=self.DottedlocationPointImage
                locationPoint.draw(self.screen,self.viewportData.panningOffset,self.viewportData.zoom,image)
        self.light_mask = pygame.Surface((self.screen.get_width() - 250,self.screen.get_height()-45), flags=pygame.SRCALPHA)
        self.light_mask.fill((0,0,0,self.shadow_alpha))
        if self.chk_states[0]:
            for light in self.dataManager.lights:
                light.draw(self.screen,self.light_mask,self.shadow_alpha,self.viewportData.panningOffset,self.viewportData.zoom,light==self.dataManager.selectedElement)
        self.screen.blit(self.light_mask, (0,30))


    def drawSelectionPreview(self):
        if self.PaletteSelectionPreview and self.dataManager.selectionPalette:
            x1, y1 = self.dataManager.selectionPalette[0]
            x2, y2 = self.dataManager.selectionPalette[1]
            pygame.draw.rect(self.screen, (0,200,0), (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)), 2)
        if self.viewportSelectionPreview and self.dataManager.selectionViewPort:
            x1, y1 = self.dataManager.selectionViewPort[0]
            x2, y2 = self.dataManager.selectionViewPort[1]
            pygame.draw.rect(self.screen, (0,200,0), (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)), 2)

    def drawTilePreview(self):
        if self.TilePreview:
            if self.dataManager.currentTool==Tools.Draw:
                for tile in self.dataManager.currentTiles:
                    self.drawTile(tile,128)
            elif self.dataManager.currentTool==Tools.Rubber:
                self.drawRubberTile()


    def drawViewport(self):
        if not self.activeTileMap:
            return
        # === fond parallax ou couleur
        bg_def = self.dataManager.get_current_background()
        idx   = self.dataManager.current_bg_index

        if bg_def and bg_def["type"] == "image":
            layers = [(ly["path"], ly["parallax"]) for ly in bg_def["layers"]]
            if self.parallax_bg is None or self.last_bg_index != idx:
                self.parallax_bg = ParallaxBackground(
                    surface=self.viewport,
                    viewport_data=self.viewportData,
                    layers=layers,
                    bg_color=bg_def["bg_color"]
                )
                self.last_bg_index = idx
            else:
                self.parallax_bg.surface = self.viewport
                self.parallax_bg.viewport_data = self.viewportData
            self.parallax_bg.render()

        elif bg_def and bg_def["type"] == "color":
            self.viewport.fill(tuple(bg_def["color"]))
        else:
            self.viewport.fill(self.bg_color)

        for layer in self.dataManager.layers:
            for tile in layer.tiles:
                self.drawTile(tile,alpha=int(layer.opacity * 255))

    def drawRubberTile(self):
        x,y=self.viewportData.toGrid(pygame.mouse.get_pos())
        rect = self.viewportData.GetTileRectFromRelative(x,y)
        overlay = pygame.Surface((rect.width,rect.height), pygame.SRCALPHA)  # Activer la transparence
        overlay.fill((255, 0, 0, 100)) 
        self.viewport.blit(overlay, rect)


    def drawTile(self, tile: Tile, alpha=None, overlay=False):
        tileMap = self.tilePaletteData.GetMapByName(tile.TileMap)
        rect = self.viewportData.GetTileRectFromRelative(tile.x, tile.y)

        if not rect.colliderect(self.viewportData.rect):
            return

        key = (
            tile.TileMap,
            tile.Originalx,
            tile.Originaly,
            tile.flipHorizontal,
            tile.flipVertical,
            tile.rotation,
            alpha
        )

        if key in self.tile_cache:
            tile_surface = self.tile_cache[key]
        else:
            tile_rect = pygame.Rect(
                tile.Originalx * tileMap.tileSize,
                tile.Originaly * tileMap.tileSize,
                tileMap.tileSize,
                tileMap.tileSize
            )
            try:
                tile_surface = tileMap.image.subsurface(tile_rect).copy()
            except:
                return

            if tileMap.colorKey:
                tile_surface.set_colorkey(tileMap.colorKey)

            if tile.flipHorizontal or tile.flipVertical:
                tile_surface = pygame.transform.flip(tile_surface, tile.flipHorizontal, tile.flipVertical)

            if tile.rotation != 0:
                tile_surface = pygame.transform.rotate(tile_surface, tile.rotation)

            tile_surface = self.GetScaledTile(tile_surface)
            tile_surface.set_alpha(alpha)

            # Stocker dans le cache
            self.tile_cache[key] = tile_surface

        self.viewport.blit(tile_surface, rect)

        if overlay:
            overlay_surface = pygame.Surface(tile_surface.get_size(), pygame.SRCALPHA)
            overlay_surface.fill((255, 0, 0, 100))
            self.viewport.blit(overlay_surface, rect)




    def GetScaledTile(self,surface):
        grid_cell_size = self.viewportData.tileSize * self.viewportData.zoom
        surface = pygame.transform.scale(surface, (grid_cell_size, grid_cell_size))
        return surface


    def drawViewportGrid(self):
        if not (self.activeTileMap and self.drawVGrid):
            return

        grid_cell_size = self.viewportData.tileSize * self.viewportData.zoom
        residual_x = -1*self.viewportData.panningOffset[0] % grid_cell_size
        x = self.viewportRect.left - residual_x
        while x <= self.viewportRect.right:
            pygame.draw.line(self.viewport, (145, 145, 145), (x, self.viewportRect.top-30), (x, self.viewportRect.bottom), 1)
            x += grid_cell_size
        residual_y = -1*self.viewportData.panningOffset[1] % grid_cell_size
        y = self.viewportRect.top - residual_y-30
        while y <= self.viewportRect.bottom:
            pygame.draw.line(self.viewport, (145, 145, 145), (self.viewportRect.left, y), (self.viewportRect.right, y), 1)
            y += grid_cell_size



    def drawTilePalette(self):
        if not self.activeTileMap:
            return
        self.TilePalette.fill((50, 58, 81))
        self.TilePalette.blit(self.activeTileMap.zoomedImage,self.tilePaletteData.panningOffset)
        self.drawPalettegrid()
        self.screen.blit(self.TilePalette,self.TilePaletteRect)
        
    def UpdateRect(self):
        self.TilePaletteRect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210*self.TilePaletteSurfaceZoom,230*self.TilePaletteSurfaceZoom)
        self.TilePalette=pygame.surface.Surface((210*self.TilePaletteSurfaceZoom, 230*self.TilePaletteSurfaceZoom))
        self.TilePaletteRect.bottom=self.screen.get_height()-40
        self.TilePaletteRect.right=self.screen.get_width()-20
        self.palette_area_rect = pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270, 210, 230)
        self.bar = pygame.image.load('./Assets/ui/travaux.png')
        self.bar = pygame.transform.scale(self.bar, (self.screen.get_width(), 17))
        self.barRect=self.bar.get_rect()
        self.barRect.centerx = self.screen.get_width() // 2
        self.barRect.bottom = self.screen.get_height()
        self.slider.rect=pygame.Rect(self.screen.get_width() - 220, 70, 185, 13)
        self.viewport=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-45))
        self.viewportRect = self.viewport.get_rect()
        self.viewportRect.top = 30
        self.colorPick.rect=pygame.Rect(self.screen.get_width() - 70, 195, 40, 20)
        for i,bouton in enumerate(self.data):
                if bouton["type"] == "ImageButton":
                    self.buttons[i].rect.x=self.screen.get_width()-bouton["rect"][0]-1000
        sw, sh = self.screen.get_size()
        panel_x = sw - 250
        panel_w = 250
        cx = panel_x + panel_w - 8 - self.btn_close.rect.width
        cy = 8
        self.btn_close.rect.topleft = (cx, cy)
          # Flèches Background
        x0 = panel_x + 20
        y0 = 60
        self.btn_bg_prev.rect.topleft = (x0, y0)
        self.btn_bg_next.rect.topleft = (x0 + panel_w - 20 - self.btn_bg_next.rect.width, y0)

        # Slider GI
        self.slider_gi.rect.topleft = (panel_x + 20, 120)

        # Schedule buttons
        sx = panel_x + 5
        sy = 180
        for i, btn in enumerate(self.schedule_buttons):
            btn.rect.topleft = (sx + i * (btn.rect.width), sy)

        # Checkboxes
        cx = panel_x + 20
        cy = 220
        line_height = 40
        for i, btn in enumerate(self.chk_buttons):
            btn.rect.topleft = (cx, cy + i * line_height)


    def drawPalettegrid(self):
        image_rect = self.activeTileMap.zoomedImage.get_rect()
        offset = self.tilePaletteData.panningOffset
        grid_cell_size = self.activeTileMap.tileSize * self.tilePaletteData.zoom
        x = image_rect.left + offset[0]
        while x <= image_rect.right + offset[0]+1:
            pygame.draw.line(self.TilePalette,(255, 0, 0),(x, image_rect.top + offset[1]),(x, image_rect.bottom + offset[1]),1)
            x += grid_cell_size
        y = image_rect.top + offset[1]
        while y <= image_rect.bottom + offset[1]+1:
            pygame.draw.line(self.TilePalette,(255, 0, 0),(image_rect.left + offset[0], y),(image_rect.right + offset[0], y),1)
            y += grid_cell_size

    def drawMainUI(self):
        self.screen.fill((200,200,200))
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        if self.activeTileMap:
            self.screen.blit(self.viewport,self.viewportRect)
            self.drawElements()
        # Interface latérale
        pygame.draw.rect(self.screen, (36, 43, 59), (screen_width - 250, 0, 250, screen_height))
        pygame.draw.rect(self.screen, (50, 58, 81), (screen_width - 230, 30, 210, 200), border_radius=3)
        pygame.draw.rect(self.screen, (107, 114, 150), (screen_width - 230, 250, 210, 140), border_radius=3)
        pygame.draw.rect(self.screen, (50, 58, 81), self.palette_area_rect, border_radius=3)
        pygame.draw.rect(self.screen, (36, 43, 59), (0, 0, screen_width - 250, 30))
        self.screen.blit(self.layerText,(screen_width - 220,40))
        self.screen.blit(self.MapText,(screen_width - 230,400))
        self.screen.blit(self.collisionsText,(screen_width - 220, 95))
        self.screen.blit(self.TypeText,(screen_width - 220, 125))
        self.screen.blit(self.NameText,(screen_width - 220, 160))
        self.screen.blit(self.ColorText,(screen_width - 220, 195))
        self.screen.blit(self.bar, self.barRect)
        edit=0
        for button in self.buttons:
            self.UpdateEyeButtons(button)
            if hasattr(button, "image_path") and "edit" in button.image_path:
                if self.dataManager.selectedElement:
                    edit+=1
                    if isinstance(self.dataManager.selectedElement,Light) and edit==1:
                        if self.dataManager.selectedElement.blink:
                            button.init_image("./Assets/ui/icones/checked.png")
                        else:
                            button.init_image("./Assets/ui/icones/unchecked.png")
                        button.draw(self.screen)
                        button.init_image("./Assets/ui/icones/edit.png")
                    else:
                        button.draw(self.screen)
            else:
                button.draw(self.screen)
        self.slider.draw(self.screen)
        if self.dataManager.selectedElement:
            self.colorPick.draw(self.screen)

        
    
    def UpdateEyeButtons(self,button):
        if hasattr(button, "image_path") and isinstance(button.image_path, str) and "eyes" in button.image_path:
                button.image_path="./Assets/ui/icones/eyesopen.png" if self.viewportData.displayRect else "./Assets/ui/icones/eyesclose.png"
                button.image=button._load_image(button.image_path)
                button.hover_image=button._create_hover_image(button.image)