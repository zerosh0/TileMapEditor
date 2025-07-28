from editor.animations.animation import AnimationManager
from editor.core.data_manager import DataManager
from editor.core.utils import Colors, Light, Tools
from editor.services.save_loader import SaveLoadManager
from editor.services.tilemap_opener import FileOpener
from editor.ui.DialogSystem import DialogBox
from editor.ui.Font import FontManager
from editor.ui.Notifications import NotificationManager
import sys
import traceback
import pygame


class DialogController:

    def __init__(self,screen,nm : NotificationManager,dataManager : DataManager,animations: AnimationManager,
                 TmapOpener : FileOpener,saveLoadManager : SaveLoadManager,clock):
          self.screen=screen
          self.nm=nm
          self.dataManager=dataManager
          self.animations=animations
          self.TmapOpener=TmapOpener
          self.saveLoadManager=saveLoadManager
          self.clock=clock

    def ask_confirmation(self, message,height=100):
            result = {'ok': False}

            def on_yes():
                result['ok'] = True
                dialog.active = False

            def on_no():
                dialog.active = False

            dialog = DialogBox(
                rect=(self.screen.get_width()/2 - 150, self.screen.get_height()/2 - 50, 300, height),
                title="Confirmation",
                description=message,
                buttons=[
                    {'text': 'Oui', 'callback': on_yes},
                    {'text': 'Non', 'callback': on_no},
                ],
                on_cancel=on_no
            )

            clock = pygame.time.Clock()
            bg = self.screen.copy()
            while dialog.active:
                dt = clock.tick(60) / 1000.0
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    dialog.handle_event(e)

                self.screen.blit(bg, (0, 0))
                dialog.draw(self.screen)
                pygame.display.flip()

            return result['ok']


    def ask_tile_params(self):
        result = {}

        def on_ok():
            try:
                name = dialog.inputs[0].text.strip()
                size = int(dialog.inputs[1].text)
                if name and size > 0:
                    result['name'] = name
                    result['size'] = size
                    dialog.active = False
            except ValueError:
                pass
        def on_cancel():
            dialog.active = False

        dialog = DialogBox(
            rect=(self.screen.get_width()/2-150,self.screen.get_height()/2-60,300,150),
            title="Paramètres TileMap",
            description="Entrez la taille des tiles et le nom de la map :",
            buttons=[{'text':'OK','callback':on_ok},
                    {'text':'Annuler','callback':on_cancel}],
            inputs=[{'placeholder':'Nom de la tile map','rules':[lambda ch:True]},
                    {'placeholder':'Taille des tiles','text':'16','rules':[str.isdigit]}],
            on_cancel=on_cancel
        )

        bg=self.screen.copy()
        while dialog.active:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                dialog.handle_event(e)
            self.screen.blit(bg,(0,0))
            dialog.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

        return result.get('size'), result.get('name')


    def CreateAnimation(self):
        result = {}

        def on_ok():
            name_txt, end_txt, speed_txt = dialog.inputs
            name = name_txt.text.strip()
            try:
                end = float(end_txt.text)
                speed = float(speed_txt.text)
            except ValueError:
                self.nm.notify('warning', 'Attention', 'La durée et la vitesse doivent être des nombres.', duration=1.5)
                return

            if not name:
                self.nm.notify('warning', 'Attention', 'Le nom ne peut pas être vide.', duration=1.5)
            elif end < 0.01:
                self.nm.notify('warning', 'Attention', 'La durée doit être ≥ 0.01s.', duration=1.5)
            elif end > 1000:
                self.nm.notify('warning', 'Attention', 'La durée doit être ≤ 1000s.', duration=1.5)
            elif speed <= 0:
                self.nm.notify('warning', 'Attention', 'La vitesse doit être > 0.', duration=1.5)
            else:
                result['name']  = name
                result['end']   = end
                result['speed'] = speed
                dialog.active = False

        def on_cancel():
            dialog.active = False

        font_manager = FontManager()
        dialog = DialogBox(
            rect=(self.screen.get_width()//2 - 125,
                self.screen.get_height()//2 - 112.5,
                250, 225),
            title="Nouvelle Animation",
            description="",
            buttons=[
                {'text': 'Créer',  'callback': on_ok},
            ],
            inputs=[
                {'label':'Nom :',      'placeholder':'idle', 'text':'', 'rules':[lambda ch: ch.isalnum() or ch=='_']},
                {'label':'Durée (s) :','placeholder':'1.0','text':'1.0','rules':[lambda ch: ch.isdigit() or ch=='.']},
                {'label':'Vitesse :',  'placeholder':'1.0','text':'1.0','rules':[lambda ch: ch.isdigit() or ch=='.']}
            ],
            on_cancel=on_cancel,
            font=font_manager.get(size=18)
        )

        bg = self.screen.copy()
        clock = pygame.time.Clock()
        while dialog.active:
            dt = clock.tick(60) / 1000.0
            self.nm.update(dt)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                dialog.handle_event(e)

            self.screen.blit(bg, (0,0))
            dialog.draw(self.screen)
            self.nm.draw(self.screen)
            pygame.display.flip()

        if 'name' in result:
            name  = result['name']
            end   = result['end']
            speed = result['speed']

            self.animations.create(name, end)
            anim = self.animations.get_current_anim()
            if anim:
                anim.speed = speed
                anim.timeline.compute_scale()

    def open_level(self):
        file_path=self.saveLoadManager.open(self)
        if not file_path:
            print("Aucune image sélectionnée.")
            self.nm.notify('info', 'Information', 'Aucune image sélectionnée.',duration=1.5)
            return
        self.TmapOpener.filepath=file_path
        try:
            self.TmapOpener.image = pygame.image.load(file_path).convert_alpha()
        except Exception as e:
            print("Erreur lors de l'ouverture du fichier !",Colors.RED,traceback.format_exc(),Colors.RESET)
            self.nm.notify('error', 'Erreur', "Erreur lors de l'ouverture de l'image !",duration=2)
            return
        
        tileSize, TileMapName = self.ask_tile_params()
        if not tileSize or not TileMapName:
            self.nm.notify('info', 'Information', 'Opération Annulée.', duration=1.0)
            return
        self.TmapOpener.processTileMap(tileSize, TileMapName)






    def EditColor(self,new_color):
        if self.dataManager.show_settings:
            return
        if self.dataManager.currentTool in [Tools.LocationPoint,Tools.Light]:
            self.dataManager.currentTool=Tools.Draw
        self.dataManager.currentTiles=[]
        self.dataManager.selectedElement.color = new_color

    def EditName(self):
        if self.dataManager.show_settings:
            return
        if self.dataManager.currentTool in [Tools.LocationPoint, Tools.Light]:
            self.dataManager.currentTool = Tools.Draw
        self.dataManager.currentTiles = []

        elem = self.dataManager.selectedElement
        if isinstance(elem, Light):
            result = {}

            def on_ok():
                text = dialog.inputs[0].text.strip()
                if text.isdigit():
                    radius = float(text)
                    if radius < 10_000:
                        if radius > 5:
                            result['radius'] = radius
                            dialog.active = False
                        else:
                            self.nm.notify('warning', 'Attention', 'Rayon trop petit.', duration=1.5)
                    else:
                        self.nm.notify('warning', 'Attention', 'Rayon trop grand.', duration=1.5)
                else:
                    self.nm.notify('warning', 'Attention', 'Le rayon doit être un nombre.', duration=1.5)

            def on_cancel():
                dialog.active = False

            dialog = DialogBox(
                rect=(
                    self.screen.get_width()/2-150,
                    self.screen.get_height()/2-50,
                    300, 120
                ),
                title="Modifier Rayon",
                description="Entrez le nouveau rayon de l'élément :",
                buttons=[
                    {'text': 'OK', 'callback': on_ok},
                    {'text': 'Annuler', 'callback': on_cancel}
                ],
                inputs=[{
                    'placeholder': 'Rayon (px)',
                    'text': str(round(elem.radius,1)),
                    'rules': [str.isdigit]
                }],
                on_cancel=on_cancel
            )

            bg = self.screen.copy()
            clock = pygame.time.Clock()
            while dialog.active:
                dt = clock.tick(60) / 1000.0
                self.nm.update(dt)
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    dialog.handle_event(e)
                self.screen.blit(bg, (0, 0))
                dialog.draw(self.screen)
                self.nm.draw(self.screen)
                pygame.display.flip()

            if 'radius' in result:
                elem.radius = result['radius']


        else:
            result = {}

            def on_ok():
                name = dialog.inputs[0].text.strip()
                if name:
                    result['name'] = name
                    dialog.active = False
                else:
                    self.nm.notify('warning', 'Attention', 'Le nom ne peut pas être vide.', duration=1.5)

            def on_cancel():
                dialog.active = False

            dialog = DialogBox(
                rect=(
                    self.screen.get_width()/2-150,
                    self.screen.get_height()/2-50,
                    300, 120
                ),
                title="Modifier Nom",
                description="Entrez le nouveau nom de l'élément :",
                buttons=[
                    {'text': 'OK', 'callback': on_ok},
                    {'text': 'Annuler', 'callback': on_cancel}
                ],
                inputs=[{
                    'placeholder': 'Nom',
                    'text': getattr(elem, 'name', ''),
                    'rules': [lambda ch: True]
                }],
                on_cancel=on_cancel
            )

            bg = self.screen.copy()
            clock = pygame.time.Clock()
            while dialog.active:
                dt = clock.tick(60) / 1000.0
                self.nm.update(dt)
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    dialog.handle_event(e)
                self.screen.blit(bg, (0, 0))
                dialog.draw(self.screen)
                self.nm.draw(self.screen)
                pygame.display.flip()

            if 'name' in result:
                elem.name = result['name']


    def EditType(self):
        if self.dataManager.show_settings:
            return

        if self.dataManager.currentTool in [Tools.LocationPoint, Tools.Light]:
            self.dataManager.currentTool = Tools.Draw
        self.dataManager.currentTiles = []

        elem = self.dataManager.selectedElement
        if isinstance(elem, Light):
            elem.blink = not elem.blink
        else:
            result = {}

            def on_ok():
                t = dialog.inputs[0].text.strip()
                if t:
                    result['type'] = t
                    dialog.active = False
                else:
                    self.nm.notify('warning', 'Attention', 'Le type ne peut pas être vide.', duration=1.5)

            def on_cancel():
                dialog.active = False

            dialog = DialogBox(
                rect=(
                    self.screen.get_width()/2-150,
                    self.screen.get_height()/2-50,
                    300, 120
                ),
                title="Modifier Type",
                description="Entrez le nouveau type de l'élément :",
                buttons=[
                    {'text': 'OK', 'callback': on_ok},
                    {'text': 'Annuler', 'callback': on_cancel}
                ],
                inputs=[{
                    'placeholder': 'Type',
                    'text': getattr(elem, 'type', ''),
                    'rules': [lambda ch: True]
                }],
                on_cancel=on_cancel
            )

            bg = self.screen.copy()
            clock = pygame.time.Clock()
            while dialog.active:
                dt = clock.tick(60) / 1000.0
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    dialog.handle_event(e)
                self.screen.blit(bg, (0, 0))
                dialog.draw(self.screen)
                pygame.display.flip()

            if 'type' in result:
                elem.type = result['type']

