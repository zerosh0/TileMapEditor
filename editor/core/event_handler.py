import pygame
from editor.animations.animation import AnimationManager
from editor.core.data_manager import DataManager
from editor.core.history_manager import HistoryManager
from editor.core.settings import Section, SettingsManager
from editor.core.utils import CollisionRect, Light, LocationPoint, Tile, Tools
from editor.vfx.vfx import ParticleEmitter
from editor.game_engine.game_manager import Game
from editor.render import viewport
from editor.render.draw_manager import DrawManager
from editor.render.tile_palette import TilePalette
from editor.ui.DropDownMenu import MenuButton
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import LevelDesign


class EventHandlerManager:

    def __init__(self,editor : 'LevelDesign'):
        self.editor=editor
        self.viewport: viewport = editor.viewport
        self.tilePalette: TilePalette = editor.tilePalette
        self.animations: AnimationManager = editor.animations
        self.DrawManager: DrawManager = editor.DrawManager
        self.dataManager: DataManager = editor.dataManager
        self.settings : SettingsManager = editor.settings
        self.HistoryManager: HistoryManager = editor.HistoryManager
        self.game_engine: Game = editor.game_engine
        self.LeftDragging = False
        self.RightDragging = False
        self.LeftClickStartPos = (0, 0)
        self.RightClickStartPos = (0, 0)
        self.LeftTempPos = (0, 0)
        self.RightTempPos = (0, 0)
        self.DragThreshold = 8
        self.MapDragActive = False
        self.RightMapDragActive = False
        self.RightViewPortDragActive = False
        self.MapDragActive = self.tilePalette.InRegion()
        self.LeftViewPortDragActive = self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap()
        self.discard_current_event = False

    def HandleEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if getattr(self.dataManager, "show_vfx_placement_tip", False):
                    self.dataManager.show_vfx_placement_tip = False
                if getattr(self.dataManager, "show_collision_placement_tip", False):
                    self.dataManager.show_collision_placement_tip = False
            self.discard_current_event = False
            self.HandleUiEvents(event)
            if self.discard_current_event:
                continue
            self.editor.game_engine.handle_events(event)
            match event.type:
                case pygame.QUIT:
                    self.editor.running = False
                case pygame.MOUSEWHEEL:
                    self.HandleMouseWheel(event)
                case pygame.MOUSEBUTTONDOWN:
                    self.HandleMouseButtonDown(event)
                case pygame.MOUSEMOTION:
                    self.HandleMouseMotion(event)
                case pygame.MOUSEBUTTONUP:
                    self.HandleMouseUp(event)
                case pygame.KEYDOWN:
                    self.HandleKeyDown(event)
                case pygame.VIDEORESIZE:
                    self.ResizeWindow()

    def ResizeWindow(self):
        self.DrawManager.UpdateRect()
        self.animations.update_rect()
        self.tilePalette.UpdateRect(self.DrawManager.TilePaletteSurfaceZoom)
        self.viewport.UpdateRect(self.DrawManager.TilePaletteSurfaceZoom)
        self.settings.update_rect()
        if self.animations.get_current_anim():
            self.animations.get_current_anim().timeline.update_rect()


    def HandleUiEvents(self, event):
        if self.dataManager.selectedElement and self.settings.active_section==Section.HIDDEN and not self.animations.panel_visible and not self.game_engine.running:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.DrawManager.colorPick.rect.collidepoint(event.pos):
                self.discard_current_event = True
            self.DrawManager.colorPick.handle_event(event)
        if self.DrawManager.colorPick.picker_visible:
            return
        self.animations.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.DrawManager.playButton.rect.collidepoint(event.pos):
            self.discard_current_event = True
        self.DrawManager.playButton.handle_event(event)
        if self.animations.get_current_anim() and not self.game_engine.running:
            self.animations.get_current_anim().timeline.handle_event(event)
        for button in self.DrawManager.buttons:
            if isinstance(self.dataManager.selectedElement, ParticleEmitter) and getattr(button, "action_name", "") == "editName":
                continue
            if self.settings.active_section==Section.HIDDEN or isinstance(button,MenuButton):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and button.rect.collidepoint(event.pos):
                    self.discard_current_event = True
                if not self.animations.panel_visible:
                    button.handle_event(event)
                elif not hasattr(button, "image_path"):
                    button.handle_event(event)
                elif not button.action_name in ["show","editName","editType","graph"] and not self.game_engine.running:
                    button.handle_event(event)
        if self.settings.active_section==Section.HIDDEN:
            if not self.animations.panel_visible:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.DrawManager.slider.rect.inflate(10, 10).collidepoint(event.pos):
                    self.discard_current_event = True
                self.DrawManager.slider.handle_event(event)
                if self.dataManager.selectedElement and isinstance(self.dataManager.selectedElement, ParticleEmitter):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.DrawManager.scale_slider.rect.inflate(10, 10).collidepoint(event.pos):
                        self.discard_current_event = True
                    self.DrawManager.scale_slider.handle_event(event)
                    self.dataManager.selectedElement.overall_scale = self.DrawManager.scale_slider.value
        else:
            self.settings.handle_event(event)
        self.dataManager.getCurrentLayer().opacity=self.DrawManager.slider.value

    def HandleMouseWheel(self, event):
        if self.tilePalette.InRegion() and self.tilePalette.GetCurrentTileMap():
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL:
                self.DrawManager.TilePaletteSurfaceZoom=max(1.0,self.DrawManager.TilePaletteSurfaceZoom+event.y*0.1)
                self.DrawManager.UpdateRect()
                self.tilePalette.UpdateRect(self.DrawManager.TilePaletteSurfaceZoom)
            else:   
                self.tilePalette.Zoom(event.y)
                self.DrawManager.viewportSelectionPreview=False
                self.dataManager.selectionViewPort=[]
        elif self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap():
            self.DrawManager.viewportSelectionPreview=False
            self.dataManager.selectionViewPort=[]
            self.viewport.Zoom(event.y)
            self.DrawManager.tile_cache.clear()
            self.dataManager.UpdateCurrentTiles(self.viewport)

    def HandleMouseButtonDown(self, event):
        if event.button == 1:  # Clic gauche
            self.LeftClickStartPos = event.pos
            self.LeftTempPos = event.pos
            self.MapDragActive = self.tilePalette.InRegion()
            self.LeftViewPortDragActive = self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap()
            if self.dataManager.currentTool == Tools.LocationPoint and self.LeftViewPortDragActive:
                self.dataManager.AddLocationPoint(self.viewport,self.DrawManager.locationPointImage)
            if self.dataManager.currentTool == Tools.VFX and self.LeftViewPortDragActive:
                self.dataManager.AddVFXEmitter(self.viewport)
            if self.dataManager.currentTool == Tools.Light and not self.viewport.light_preview and  \
                self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap():
                self.viewport.light_origin = event.pos
                self.viewport.light_preview = True
                self.viewport.light_current = event.pos
        elif event.button == 3 and not self.DrawManager.colorPick.picker_visible:  # Clic droit
            self.RightClickStartPos = event.pos
            self.RightTempPos = event.pos
            self.RightViewPortDragActive = self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap()
            self.RightMapDragActive = self.tilePalette.InRegion() and self.tilePalette.GetCurrentTileMap()
            self.MapDragActive = self.tilePalette.InRegion()

    def HandleMouseMotion(self, event):
        if pygame.mouse.get_pressed()[0]:  # Clic gauche maintenu
            self.HandleAction()
            if abs(event.pos[0] - self.LeftClickStartPos[0]) > self.DragThreshold or \
               abs(event.pos[1] - self.LeftClickStartPos[1]) > self.DragThreshold:
                self.LeftDragging = True
                if self.MapDragActive and self.LeftDragging:
                        self.tilePalette.move(event.pos[0] - self.LeftTempPos[0], event.pos[1] - self.LeftTempPos[1])
                if self.LeftViewPortDragActive and self.LeftDragging and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    self.dataManager.selectionViewPort=(self.LeftClickStartPos,pygame.mouse.get_pos())
                    self.DrawManager.viewportSelectionPreview=True
                elif self.viewport.InRegion():
                    self.DrawManager.viewportSelectionPreview=False
                    self.dataManager.selectionViewPort=[]
                self.LeftTempPos = event.pos
        if pygame.mouse.get_pressed()[2]:  # Clic droit maintenu
            if abs(event.pos[0] - self.RightClickStartPos[0]) > self.DragThreshold or \
               abs(event.pos[1] - self.RightClickStartPos[1]) > self.DragThreshold:
                self.RightDragging = True
                if self.RightViewPortDragActive and not self.MapDragActive:
                    self.viewport.move(event.pos[0] - self.RightTempPos[0], event.pos[1] - self.RightTempPos[1])
                elif self.MapDragActive and self.RightMapDragActive:
                    self.DrawManager.PaletteSelectionPreview=True
                    self.dataManager.selectionPalette=(self.RightClickStartPos,pygame.mouse.get_pos())
                self.RightTempPos = event.pos
            if self.viewport.InRegion():
                    self.DrawManager.viewportSelectionPreview=False
                    self.dataManager.selectionViewPort=[]
        if self.tilePalette.GetCurrentTileMap() and not (self.MapDragActive or self.RightViewPortDragActive) and self.viewport.InRegion():
            self.DrawManager.TilePreview=True
            self.dataManager.UpdateCurrentTiles(self.viewport)
        else:
            self.DrawManager.TilePreview=False
        if self.viewport.light_preview and self.viewport.light_origin:
            self.viewport.light_current = event.pos


    def HandleMouseUp(self, event):
        if event.button == 1:
            if self.LeftDragging:
                self.Handledragclick()
            else:
                self.Handleclick(event)
            self.LeftDragging = False
            self.MapDragActive = False
        elif event.button == 3:
            if self.RightDragging:
                self.Handledragclick()
            else:
                if not self.DrawManager.colorPick.picker_visible and not self.animations.mouse_on_timeline():
                    self.dataManager.ChangeSelectedCollisionRect(self.viewport,self.DrawManager.locationPointImage)
            self.DrawManager.PaletteSelectionPreview=False
            self.MapDragActive=False
            self.RightDragging = False
            self.LeftViewPortDragActive=False
            self.RightMapDragActive = False
            self.RightViewPortDragActive = False
        self.lastAddedTilePositions = None

    def Handledragclick(self):
        if self.RightMapDragActive:
            self.dataManager.ChangeCurrentTilesSelection(self.tilePalette)

    def HandleAction(self):
        if self.DrawManager.TilePreview and not self.DrawManager.viewportSelectionPreview and not pygame.key.get_pressed()[pygame.K_LSHIFT] and self.viewport.InRegion():
            if self.dataManager.currentTool == Tools.Draw and not self.MapDragActive:
                self.dataManager.AddCurrentTiles()
            if self.dataManager.currentTool == Tools.Rubber:
                self.HistoryManager.RegisterRemoveTiles(self.dataManager.currentLayer,[self.viewport.toGrid(pygame.mouse.get_pos())],self.dataManager)
                x,y=self.viewport.toGrid(pygame.mouse.get_pos())
                self.dataManager.RemoveTile(x,y)

    def Handleclick(self,event):
        self.HandleAction()
        if self.tilePalette.GetCurrentTileMap() and self.tilePalette.InRegion():
            grid_x, grid_y = self.tilePalette.toGrid(pygame.mouse.get_pos(), self.tilePalette.GetCurrentTileMap().tileSize)
            self.dataManager.currentTiles = [Tile(self.tilePalette.GetCurrentTileMap().name, 0, 0, grid_x, grid_y)]
        if self.dataManager.currentTool == Tools.Light:
            if self.viewport.light_preview and self.viewport.light_origin :
                ox, oy = self.viewport.light_origin
                x, y = event.pos
                radius = ((x-ox)**2 + (y-oy)**2)**0.5 / self.viewport.zoom
                if radius>25:
                    self.dataManager.addLight(self.viewport.light_origin, radius,self.viewport)
                    self.viewport.light_origin = None
                    self.viewport.light_preview = False


    def HandleKeyDown(self, event):
        if self.game_engine.running:
            return

        if event.key == pygame.K_UP:
            self.dataManager.changeCurrentLayer(1)
            self.DrawManager.updateLayerText(self.dataManager.currentLayer)
            self.DrawManager.slider.value=self.dataManager.getCurrentLayer().opacity
            
        elif event.key == pygame.K_DOWN:
            self.dataManager.changeCurrentLayer(-1)
            self.DrawManager.slider.value=self.dataManager.getCurrentLayer().opacity
            self.DrawManager.updateLayerText(self.dataManager.currentLayer)
        elif event.key == pygame.K_RIGHT:
            self.tilePalette.changeCurrentTileMap(1)
        elif event.key == pygame.K_LEFT:
            self.tilePalette.changeCurrentTileMap(-1)
        elif event.key == pygame.K_DELETE:
            if self.dataManager.selectedElement:
                if isinstance(self.dataManager.selectedElement,CollisionRect):
                    self.dataManager.collisionRects.remove(self.dataManager.selectedElement)
                    self.HistoryManager.RegisterRemoveElement(self.dataManager.selectedElement)
                elif isinstance(self.dataManager.selectedElement,LocationPoint):
                    self.dataManager.locationPoints.remove(self.dataManager.selectedElement)
                    self.HistoryManager.RegisterRemoveElement(self.dataManager.selectedElement)
                elif isinstance(self.dataManager.selectedElement,Light):
                    self.dataManager.lights.remove(self.dataManager.selectedElement)
                    self.HistoryManager.RegisterRemoveLight(self.dataManager.selectedElement)
                elif isinstance(self.dataManager.selectedElement,ParticleEmitter):
                    self.dataManager.emitters.remove(self.dataManager.selectedElement)
                    self.HistoryManager.RegisterRemoveElement(self.dataManager.selectedElement)
                
                self.dataManager.selectedElement=None
        elif event.key == pygame.K_z and event.mod & pygame.KMOD_LCTRL:
            self.HistoryManager.Undo(self.dataManager)
        elif event.key == pygame.K_y and event.mod & pygame.KMOD_LCTRL:
            self.HistoryManager.Redo(self.dataManager)
        elif event.key == pygame.K_h:
            self.settings.is_grid_visible = not self.settings.is_grid_visible
            for widget in self.settings.widgets[Section.ADVANCED]:
                if widget[2]=="is_grid_visible":
                    widget[1].state=self.settings.is_grid_visible

