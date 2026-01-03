from typing import Dict
from editor.animations.animation import AnimationManager
from editor.blueprint_editor.system import BlueprintEditor
from editor.core.data_manager import *
from editor.core.event_handler import EventHandlerManager
from editor.game_engine.game_manager import Game
from editor.services.dialog_controller import DialogController
from editor.core.history_manager import HistoryManager
from editor.render.draw_manager import DrawManager
from editor.render.tile_palette import TilePalette
from editor.services.documentation import DocServer
from editor.ui.Notifications import NotificationManager
from editor.services.save_loader import SaveLoadManager
from editor.core.settings import Section, SettingsManager
from editor.services.tilemap_opener import FileOpener
from editor.core.utils import Colors, open_github
from editor.render.viewport import ViewPort
from editor.services.update_handler import UpdateAndCrashHandler
from editor.game_engine.core.level import Level
import threading
import traceback
import pygame


from editor.ui.Release import ReleaseNotesPopup
from editor.vfx.play_ground import ParticleEditor

class LevelDesign:
    def __init__(self, screen: pygame.surface.Surface):
        self.running = True
        self.version=1.2
        self.screen = screen
        self.zoom_sensitivity = 0.25
        self.move_sensitivity = 1
        self.level_loaded=False
        self.clipboard: List[Dict] = []
        self.nm = NotificationManager()
        self.doc = DocServer(self.nm)
        self.settings = SettingsManager(self.screen,"./Assets/ui/settings_ui.json",self.nm)
        self.HistoryManager = HistoryManager()
        self.animations = AnimationManager(self.screen,self.nm,self.timelineClick) 
        self.dataManager = DataManager(self.HistoryManager,self.settings,self.animations)
        self.settings.dataManager=self.dataManager
        self.tilePalette = TilePalette(self.screen, self.move_sensitivity, self.zoom_sensitivity)
        self.viewport = ViewPort(self.screen, self.move_sensitivity, self.zoom_sensitivity,self.animations)
        self.clock = pygame.time.Clock()
        self.saveLoadManager=SaveLoadManager(self.screen,self.nm)
        self.updateChecker = UpdateAndCrashHandler(
            repo_owner="zerosh0",
            repo_name="TileMapEditor",
            local_commit_file="last_commit.txt",
            screen=self.screen,
            version=self.version
        )
        threading.Thread(target=self.updateChecker.schedule_update_check, daemon=True).start()
        self.DrawManager = DrawManager(self.screen,self.updateChecker,self.nm,self.settings)
        self.viewport.forbiddenStates.extend(self.DrawManager.buttons)
        # Actions utilisateur
        self.actions = {
            "save": lambda: self.save_level(self),
            "open": lambda: self.DialogController.open_level(),
            "load": self.load_level,
            "world_settings": lambda: self.settings.change_section(Section.WORLD),
            "player_settings": lambda: self.settings.change_section(Section.PLAYER_PROFILE),
            "interface_settings": lambda: self.settings.change_section(Section.INTERFACE),
            "advanced_settings": lambda: self.settings.change_section(Section.ADVANCED),
            "New":self.new,
            "rubber": lambda: self.setTool(Tools.Rubber),
            "selection": lambda: self.setTool(Tools.Selection),
            "fill": lambda: self.setTool(Tools.Fill),
            "random": lambda: self.setTool(Tools.Random),
            "flip_vertical": lambda: self.dataManager.flipCurrentTiles(Axis.Vertical),
            "flip_horizontal": lambda: self.dataManager.flipCurrentTiles(Axis.Horizontal),
            "draw": lambda: self.setTool(Tools.Draw),
            "location_point": lambda: self.setTool(Tools.LocationPoint),
            "light": lambda: self.setTool(Tools.Light),
            "VFX": lambda: self.vfx(),
            "rotate": lambda: self.dataManager.RotateCurrentTiles(),
            "show": lambda: self.viewport.ChangeShowState(),
            "editName": lambda: self.DialogController.EditName(),
            "editType": lambda: self.DialogController.EditType(),
            "editColor": lambda color: self.dataManager.EditColor(color),
            "bg_next": self.dataManager.bg_next,
            "bg_prev": self.dataManager.bg_prev,
            "toggle_settings": lambda: self.dataManager.toogle_settings_display(),
            "open_github": lambda: open_github(),
            "open_timeline" : lambda: self.animations.toogleTimeline(),
            "new_animation": lambda: self.DialogController.CreateAnimation(),
            "animation_panel": self.toogleAnimPanel,
            "sync_animations": lambda: self.animations.sync(),
            "play": lambda s: self.playGame(s),
            "graph": lambda : self.openGraph(),
            "open_doc": self.doc.open_docs
        }
        self.DrawManager.loadAssets(self.actions)
        self.settings.dataManager=self.dataManager
        self.game_engine=Game(self.screen,self.dataManager,self.tilePalette,self.clock,self.animations,self.nm)
        self.eventHandler=EventHandlerManager(self)
        self.TmapOpener = FileOpener(self.screen, self.tilePalette,self.eventHandler.ResizeWindow,self.nm)
        self.DialogController=DialogController(self.screen,self.nm,self.dataManager,
                                               self.animations,self.TmapOpener,self.saveLoadManager,self.clock)
        self.settings.game_engine=self.game_engine
        self.dataManager.game_engine=self.game_engine
        self.init_system()
        self.viewport.forbiddenStates.extend(self.DrawManager.buttons)
        self.settings.load_settings()
        self.popup = ReleaseNotesPopup(
            screen_size=screen.get_size(),
            on_close=self.tutorial
        )
        
        

    def clear_cache(self):
        self.settings._save_settings()
        self.clipboard: List[Dict] = []
        self.game_engine.running=False
        self.HistoryManager = HistoryManager()
        self.animations = AnimationManager(self.screen,self.nm,self.timelineClick) 
        self.dataManager = DataManager(self.HistoryManager,self.settings,self.animations) 
        self.tilePalette = TilePalette(self.screen, self.move_sensitivity, self.zoom_sensitivity)
        self.viewport = ViewPort(self.screen, self.move_sensitivity, self.zoom_sensitivity,self.animations)
        self.DrawManager = DrawManager(self.screen,self.updateChecker,self.nm,self.settings)
        self.TmapOpener.tilePalette=self.tilePalette
        self.settings.load_settings()
        self.DrawManager.settings=self.settings
        self.DrawManager.loadAssets(self.actions)
        self.viewport.forbiddenStates.extend(self.DrawManager.buttons)
        self.settings.dataManager=self.dataManager
        self.settings.game_engine=self.game_engine
        self.dataManager.game_engine=self.game_engine
        self.DialogController=DialogController(self.screen,self.nm,self.dataManager,
                                               self.animations,self.TmapOpener,self.saveLoadManager,self.clock)
        self.eventHandler=EventHandlerManager(self)
        if len(self.animations.animations)==0:
            self.animations.create("animation_1",2.0)
        self.animations.get_current_anim().timeline.active=False


    def init_system(self):
        if self.settings.start_mode==0:
            self.saveLoadManager.load(self,"./Exemples/new_exemple.json",init=True)
        elif self.settings.start_mode==1:
            self.saveLoadManager.load(self,"./Exemples/exemple.json",init=True)
        elif self.settings.start_mode==2:
            self.new()
        else:
            try:
                self.saveLoadManager.load(self,self.settings.last_path,init=True) 
            except:
                self.new()

                
    def update_game_engine(self):
        self.settings.game_engine=self.game_engine                
                  
                      
                  

    def timelineClick(self):
        self.dataManager.selectedElement = None

    def save_level(self,editor):
        if self.dataManager.currentTool==Tools.Light:
            self.dataManager.currentTool=Tools.Draw
        self.saveLoadManager.save(editor)

    def load_level(self):
        try:
            self.saveLoadManager.load(self)
        except Exception as e:
            print("Erreur lors de l'ouverture du niveau !\n",Colors.RED,traceback.format_exc(),Colors.RESET)
            self.clear_cache()
            self.nm.notify('error', 'Erreur', "Erreur lors de l'ouverture du niveau !",duration=4)

    def update(self,dt):
            self.nm.update(dt)
            self.settings.update_startmode_dropdown()
            self.animations.update(dt,self.dataManager)
            self.game_engine.update(self.settings)
            self.DrawManager.playButton.state=self.game_engine.running
            if self.settings.game_engine is None:
                self.settings.game_engine=self.game_engine
    

    def draw(self):
            self.DrawManager.draw(self.viewport, self.dataManager, self.tilePalette,self.animations,self.clock,self.game_engine)
            self.nm.draw(self.screen)
            self.popup.run(screen, version=self.version)

    def run(self):
        while self.running:
            fps=60 if self.game_engine.running else 0
            dt = self.clock.tick(fps) / 1000.0
            self.eventHandler.HandleEvents()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        self.settings._save_settings()


    def playGame(self,_state):
        if not self.settings.player_spawn_point:
            self.nm.notify('warning', 'Attention', 'Veuillez d\'abord choisir un SpawnPoint.', duration=1.5)
            self.DrawManager.playButton.state=False
            return
    
        self.game_engine.player.audio_manager.clear_sounds()
        self.game_engine.level=Level.from_data_manager(self.dataManager,self.tilePalette,self.animations)
        self.game_engine.player.level=self.game_engine.level
        self.game_engine.player.collisions.level=self.game_engine.level
        self.game_engine.player.update_location_by_name(self.settings.player_spawn_point)
        self.game_engine.player.last_action_time = pygame.time.get_ticks()
        self.game_engine.level.draw_player=lambda s : self.game_engine.player.draw(s)
        for enemy in self.game_engine.enemies:
            enemy.level=self.game_engine.level
            enemy.collisions.level=self.game_engine.level
        self.game_engine.running= not self.game_engine.running
        self.viewport.game_engine_running=self.game_engine.running
        if self.viewport.game_engine_running:
            self.game_engine.update_settings(self.settings)
            self.game_engine.player.movement.clear_forces()
            self.game_engine.player.health_system.health=self.game_engine.player.health_system.max_health
            self.game_engine.level.shadow_alpha=self.settings.global_illum*255
            self.game_engine.level.reset_text()
            for Collisionrect in self.game_engine.level.scaled_collision_rects:
                if Collisionrect.graph is not None:
                            Collisionrect.graph._reset_flipflops()
                            Collisionrect.graph._reset_once_nodes()
                            Collisionrect.graph.clear_error()
                            start=Collisionrect.graph.events.get("on_start")
                            if start:
                                Collisionrect.graph.run_logic_from_event(start)
        else:
            
            for Collisionrect in self.game_engine.level.scaled_collision_rects:
                if Collisionrect.graph is not None:
                            start=Collisionrect.graph.events.get("on_end")
                            if start:
                                Collisionrect.graph.run_logic_from_event(start)

    def openGraph(self):
        if isinstance(self.dataManager.selectedElement,CollisionRect):
            if self.dataManager.selectedElement.graph is not None:
                self.dataManager.selectedElement.graph.run()
            else:
                self.dataManager.selectedElement.graph=BlueprintEditor(self)
                self.dataManager.selectedElement.graph.run()
            self.eventHandler.ResizeWindow()

    def toogleAnimPanel(self):
        self.animations._toggle_panel()
        if self.animations.panel_visible:
            self.settings.active_section=Section.HIDDEN

    def vfx(self):
        ok = self.DialogController.ask_confirmation(
            "Le système de particules est en phase expérimentale. Voulez-vous ouvrir la sandbox ?",150
        )
        if not ok: return
        self.setTool(Tools.VFX)
        ParticleEditor(self.screen,self.clock).run()
        self.eventHandler.ResizeWindow()
        


    def tutorial(self,already_open):
        if already_open: return
        ok = self.DialogController.ask_confirmation(
            "C'est votre première utilisation de l'éditeur. Souhaitez-vous ouvrir la documentation maintenant ? Vous pourrez toujours y accéder plus tard via Aide > Documentation.",150
        )
        if not ok: return
        self.doc.open_docs()

    def new(self):
        if self.tilePalette.GetCurrentTileMap() and self.level_loaded:
            ok = self.DialogController.ask_confirmation(
                "Des modifications non sauvegardées seront perdues. Créer un nouveau niveau ?"
            )
            if not ok:
                return
        self.settings = SettingsManager(self.screen,"./Assets/ui/settings_ui.json",self.nm)
        self.clear_cache()
        self.level_loaded=True

    def setTool(self,tool : Tools):
        if self.dataManager.show_settings:
            return
        self.dataManager.setTool(tool,self.viewport)
        if self.DrawManager.viewportSelectionPreview:
            self.DrawManager.viewportSelectionPreview=False
            self.dataManager.selectionViewPort=[]



if __name__ == "__main__":
    # En cas OSError: [Errno 24] Too many open files
    # if sys.platform != "win32":
    #     import resource
    #     soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    #     if soft < 2048:
    #         try:
    #             resource.setrlimit(resource.RLIMIT_NOFILE, (min(4096, hard), hard))
    #             print(f"✅ Limite de fichiers augmentée à {min(4096, hard)} (max possible : {hard})")
    #         except Exception as e:
    #             print(f"⚠️ Impossible d'augmenter la limite de fichiers ouverts : {e}")
    pygame.init()
    pygame.key.set_repeat(300, 50)
    pygame.mixer.set_num_channels(32)
    screen = pygame.display.set_mode((1000, 700),pygame.RESIZABLE)
    Editor=LevelDesign(screen)
    pygame.display.set_caption(f'Editeur de Niveau v{Editor.version}')
    Editor.run = Editor.updateChecker.handle_crash(Editor.run,Editor)
    Editor.run()

