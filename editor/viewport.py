
import pygame


class ViewPort():
    def __init__(self,screen,moveSensitivity,zoomSensitivity):
        self.screen=screen
        self.moveSensitivity=moveSensitivity
        self.zoomSensitivity=zoomSensitivity
        self.tileSize=16
        self.zoom=1.0
        self.panningOffset=[0,0]
        self.surface=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-45))
        self.rect = self.surface.get_rect()
        self.tilePaletteRect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210,230)
        self.screen_pos = (self.rect.x, self.rect.y)
        self.displayRect=True
        self.light_origin = None
        self.light_preview = False
        self.light_current=None

    def UpdateRect(self,SurfaceZoom):
        self.surface=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-45))
        self.rect = self.surface.get_rect()
        self.tilePaletteRect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210*SurfaceZoom,230*SurfaceZoom)
        self.tilePaletteRect.bottom=self.screen.get_height()-40
        self.tilePaletteRect.right=self.screen.get_width()-20

    def InRegion(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]-30) and not  self.tilePaletteRect.collidepoint(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1])

    def move(self,dx,dy):
        self.panningOffset[0]+=dx*self.moveSensitivity
        self.panningOffset[1]+=dy*self.moveSensitivity

    def hoveredTile(self):
        return self.toGrid(pygame.mouse.get_pos())

    def toGrid(self, screen_pos: tuple):
        # Utiliser la position d'affichage réelle du viewport
        viewport_x = screen_pos[0] - self.screen_pos[0]
        viewport_y = screen_pos[1] - self.screen_pos[1]
        relative_x = viewport_x - self.panningOffset[0]
        relative_y = viewport_y - self.panningOffset[1]
        grid_cell_size = self.tileSize * self.zoom
        grid_x = int(relative_x // grid_cell_size)
        grid_y = int(relative_y // grid_cell_size)
        return (grid_x, grid_y)

    
    def GetTileRectFromRelative(self,x,y):
        grid_cell_size = self.tileSize * self.zoom
        tile_content_x = self.panningOffset[0] + x * grid_cell_size
        tile_content_y = self.panningOffset[1] + y * grid_cell_size
        rect_x = self.rect.x + round(tile_content_x)
        rect_y = self.rect.y + round(tile_content_y)
        return pygame.Rect(rect_x, rect_y, grid_cell_size, grid_cell_size)

    def Zoom(self,zoom):
        self.zoom=round(max(self.zoom+zoom*self.zoomSensitivity,0.25),2)


    def toMapCoords(self, screen_pos: tuple):
        """
        Convertit une position écran en coordonnées de la carte
        (en pixels dans le référentiel original de la carte),
        en tenant compte du décalage et du zoom.
        """
        viewport_x = screen_pos[0] - self.screen_pos[0]
        viewport_y = screen_pos[1] - self.screen_pos[1]
        # Les coordonnées relatives à la carte (non arrondies)
        map_x = (viewport_x - self.panningOffset[0]) / self.zoom
        map_y = (viewport_y - self.panningOffset[1]) / self.zoom
        return (map_x, map_y)
