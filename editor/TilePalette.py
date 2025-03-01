import pygame
from editor.utils import List,TileMap

class TilePalette():
    def __init__(self,screen,moveSensitivity,zoomSensitivity):
        self.screen=screen
        self.moveSensitivity=moveSensitivity
        self.zoomSensitivity=zoomSensitivity
        self.currentTileMap=0
        self.Maps: List[TileMap]=[]
        self.zoom=1.0
        self.panningOffset=[0,0]
        self.surface=pygame.surface.Surface((210, 230))
        self.rect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210,230)
    
    def UpdateRect(self,SurfaceZoom):
        self.rect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210*SurfaceZoom,230*SurfaceZoom)
        self.surface=pygame.surface.Surface((210*SurfaceZoom, 230*SurfaceZoom))
        self.rect.bottom=self.screen.get_height()-40
        self.rect.right=self.screen.get_width()-20

    def changeCurrentTileMap(self, change: int):
        # Sauvegarde des paramètres actuels de la map
        if len(self.Maps)>1:
            current_map = self.GetCurrentTileMap()
            current_map.zoom = self.zoom
            current_map.panningOffset = self.panningOffset.copy()

            # Changement de tilemap
            self.currentTileMap = (self.currentTileMap + change) % len(self.Maps)
            
            # Récupère les paramètres de la nouvelle map
            new_map = self.GetCurrentTileMap()
            self.zoom = new_map.zoom
            self.panningOffset = new_map.panningOffset.copy()
            self.UpdateZoom()

    def GetMapByName(self,name):
        for map in self.Maps:
            if map.name==name:
                return map

    def AddMap(self,name,filepath,tileSize,image,colorKey):
        self.Maps.append(TileMap(name,filepath,tileSize,image,colorKey,image))

    def GetCurrentTileMap(self):
        if len(self.Maps)>self.currentTileMap:
            return self.Maps[self.currentTileMap]
        return None

    def InRegion(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]) 
    
    def move(self, dx, dy):
        new_x = self.panningOffset[0] + dx * self.moveSensitivity
        new_y = self.panningOffset[1] + dy * self.moveSensitivity
        vp_width = self.rect.width
        vp_height = self.rect.height

        current_map = self.GetCurrentTileMap()
        img = current_map.zoomedImage
        img_width = img.get_width()
        img_height = img.get_height()

        # Pour l'axe X
        if img_width > vp_width:
            # L'image est plus large que le viewport :
            # L'offset autorisé va de (vp_width - img_width) à 0
            min_x = vp_width - img_width
            max_x = 0
        else:
            # L'image est plus petite que le viewport :
            # On autorise l'offset de manière à garder au moins 4 pixels visibles
            min_x = -(img_width - 4)
            max_x = vp_width - 4

        new_x = max(min_x, min(new_x, max_x))

        # Pour l'axe Y
        if img_height > vp_height:
            min_y = vp_height - img_height
            max_y = 0
        else:
            min_y = -(img_height - 4)
            max_y = vp_height - 4

        new_y = max(min_y, min(new_y, max_y))

        self.panningOffset[0] = new_x
        self.panningOffset[1] = new_y



    def hoveredTile(self):
        return self.toGrid(pygame.mouse.get_pos())

    def toGrid(self, screen_pos: tuple,tileSize):
        viewport_x = screen_pos[0] - self.rect.x
        viewport_y = screen_pos[1] - self.rect.y
        relative_x = viewport_x - self.panningOffset[0]
        relative_y = viewport_y - self.panningOffset[1]
        grid_cell_size = tileSize * self.zoom
        grid_x = int(relative_x // grid_cell_size)
        grid_y = int(relative_y // grid_cell_size)
        return (grid_x, grid_y)
    
    def GetTileRectFromRelative(self,x,y,tileSize):
        grid_cell_size = tileSize * self.zoom
        tile_content_x = self.panningOffset[0] + x * grid_cell_size
        tile_content_y = self.panningOffset[1] + y * grid_cell_size
        rect_x = self.rect.x + tile_content_x+1
        rect_y = self.rect.y + tile_content_y+1
        return pygame.Rect(rect_x, rect_y, grid_cell_size, grid_cell_size)

    def Zoom(self,zoom):
        self.zoom=max(self.zoom+zoom*self.zoomSensitivity,0.1)
        self.UpdateZoom()
        
    def UpdateZoom(self):
        self.GetCurrentTileMap().zoomedImage=pygame.transform.scale(
                self.GetCurrentTileMap().image,
                (max(self.GetCurrentTileMap().image.get_width()*self.zoom,0.1),
                max(self.GetCurrentTileMap().image.get_height()*self.zoom,0.1))
            )
        if self.GetCurrentTileMap().colorKey:
            self.GetCurrentTileMap().zoomedImage.set_colorkey(self.GetCurrentTileMap().colorKey)
