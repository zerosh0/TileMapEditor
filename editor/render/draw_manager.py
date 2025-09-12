import json
from pathlib import Path
import traceback
from typing import List
import pygame
from editor.animations.animation import AnimationManager
from editor.game_engine.game_manager import Game
from editor.render.parallax import ParallaxBackground
from editor.services.update_handler import UpdateAndCrashHandler
from editor.ui.CheckBox import Checkbox
from editor.ui.ColorButton import ColorButton
from editor.ui.DropDownMenu import MenuButton
from editor.ui.Font import FontManager
from editor.ui.ImageButton import ImageButton
from editor.ui.Notifications import NotificationManager
from editor.core.settings import SettingsManager
from editor.core.data_manager import DataManager, Tile,Tools
from editor.render.tile_palette import TilePalette
from editor.ui.Slider import Slider
from editor.ui.TextButton import Button
from editor.core.utils import CollisionRect, Light
from editor.render.viewport import ViewPort

class DrawManager:
    def __init__(self, screen: pygame.surface.Surface,update: UpdateAndCrashHandler,nm : NotificationManager,settings : SettingsManager):
        self.screen=screen
        self.viewport=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-30))
        self.light_mask = pygame.Surface((self.screen.get_width() - 250,self.screen.get_height()-30), flags=pygame.SRCALPHA)
        self.shadow_alpha=0
        self.light_mask.fill((0,0,0,self.shadow_alpha))
        self.viewportRect = self.viewport.get_rect()
        self.viewportRect.top = 30
        self.TilePalette=pygame.surface.Surface((210, 230))
        self.TilePaletteSurfaceZoom=1
        self.buttons: List[Button] = []
        self.bg_color = (200, 200, 200)
        self.TilePreview=False
        self.PaletteSelectionPreview=False
        self.viewportSelectionPreview=False
        self.tile_cache = {}
        self.update=update
        self.nm=nm
        self.settings=settings
        self.parallax_bg: ParallaxBackground | None = None
        self.last_bg_index: int | None = None
        self.fps=-1
        self.font_manager = FontManager()
        self.fps_font   = self.font_manager.get(size=18)
        self.fps_color  = (255, 255, 255)
        self.fps_margin = 10
        self.macOsBlendingProblem = False #Si viewport noir lors de la pose de tuile

    def loadAssets(self,actions):
        self.actions=actions
        self.bar = pygame.image.load('./Assets/ui/travaux.png')
        self.bar = pygame.transform.scale(self.bar, (self.screen.get_width(), 17))
        self.font = self.font_manager.get(size=26)
        self.layerText=self.font.render("Layer: 0", True, (255, 255, 255))
        self.GlobalIllumination=self.font.render("Global Illumination", True, (255, 255, 255))
        self.MapText=self.font.render("Map:", True, (255, 255, 255))
        self.collisionsText=self.font.render("Références", True, (255, 255, 255))
        self.NameText=self.font.render("Name: ", True, (255, 255, 255))
        self.TypeText=self.font.render("Type: ", True, (255, 255, 255))
        self.ColorText=self.font.render("Color: ", True, (255, 255, 255))
        self.slider = Slider(rect=(self.screen.get_width() - 220, 70, 185, 13), 
                             min_value=0, max_value=1, initial_value=1,
                             progress_color=(109, 132, 165),bar_color=(83, 89, 98))
        self.playButton=Checkbox(rect=(450, 0, 89, 29),checked_image_path="./Assets/ui/icones/stop.png",unchecked_image_path="./Assets/ui/icones/play.png",action=self.actions.get("play"))
        self.colorPick=ColorButton(rect=(self.screen.get_width() - 70, 195, 40, 20),initial_color=(255, 0, 0),action=self.actions.get("editColor"))
        self.locationPointImage=pygame.image.load('./Assets/ui/LocationPoint.png')
        self.locationPointImageFlag=pygame.image.load('./Assets/ui/LocationPoint_flag.png')
        self.DottedlocationPointImage=pygame.image.load('./Assets/ui/DottedLocationPoint.png')
        self.DottedlocationPointImageFlag=pygame.image.load('./Assets/ui/DottedLocationPoint_flag.png')
        self.load_buttons("./Asset/ui/ui.json")
        self.UpdateRect()


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
                action = self.actions.get(bouton.get("action", ""), lambda: print(f"Action {bouton.get('action')} non définie"))

                if bouton["type"] == "Button":
                    self.buttons.append(
                        Button(
                            bouton["rect"],
                            bouton["text"],
                            action,
                            bg_color=bouton.get("bg_color", (255, 255, 255)),
                            size=bouton.get("size", 20)
                        )
                    )

                elif bouton["type"] == "ImageButton":
                    bouton["rect"][0] = -bouton["rect"][0]
                    self.buttons.append(
                        ImageButton(
                            bouton["rect"],
                            bouton["image"],
                            action,
                            hover_image_path=bouton.get("hover_image"),
                            tint_color=(109, 132, 165)
                        )
                    )
                    self.buttons[-1].action_name=bouton.get("action", "")

                elif bouton["type"] == "Dropdown":
                    submenu_items = []
                    for item in bouton.get("items", []):
                        item_action = self.actions.get(item["action"], lambda: print(f"Action {item['action']} non définie"))
                        submenu_items.append((item["text"], item_action))

                    self.buttons.append(
                        MenuButton(
                            rect=tuple(bouton["rect"]),
                            text=bouton["text"],
                            submenu_items=submenu_items,
                            font=self.font,
                            bg_color=bouton.get("bg_color", (255, 255, 255))
                        )
                    )

    def draw(self,viewport: ViewPort,dataManager: DataManager,tilePalette: TilePalette,animation: AnimationManager,clock,game_engine : Game):
        self.game_engine=game_engine
        self.tilePaletteData=tilePalette
        self.activeTileMap=self.tilePaletteData.GetCurrentTileMap()
        self.viewportData=viewport
        self.dataManager=dataManager
        self.viewportData.screen_pos = (self.viewportRect.x, self.viewportRect.y)
        self.animation=animation
        self.shadow_alpha=self.settings.global_illum*255
        self.drawn=0
        self.fps=clock.get_fps()
        self.updateMapText(self.tilePaletteData.GetCurrentTileMap())
        self.UpdateCollisionText()
        self.drawViewport()
        self.drawViewportGrid()
        self.drawTilePreview()
        self.drawMainUI()
        self.drawLight()
        if not self.game_engine.running:
            self.animation.draw()
        self.drawTilePalette()
        self.drawSelectionPreview()
        if self.dataManager.selectedElement and not self.animation.panel_visible:
            self.colorPick.draw(self.screen)
        self.settings.draw()
        self.drawFps()
        self.update.display_update_notification(self.nm)


    def drawFps(self):
        if self.settings.fps:
            fps_surf = self.fps_font.render(f"{self.fps:.0f} FPS", True, self.fps_color)
            self.screen.blit(fps_surf, (self.screen.get_width() - fps_surf.get_width() - 20, self.fps_margin))
        if self.settings.drawn:
            drawn_surf = self.fps_font.render(f"{self.drawn} tiles", True, self.fps_color)
            self.screen.blit(drawn_surf, (self.screen.get_width() - drawn_surf.get_width() - 180, self.fps_margin))

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
        if not self.viewportData.displayRect or self.game_engine.running:
            return

        viewport_rect = pygame.Rect(0, 30, self.viewport.get_width(), self.viewport.get_height())

        if self.settings.show_collisions:
            for collision in self.dataManager.collisionRects:
                screen_rect = collision.get_screen_rect(self.viewportData.panningOffset, self.viewportData.zoom)
                if viewport_rect.colliderect(screen_rect):
                    collision.draw(self.screen, self.viewportData.panningOffset, self.viewportData.zoom,
                                collision == self.dataManager.selectedElement)

        if self.settings.show_location_points:
            for lp in self.dataManager.locationPoints:
                image = self.locationPointImageFlag if lp.name == self.settings.player_spawn_point else self.locationPointImage
                if lp == self.dataManager.selectedElement:
                    image = self.DottedlocationPointImageFlag if lp.name == self.settings.player_spawn_point else self.DottedlocationPointImage
                screen_rect = lp.get_screen_rect(self.viewportData.panningOffset, self.viewportData.zoom, image)
                if viewport_rect.colliderect(screen_rect):
                    lp.draw(self.screen, self.viewportData.panningOffset, self.viewportData.zoom, image)

        if self.settings.display_lights:
            self.light_mask = pygame.Surface((self.screen.get_width() - 250, self.screen.get_height() - 30), flags=pygame.SRCALPHA)
            self.light_mask.fill((0, 0, 0, self.shadow_alpha))
            for light in self.dataManager.lights:
                cx, cy = light.get_screen_pos(self.viewportData.panningOffset, self.viewportData.zoom)
                radius_px = int(light.radius * self.viewportData.zoom)
                light_rect = pygame.Rect(cx - radius_px, cy - radius_px, 2 * radius_px, 2 * radius_px)
                if viewport_rect.colliderect(light_rect):
                    light.draw(self.screen, self.light_mask, self.shadow_alpha, self.viewportData.panningOffset,
                            self.viewportData.zoom,
                            light == self.dataManager.selectedElement and not self.colorPick.picker_visible)
            self.screen.blit(self.light_mask, (0, 30))




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
        if self.TilePreview and not self.game_engine.running:
            if self.dataManager.currentTool==Tools.Draw:
                for tile in self.dataManager.currentTiles:
                    self.drawTile(tile,128)
            elif self.dataManager.currentTool==Tools.Rubber:
                self.drawRubberTile()


    def drawViewport(self):
        if not self.activeTileMap:
            return
        if self.game_engine.running:
            self.game_engine.draw(self.viewport)
            return
        # === fond parallax ou couleur ===
        bg_def = self.dataManager.get_current_background()
        idx   = self.dataManager.settings.parallax_index

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

        anim_states = self.animation.get_current_states()
        current_coords = {(t.x, t.y) for t in self.dataManager.currentTiles}
        for layer_index, layer in enumerate(self.dataManager.layers):
            for tile in layer.tiles:
                self.drawTile(tile, alpha=int(layer.opacity * 255))

            for anim_name, anim_data in anim_states.items():
                for anim_id, frame_dict in anim_data.items():
                    for (x, y, lay), anim_tile in frame_dict.items():
                        if lay == layer_index:
                            if anim_tile.tile.TileMap == "":
                                continue
                            if (self.settings.keyframe_overlay
                                    and not self.animation.get_current_anim().timeline.record
                                    and self.dataManager.currentTiles
                                    and (x, y) in current_coords and self.dataManager.currentTool==Tools.Draw):
                                    self.drawTile(anim_tile.tile,
                                                alpha=int(layer.opacity * 255),
                                                overlay_yellow=True)
                            else:
                                self.drawTile(
                                    anim_tile.tile,
                                    alpha=int(layer.opacity * 255),
                                    overlay_cyan=self.animation.animations[anim_name].display_keyframes
                                )



    def drawRubberTile(self):
        x,y=self.viewportData.toGrid(pygame.mouse.get_pos())
        rect = self.viewportData.GetTileRectFromRelative(x,y)
        overlay = pygame.Surface((rect.width,rect.height), pygame.SRCALPHA)  # Activer la transparence
        overlay.fill((255, 0, 0, 100)) 
        self.viewport.blit(overlay, rect)


    def drawTile(self, tile: Tile, alpha=None, overlay=False, overlay_cyan=False,overlay_yellow=False):
        tileMap = self.tilePaletteData.GetMapByName(tile.TileMap)
        rect = self.viewportData.GetTileRectFromRelative(tile.x, tile.y)


        if not rect.colliderect(self.viewportData.rect):
            return
        self.drawn+=1
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
            if alpha!=255:
                tile_surface.set_alpha(alpha)
            elif self.macOsBlendingProblem:
                tile_surface.set_alpha(254)

            # Stocker dans le cache
            self.tile_cache[key] = tile_surface
        self.viewport.blit(tile_surface, rect)

        if overlay:
            overlay_surface = pygame.Surface(tile_surface.get_size(), pygame.SRCALPHA)
            overlay_surface.fill((255, 0, 0, 100))
            self.viewport.blit(overlay_surface, rect)
        elif overlay_yellow:
            overlay_surface = pygame.Surface(tile_surface.get_size(), pygame.SRCALPHA)
            overlay_surface.fill((241, 241, 77,150))
            self.viewport.blit(overlay_surface, rect)            
        elif overlay_cyan:
            overlay_surface = pygame.Surface(tile_surface.get_size(), pygame.SRCALPHA)
            overlay_surface.fill((0, 255, 255, 60))
            self.viewport.blit(overlay_surface, rect)




    def GetScaledTile(self,surface):
        grid_cell_size = self.viewportData.tileSize * self.viewportData.zoom
        surface = pygame.transform.scale(surface, (grid_cell_size, grid_cell_size))
        return surface


    def drawViewportGrid(self):
        if not (self.activeTileMap and self.settings.is_grid_visible) or self.game_engine.running:
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
        self.viewport=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-30))
        self.viewportRect = self.viewport.get_rect()
        self.viewportRect.top = 30
        self.colorPick.rect=pygame.Rect(self.screen.get_width() - 70, 195, 40, 20)
        self.playButton.rect.x=450/1000*self.screen.get_width()
        for i,bouton in enumerate(self.data):
                if bouton["type"] == "ImageButton":
                    self.buttons[i].rect.x=self.screen.get_width()-bouton["rect"][0]-1000
                    if "play" in bouton["image"]:
                        self.buttons[i].rect.x=self.screen.get_width()/2-bouton["rect"][2]/2


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
        pygame.draw.rect(self.screen, (36, 36, 36), (screen_width - 250, 0, 250, screen_height))
        pygame.draw.rect(self.screen, (47, 47, 47), (screen_width - 230, 30, 210, 200), border_radius=3)
        pygame.draw.rect(self.screen, (47, 47, 47), (screen_width - 230, 250, 210, 140), border_radius=3)
        pygame.draw.rect(self.screen, (26, 26, 26), self.palette_area_rect, border_radius=3)
        pygame.draw.rect(self.screen, (36, 36, 36), (0, 0, screen_width - 250, 30))
        self.screen.blit(self.layerText,(screen_width - 220,40))
        self.screen.blit(self.MapText,(screen_width - 230,400))
        self.screen.blit(self.collisionsText,(screen_width - 220, 95))
        self.screen.blit(self.TypeText,(screen_width - 220, 125))
        self.screen.blit(self.NameText,(screen_width - 220, 160))
        self.screen.blit(self.ColorText,(screen_width - 220, 195))
        #self.screen.blit(self.bar, self.barRect)
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
            elif hasattr(button, "image_path") and self.dataManager.currentTool and button.action_name==self.dataManager.currentTool._value_:
                button.draw(self.screen,is_tinted=True)
            elif hasattr(button, "image_path") and "graph" in button.image_path:
                if isinstance(self.dataManager.selectedElement,CollisionRect):
                    button.draw(self.screen)
            else:
                button.draw(self.screen)
        self.slider.draw(self.screen)
        self.playButton.draw(self.screen)



        
    
    def UpdateEyeButtons(self,button):
        if hasattr(button, "image_path") and isinstance(button.image_path, str) and "eyes" in button.image_path:
                button.image_path="./Assets/ui/icones/eyesopen.png" if self.viewportData.displayRect else "./Assets/ui/icones/eyesclose.png"
                button.image=button._load_image(button.image_path)
                button.hover_image=button._create_hover_image(button.image)