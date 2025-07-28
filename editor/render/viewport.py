
import pygame
from editor.animations.animation import AnimationManager
from editor.ui.DropDownMenu import MenuButton



class ViewPort():
    def __init__(self,screen,moveSensitivity,zoomSensitivity,animation : AnimationManager):
        self.screen=screen
        self.moveSensitivity=moveSensitivity
        self.zoomSensitivity=zoomSensitivity
        self.tileSize=16
        self.zoom=1.0
        self.panningOffset=[0,0]
        self.parallaxOffset=[0,0]
        self.surface=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-30))
        self.rect = self.surface.get_rect()
        self.tilePaletteRect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210,230)
        self.screen_pos = (self.rect.x, self.rect.y)
        self.displayRect=True
        self.light_origin = None
        self.light_preview = False
        self.light_current=None
        self.forbiddenStates=[]
        self.game_engine_running=False
        self.animation=animation

    def UpdateRect(self,SurfaceZoom):
        self.surface=pygame.surface.Surface((self.screen.get_width() - 250,self.screen.get_height()-30))
        self.rect = self.surface.get_rect()
        self.tilePaletteRect=pygame.Rect(self.screen.get_width() - 230, self.screen.get_height() - 270,210*SurfaceZoom,230*SurfaceZoom)
        self.tilePaletteRect.bottom=self.screen.get_height()-40
        self.tilePaletteRect.right=self.screen.get_width()-20

    def isInteractionAllowed(self):
        for state in self.forbiddenStates:
            if isinstance(state,MenuButton):
                if state.dropdown.is_open:
                    return False
        return True

    def InRegion(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]-30) and not \
               self.tilePaletteRect.collidepoint(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]) and \
               self.isInteractionAllowed() and not self.animation.mouse_on_timeline() and not self.animation.dialog and not \
               (self.animation.get_current_anim() and \
                (self.animation.get_current_anim().timeline.dragging_cursor or self.animation.get_current_anim().timeline.dragging_kf)) and not self.game_engine_running
               

    def move(self,dx,dy):
        self.panningOffset[0]+=dx*self.moveSensitivity
        self.panningOffset[1]+=dy*self.moveSensitivity
        self.parallaxOffset[0]+=dx*self.moveSensitivity
        self.parallaxOffset[1]+=dy*self.moveSensitivity

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

    def getMouseGridPos(self):
        return self.toGrid(pygame.mouse.get_pos())
    
    def GetTileRectFromRelative(self,x,y):
        grid_cell_size = self.tileSize * self.zoom
        tile_content_x = self.panningOffset[0] + x * grid_cell_size
        tile_content_y = self.panningOffset[1] + y * grid_cell_size
        rect_x = self.rect.x + round(tile_content_x)
        rect_y = self.rect.y + round(tile_content_y)
        return pygame.Rect(rect_x, rect_y, grid_cell_size, grid_cell_size)

    def Zoom(self, zoom_delta):
        old_zoom = self.zoom
        new_zoom = max(old_zoom + zoom_delta * self.zoomSensitivity, 0.25)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x = mouse_x - self.rect.x
        rel_y = mouse_y - self.rect.y
        world_x = (rel_x - self.panningOffset[0]) / old_zoom
        world_y = (rel_y - self.panningOffset[1]) / old_zoom
        self.zoom = round(new_zoom, 2)
        self.panningOffset[0] = rel_x - world_x * self.zoom
        self.panningOffset[1] = rel_y - world_y * self.zoom



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

    def ChangeShowState(self):
        self.displayRect = not self.displayRect