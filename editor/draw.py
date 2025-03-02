import json
from typing import List
import pygame
from editor.ui import Button, ColorButton, ImageButton, Slider
from editor.DataManager import DataManager, Tile,Tools
from editor.TilePalette import TilePalette
from editor.viewport import ViewPort

class DrawManager:
    def __init__(self, screen: pygame.surface.Surface,actions):
        self.screen=screen
        self.viewport=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-45))
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
        self.loadAssets()

    def loadAssets(self):
        self.bar = pygame.image.load('./Assets/ui/travaux.png')
        self.bar = pygame.transform.scale(self.bar, (self.screen.get_width(), 17))
        self.font = pygame.font.Font(None, 26)
        self.layerText=self.font.render("Layer: 0", True, (255, 255, 255))
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
        self.load_buttons("./Assets/ui/ui.json")
        self.UpdateRect()


    def updateLayerText(self,layer):
        self.layerText=self.font.render(f"Layer: {layer}", True, (255, 255, 255))
    
    def updateMapText(self,map):
        if map:
            self.MapText=self.font.render(f"Map: {map.name}", True, (255, 255, 255))

    def load_buttons(self,json_file):
        with open(json_file, "r", encoding="utf-8") as file:
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
        self.drawSelectionPreview()
        
    def UpdateCollisionText(self):
        if self.dataManager.selectedElement:
            self.NameText=self.font.render(f"Name: {self.dataManager.selectedElement.name}", True, (255, 255, 255))
            self.TypeText=self.font.render(f"Type: {self.dataManager.selectedElement.type}", True, (255, 255, 255))
            self.ColorText=self.font.render("Color: ", True, (255, 255, 255))
            self.colorPick.color=self.dataManager.selectedElement.color
        else:
            self.NameText=self.font.render("", True, (255, 255, 255))
            self.TypeText=self.font.render("", True, (255, 255, 255))
            self.ColorText=self.font.render("", True, (255, 255, 255))

    def drawElements(self):
        if not self.viewportData.displayRect:
            return
        for CollisionRect in self.dataManager.collisionRects:
            CollisionRect.draw(self.screen,self.viewportData.panningOffset,self.viewportData.zoom,CollisionRect==self.dataManager.selectedElement)
        for locationPoint in self.dataManager.locationPoints:
            image=self.locationPointImage
            if locationPoint==self.dataManager.selectedElement:
                image=self.DottedlocationPointImage
            locationPoint.draw(self.screen,self.viewportData.panningOffset,self.viewportData.zoom,image)

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


    def drawTile(self,tile: Tile,alpha=None,overlay=False):
        tileMap=self.tilePaletteData.GetMapByName(tile.TileMap)
        rect = self.viewportData.GetTileRectFromRelative(tile.x,tile.y)
        # Extraire la portion d'image correspondant à la tile
        tile_rect = pygame.Rect(tile.Originalx * tileMap.tileSize,tile.Originaly * tileMap.tileSize,tileMap.tileSize,tileMap.tileSize)
        try:
            tile_surface = tileMap.image.subsurface(tile_rect).copy()
        except:
            return
        if tileMap.colorKey:
            tile_surface.set_colorkey(tileMap.colorKey)
        # Appliquer les transformations
        if tile.flipHorizontal or tile.flipVertical:
            tile_surface = pygame.transform.flip(tile_surface, tile.flipHorizontal, tile.flipVertical)
    
        # Appliquer la rotation si nécessaire
        if tile.rotation != 0:
            tile_surface = pygame.transform.rotate(tile_surface, tile.rotation)
            
        # Redimensionner la tile selon le zoom
        scaled = self.GetScaledTile(tile_surface)
        scaled.set_alpha(alpha)
        self.viewport.blit(scaled, rect)
        if overlay:
            overlay = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)  # Activer la transparence
            overlay.fill((255, 0, 0, 100)) 
            self.viewport.blit(overlay, rect)


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
        self.screen.fill(self.bg_color)
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

        for button in self.buttons:
            self.UpdateEyeButtons(button)
            if hasattr(button, "image_path") and "edit" in button.image_path:
                if self.dataManager.selectedElement:
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