from typing import List
import pygame
from editor.TilePalette import TilePalette
from editor.ui import Button

class FileOpener:
    def __init__(self, screen: pygame.surface.Surface,tilePalette: TilePalette,updateMainRect):
        self.screen = screen
        self.tilePalette=tilePalette
        self.updateMainRect=updateMainRect
        self.font = pygame.font.Font(None, 26)
        self.tilesmaps = []
        self.active_tilemap = None
        self.buttons: List[Button] = []
        self.editing=True
        self.pickingColor=False
        self.tileSize=None
        self.name=None
        self.image=None
        self.colorkey=None
        self.grid_cell_size=None
        self.filepath=None
        self.AddButtons()
        self.TextColor = self.font.render("Cliquez sur l'image pour choisir la ColorKey", True, (255, 255, 0))

    def getMapByName(self,name):
        for tilemap in self.tilesmaps:
            if tilemap.get("name")==name:
                return tilemap

    def AddButtons(self):
        self.buttons.append(Button((self.screen.get_width() - 110, self.screen.get_height() - 60, 100, 40),
                                   "Done", self.validate_tileMap, bg_color=(36, 43, 59),hover_color=(16, 152, 104), size=25))
        self.buttons.append(Button((self.screen.get_width() - 120, self.screen.get_height() - 60, 100, 40),
                                     "Cancel", self.cancel_editing, bg_color=(36, 43, 59),hover_color=(200, 0, 0), size=25))
        self.buttons.append(Button((self.screen.get_width() - 330, self.screen.get_height() - 60, 100, 40),
                                       "Set ColorKey", self.ColorPicker, bg_color=(36, 43, 59), size=25))

    def UpdateRect(self):
        self.buttons[0].rect=pygame.Rect(self.screen.get_width() - 110, self.screen.get_height() - 60, 100, 40)
        self.buttons[1].rect=pygame.Rect(self.screen.get_width() - 210, self.screen.get_height() - 60, 100, 40)
        self.buttons[2].rect=pygame.Rect(self.screen.get_width() - 330, self.screen.get_height() - 60, 100, 40)

    def ColorPicker(self):
        self.pickingColor=True

    def cancel_editing(self):
        self.editing = False
        print("Édition annulée.")

        
    def NewTileMapReset(self,name,tileSize):
        self.editing=True
        self.tileSize=tileSize
        self.name=name
        self.colorkey=None
        self.scale_image()
        infoText = f"Tile size: {self.tileSize}x{self.tileSize} pixels. Vérifiez la découpe."
        self.infoText = self.font.render(infoText, True, (255, 255, 255))

    def processTileMap(self,tileSize,name):
        self.UpdateRect()
        self.NewTileMapReset(name,tileSize)
        while self.editing:
            self.handleEvents()
            self.draw()
            pygame.display.flip()

    def scale_image(self):
        max_display_width = int(self.screen.get_width() * 0.8)
        max_display_height = int(self.screen.get_height() * 0.8)
        img_width = self.image.get_width()
        img_height = self.image.get_height()
        scale_factor = min(max_display_width / img_width, max_display_height / img_height)
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        self.image = pygame.transform.scale(self.image, (new_width, new_height))
        self.grid_cell_size = self.tileSize * scale_factor
        


    
    def draw(self):
        self.screen.fill((36, 43, 59))
        image_rect = self.image.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(self.image, image_rect)
        self.draw_grid(image_rect)
        self.screen.blit(self.infoText, (20, 20))
        if self.pickingColor:
            self.screen.blit(self.TextColor, (20, 50))
        for button in self.buttons:
            button.draw(self.screen)
    

    def draw_grid(self,image_rect):
        x = image_rect.left
        while x <= image_rect.right + 1:
            pygame.draw.line(self.screen, (255, 0, 0), (x, image_rect.top), (x, image_rect.bottom), 1)
            x += self.grid_cell_size
        y = image_rect.top
        while y <= image_rect.bottom:
            pygame.draw.line(self.screen, (255, 0, 0), (image_rect.left, y), (image_rect.right, y), 1)
            y += self.grid_cell_size

    def handleEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Operation Annulée")
                self.editing = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.pickingColor:
                    try:
                        self.colorkey=self.screen.get_at(event.pos)
                        self.image.set_colorkey(self.colorkey)
                        self.pickingColor=False
                    except:
                        print("impossible de récupérer la couleur")
            elif event.type == pygame.VIDEORESIZE:
                self.UpdateRect()
            for button in self.buttons:
                button.handle_event(event)

    
    def validate_tileMap(self):
        #image propre (non redimensionnée)
        self.image = pygame.image.load(self.filepath).convert_alpha()
        if self.colorkey:
            self.image.set_colorkey(self.colorkey)
        total_tiles = ((self.image.get_width()+1) // self.grid_cell_size) * ((self.image.get_height()+1) // self.grid_cell_size)
        self.tilePalette.AddMap(self.name,self.filepath,self.tileSize,self.image,self.colorkey)
        self.tilePalette.currentTileMap=len(self.tilePalette.Maps)-1
        print(f"Tile map '{self.name}' ajoutée avec {total_tiles} tiles.") #340
        self.editing=False
        self.updateMainRect()
       