from datetime import datetime
import tkinter as tk
from tkinter import simpledialog,filedialog,colorchooser
from editor.DataManager import *
from editor.History import HistoryManager
from editor.draw import DrawManager
from editor.TilePalette import TilePalette
from editor.saveLoader import SaveLoadManager
from editor.tilemapOpener import FileOpener
import pygame
from editor.utils import Colors
from editor.viewport import ViewPort


class LevelDesign:
    def __init__(self, screen: pygame.surface.Surface):
        self.version=0.2
        self.screen = screen
        self.zoom_sensitivity = 0.25
        self.move_sensitivity = 1
        self.running = True

        # Gestion des données et de l'affichage
        self.HistoryManager = HistoryManager()
        self.dataManager = DataManager(self.HistoryManager) 
        self.tilePalette = TilePalette(self.screen, self.move_sensitivity, self.zoom_sensitivity)
        self.viewport = ViewPort(self.screen, self.move_sensitivity, self.zoom_sensitivity)
        self.TmapOpener = FileOpener(self.screen, self.tilePalette,self.ResizeWindow)
        
        
        # Actions utilisateur
        self.actions = {
            "save": self.save_level,
            "open": self.open_level,
            "load": self.load_level,
            "play": lambda: print("play"),
            "rubber": lambda: self.setTool(Tools.Rubber),
            "selection": lambda: self.setTool(Tools.Selection),
            "fill": lambda: self.setTool(Tools.Fill),
            "random": lambda: self.setTool(Tools.Random),
            "flip_vertical": lambda: self.dataManager.flipCurrentTiles(Axis.Vertical),
            "flip_horizontal": lambda: self.dataManager.flipCurrentTiles(Axis.Horizontal),
            "draw": lambda: self.setTool(Tools.Draw),
            "location_point": lambda: self.setTool(Tools.LocationPoint),
            "rotate": self.dataManager.RotateCurrentTiles,
            "show": self.ChangeShowState,
            "editName": self.EditName,
            "editType": self.EditType,
            "editColor":self.EditColor
        }
        self.DrawManager = DrawManager(self.screen, self.actions)
        self.saveLoadManager=SaveLoadManager()
        self.PostInit()

    def PostInit(self):
        # État des interactions
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


    def open_level(self):
        file_path=self.saveLoadManager.open(self)

        if not file_path:
            print("Aucune image sélectionnée.")
            return
        self.TmapOpener.filepath=file_path
        self.TmapOpener.image = pygame.image.load(file_path).convert_alpha()
        tileSize=simpledialog.askinteger("Taille des tiles", "Entrez la taille des tiles (ex: 32):", initialvalue=32)
        if not tileSize:
            print("Opération Annulée")
            return
        TileMapName=simpledialog.askstring("Nom de la tile map", "Entrez le nom de la tile map:")
        if not TileMapName:
            print("Opération Annulée")
            return
        self.TmapOpener.processTileMap(tileSize,TileMapName)


    def save_level(self):
        self.saveLoadManager.save(self)

    def load_level(self):
        self.saveLoadManager.load(self)


    def ChangeShowState(self):
        self.viewport.displayRect = not self.viewport.displayRect

    def setTool(self,tool : Tools):
        self.dataManager.setTool(tool,self.viewport)
        if self.DrawManager.viewportSelectionPreview:
            self.DrawManager.viewportSelectionPreview=False
            self.dataManager.selectionViewPort=[]

    def HandleEvents(self):
        for event in pygame.event.get():
            self.HandleUiEvents(event)
            match event.type:
                case pygame.QUIT:
                    self.running = False
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
        self.tilePalette.UpdateRect()
        self.viewport.UpdateRect()

    def EditName(self):
        if self.dataManager.currentTool==Tools.LocationPoint:
            self.dataManager.currentTool=Tools.Draw
        self.dataManager.currentTiles=[]
        name = simpledialog.askstring("Nom du rectangle", "Entrez le nouveau nom du rectangle:")
        if name:
            self.dataManager.selectedElement.name = name
        else:
            print("Format d'entrée invalide")

    def EditColor(self,new_color):
        if self.dataManager.currentTool==Tools.LocationPoint:
            self.dataManager.currentTool=Tools.Draw
        self.dataManager.currentTiles=[]
        self.dataManager.selectedElement.color = new_color

    def EditType(self):
        self.dataManager.currentTiles=[]
        if self.dataManager.currentTool==Tools.LocationPoint:
            self.dataManager.currentTool=Tools.Draw
        type_value = simpledialog.askstring("Type du rectangle", "Entrez le nouveau type du rectangle:")
        if type_value:
            self.dataManager.selectedElement.type = type_value
        else:
            print("Format d'entrée invalide")



    def HandleUiEvents(self, event):
        for button in self.DrawManager.buttons:
            button.handle_event(event)
        self.DrawManager.slider.handle_event(event)
        self.DrawManager.colorPick.handle_event(event)
        self.dataManager.getCurrentLayer().opacity=self.DrawManager.slider.value

    def HandleMouseWheel(self, event):
        if self.tilePalette.InRegion() and self.tilePalette.GetCurrentTileMap():
            self.tilePalette.Zoom(event.y)
            self.DrawManager.viewportSelectionPreview=False
            self.dataManager.selectionViewPort=[]
        elif self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap():
            self.DrawManager.viewportSelectionPreview=False
            self.dataManager.selectionViewPort=[]
            self.viewport.Zoom(event.y)
            self.UpdateCurrentTiles()

    def HandleMouseButtonDown(self, event):
        if event.button == 1:  # Clic gauche
            self.LeftClickStartPos = event.pos
            self.LeftTempPos = event.pos
            self.MapDragActive = self.tilePalette.InRegion()
            self.LeftViewPortDragActive = self.viewport.InRegion() and self.tilePalette.GetCurrentTileMap()
            if self.dataManager.currentTool == Tools.LocationPoint and self.LeftViewPortDragActive:
                self.dataManager.AddLocationPoint(self.viewport,self.DrawManager.locationPointImage,self.DrawManager.DottedlocationPointImage)
        elif event.button == 3:  # Clic droit
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
                if self.RightViewPortDragActive:
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
            self.UpdateCurrentTiles()
        else:
            self.DrawManager.TilePreview=False



    def HandleMouseUp(self, event):
        if event.button == 1:
            if self.LeftDragging:
                self.Handledragclick()
            else:
                self.Handleclick()
            self.LeftDragging = False
            self.MapDragActive = False
        elif event.button == 3:
            if self.RightDragging:
                self.Handledragclick()
            else:
                self.dataManager.ChangeSelectedCollisionRect(self.viewport)
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
        if self.DrawManager.TilePreview and not self.DrawManager.viewportSelectionPreview and not pygame.key.get_pressed()[pygame.K_LSHIFT]:
            if self.dataManager.currentTool == Tools.Draw and not self.MapDragActive:
                self.dataManager.AddCurrentTiles()
            if self.dataManager.currentTool == Tools.Rubber:
                self.HistoryManager.RegisterRemoveTiles(self.dataManager.currentLayer,[self.viewport.toGrid(pygame.mouse.get_pos())],self.dataManager)
                self.dataManager.getCurrentLayer().removeTile(self.viewport.toGrid(pygame.mouse.get_pos()))

    def Handleclick(self):
        self.HandleAction()
        if self.tilePalette.GetCurrentTileMap() and self.tilePalette.InRegion():
            grid_x, grid_y = self.tilePalette.toGrid(pygame.mouse.get_pos(), self.tilePalette.GetCurrentTileMap().tileSize)
            self.dataManager.currentTiles = [Tile(self.tilePalette.GetCurrentTileMap().name, 0, 0, grid_x, grid_y)]


    def HandleKeyDown(self, event):
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
                else:
                    self.dataManager.locationPoints.remove(self.dataManager.selectedElement)
                self.HistoryManager.RegisterRemoveElement(self.dataManager.selectedElement)
                self.dataManager.selectedElement=None
        elif event.key == pygame.K_z and event.mod & pygame.KMOD_LCTRL:
            self.HistoryManager.Undo(self.dataManager)
        elif event.key == pygame.K_y and event.mod & pygame.KMOD_LCTRL:
            self.HistoryManager.Redo(self.dataManager)
        elif event.key == pygame.K_h:
            self.DrawManager.drawVGrid= not self.DrawManager.drawVGrid

    def UpdateCurrentTiles(self):
        self.dataManager.UpdateCurrentTiles(self.viewport)

    def run(self):
        while self.running:
            self.HandleEvents()
            self.DrawManager.draw(self.viewport, self.dataManager, self.tilePalette)
            pygame.display.flip()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    pygame.init()
    screen = pygame.display.set_mode((1000, 700),pygame.RESIZABLE)
    Editor=LevelDesign(screen)
    pygame.display.set_caption(f'Editeur de Niveau Alpha {Editor.version}')
    try:
        Editor.run()
    except Exception as e:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = random.randint(1000, 9999)
        save_name = f"SecureSave_{timestamp}_{random_id}.json"
        
        # Sauvegarde d'urgence
        Editor.saveLoadManager.save(Editor, save_name)
        
        print(f"\n{Colors.RED}╔═══════════════════════════════════════════════════╗")
        print(f"║ {Colors.YELLOW}CRASH DE L'EDITEUR ! {Colors.RED}")
        print(f"╠═══════════════════════════════════════════════════╣")
        print(f"║ {Colors.YELLOW}Erreur : {Colors.RESET}{str(e)}{Colors.RED}")
        print(f"║ {Colors.YELLOW}Type : {Colors.RESET}{type(e).__name__}{Colors.RED}")
        print(f"╠═══════════════════════════════════════════════════╣")
        print(f"║ {Colors.GREEN}Une sauvegarde de secours a été créée :{Colors.RED}")
        print(f"║ {Colors.BLUE}{save_name}{Colors.RED}")
        print(f"╚═══════════════════════════════════════════════════╝{Colors.RESET}\n")
        
        raise