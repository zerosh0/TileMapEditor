import traceback
import pygame
from pygame.locals import *
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from editor.ui.Font import FontManager
from editor.ui.Input import InputField
from editor.blueprint_editor.node import CATEGORY_ORDER, NODE_REGISTRY, Node,Pin
from editor.blueprint_editor.blueprints.b_events import *
from editor.blueprint_editor.blueprints.b_logic import *
from editor.blueprint_editor.blueprints.b_debug import *
from editor.blueprint_editor.blueprints.b_player import *
from editor.blueprint_editor.blueprints.b_input import *
from editor.blueprint_editor.blueprints.b_animations import *
from editor.blueprint_editor.blueprints.b_world import *
from editor.blueprint_editor.blueprints.b_audio import *
from editor.blueprint_editor.blueprints.b_others import *
from editor.blueprint_editor.blueprints.b_operators import *
from editor.blueprint_editor.blueprints.b_custom import *

#LevelGraph
class BlueprintEditor:

    def __init__(self,LevelEditor):
        self.LevelEditor=LevelEditor
        self.screen=self.LevelEditor.screen
        self.clock = pygame.time.Clock()
        self.offset = [0, 0]
        self.panning = False
        self.pan_start = (0, 0)
        self.nodes: List[Node] = []
        self.connections: List[Tuple[Pin, Pin]] = []
        self.connecting: Optional[Pin] = None
        self.selected: List[Node] = []
        self.delete_target: Optional[Node] = None
        self.start_node: Optional[Node] = None
        self.events = {}
        self.error_node: Optional[Node] = None
        self.error_message: str = ""
        self.delayed_tasks: List[Dict] = []

        self.show_menu = False
        self.menu_pos = (0,0)
        self.menu_height = 200
        self.menu_items: List[Tuple[pygame.Rect, Callable, str]] = []
        self.search_field = InputField(rect=(0,0,200,24), placeholder="Recherche…", on_change=lambda _: self._build_menu())
        self.menu_scroll = 0

        self.sidebar_width = 220
        self._build_sidebar()
        self.dragging_factory: Optional[Callable] = None
        self.sidebar_scroll = 0
        self.sidebar_visible = False
        self.toggle_rect = pygame.Rect(0, 0, 16, 64)

        self.running = True
        self.close_btn_size = 10
        self.close_btn_padding = 8
        self.variable_store: Dict[str, Any] = {}
        self.selecting = False
        self.selection_start = (0, 0)
        self.selection_rect = pygame.Rect(0, 0, 0, 0)
        self.dragging_selection = False
        self.drag_offset = {}





    def _build_sidebar(self):
        """Construit la liste des catégories + labels pour le panneau."""
        self.sidebar_items: List[Tuple[pygame.Rect, Callable, str]] = []
        font = FontManager().get(size=18)
        y = 20
        for cat in CATEGORY_ORDER:
            title_surf = font.render(cat, True, (200,200,200))
            self.sidebar_items.append(("header", title_surf, (10, y)))
            y += title_surf.get_height() + 6

            for label, (cls, _) in NODE_REGISTRY.items():
                if NODE_REGISTRY[label][1] != cat:
                    continue
                rect = pygame.Rect(10, y, self.sidebar_width - 20, 20)
                def make_factory(c=cls):
                    return lambda pos: c(pos, self, properties={})
                self.sidebar_items.append(("item", rect, make_factory(), label))
                y += 24
            y += 10


    def _build_menu(self):
        self.menu_scroll = 0
        self.menu_items.clear()
        q = self.search_field.text.lower()
        x0, y0 = self.menu_pos
        y = y0 + 45


        grouped: Dict[str, List[Tuple[str, Type[Node]]]] = {}
        for label, (cls, cat) in NODE_REGISTRY.items():
            #print(cat,label)
            if q in label.lower():
                grouped.setdefault(cat, []).append((label, cls))


        for cat in CATEGORY_ORDER:
            items = grouped.get(cat)
            if not items:
                continue

            font = FontManager().get(size=20)
            text_surf = font.render(cat, True, (200,200,200))
            self.menu_items.append(("header", text_surf, (x0+10, y)))
            y += text_surf.get_height() + 4


            for label, cls in items:
                rect = pygame.Rect(x0+10, y, 180, 24)
                def make_factory(c):
                    return lambda: c((self.menu_pos[0] + self.offset[0],
                                    self.menu_pos[1] + self.offset[1]), self,properties={})
                factory = make_factory(cls)
                self.menu_items.append(("item", rect, factory, label))
                y += 26


        total_h   = y - (y0 + 10)
        visible_h = self.menu_height - 20
        self.max_scroll = max(0, total_h - visible_h)

        
    def delete_node(self, node: Node):
        new_connections = []
        for out_p, in_p in self.connections:
            if out_p.node is node or in_p.node is node:
                out_p.disconnect()
            else:
                new_connections.append((out_p, in_p))
        self.connections = new_connections

        if node.is_event:
            self.events.pop(node.title, None)
        if node in self.nodes:
            self.nodes.remove(node)
        if node in self.selected:
            self.selected.remove(node)

    def set_start(self, node: Node):
        self.start_node = node

    def add_node(self, node: Node):
        if not node:
            return
        if node.is_event:
            if node.title in self.events:
                print(f"{node.title} déjà présente !")
                self.LevelEditor.nm.notify('warning', 'Attention',
                           f'L\'évènement {node.title} existe déjà !', duration=1.5)
                return
            self.events[node.title]=node
        self.nodes.append(node)

    def start_connection(self, pin: Pin):
        if pin.connection:
            self.connections = [
                (o, i) for (o, i) in self.connections
                if o is not pin and i is not pin
            ]
            pin.disconnect()
        self.connecting = pin


    def finish_connection(self, target_pin: Pin):
        src = self.connecting
        dst = target_pin
        if src and src.connection:
            src.disconnect()
        if dst.connection:
            dst.disconnect()
        self.connections = [
            (o, i) for (o, i) in self.connections
            if o not in (src, dst) and i not in (src, dst)
        ]
        if src and src.is_output != dst.is_output and src.pin_type == dst.pin_type:
            # on assure que out_p est bien le output
            out_p, in_p = (src, dst) if src.is_output else (dst, src)
            out_p.connect(in_p)
            self.connections.append((out_p, in_p))
        self.connecting = None



    def _reset_flipflops(self):
        for node in self.nodes:
            if isinstance(node, FlipFlopNode):
                node.properties["state"] = 0
                node.properties["last"]  = "A"

    def _reset_once_nodes(self):
        for node in self.nodes:
            if isinstance(node, OnceNode):
                node.properties["triggered"] = False

    def run_logic_from_event(self, event_node: Node):

            context = {}
            queue: List[Dict] = [{"node": event_node, "context": dict(context)}]

            while queue:
                item = queue.pop(0)
                node = item["node"]
                context = item["context"]
                try:
                    next_node = node.execute(context)

                    if isinstance(node, ForNode):
                        count = node._get_count(context)
                        loop_pin = next(p for p in node.outputs if p.name=="loop")
                        body_start = loop_pin.connection.node if loop_pin.connection else None

                        for i in range(count):
                            node.properties['index'] = i
                            sub = body_start
                            while sub:
                                context['properties'] = sub.properties
                                sub = sub.execute(context)

                        node.properties['index'] = 0
                        next_pin = next(p for p in node.outputs if p.name=="next")
                        if next_pin.connection:
                            queue.insert(0, {
                                "node": next_pin.connection.node,
                                "context": dict(context)
                            })

                    else:
                        if next_node:
                            queue.insert(0, {"node": next_node, "context": dict(context)})
                except Exception as e:
                    full_tb = traceback.format_exception(type(e), e, e.__traceback__)
                    snippet = ''.join(full_tb[-2:]).strip()
                    self.handle_node_error(node, snippet)
                    break

    def process_delayed_tasks(self):
        now = pygame.time.get_ticks()
        ready = [t for t in self.delayed_tasks if t["resume_at"] <= now]
        for task in ready:
            node = task["node"]
            context = task["context"]
            out_pin = next(p for p in node.outputs if p.name=="done")
            if out_pin.connection:
                next_node = out_pin.connection.node
                self.run_logic_from_event(next_node)
            self.delayed_tasks.remove(task)


    def clear_error(self):
        if self.error_node is not None:
            self.error_node = None
            self.error_message = ""
            for n in self.nodes:
                setattr(n, 'has_error', False)

    def handle_node_error(self, node: Optional[Node], exception: Exception):
        if node is None:
            return
        self.error_node = node
        self.error_message = str(exception)
        setattr(node, 'has_error', True)
        sw, sh = self.screen.get_size()
        self.offset[0] = node.x - sw//2 + Node.WIDTH//2
        self.offset[1] = node.y - sh//2 + node.height//2
        self.LevelEditor.nm.notify('error', 'Erreur d\'exécution',
                                   f"{node.title}: {self.error_message}", duration=6.0)
        self.run()

    def get_mouse_button(self,e):
        if e.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            if e.button == 2:
                return 2
            if e.button == 1 and (pygame.key.get_mods() & KMOD_ALT):
                return 2
            return e.button
        return None


    def run_logic(self, context: Dict[str, Any]):
        node = self.start_node
        while node:
            # on injecte les propriétés du node dans le contexte
            context['properties'] = node.properties
            node = node.execute(context)
                
    def handle_event(self, e: pygame.event.Event):
            mx, my = pygame.mouse.get_pos()
            for n in self.nodes:
                n.handle_event(e)

            # Copier (Ctrl+C)
            if e.type == KEYDOWN and e.key == K_c and (e.mod & KMOD_CTRL):
                # on ne copie que si on a au moins un nœud sélectionné
                if not self.selected:
                    return

                # construire la liste de nœuds et leur index
                node_list = list(self.selected)
                idx_map   = {node: i for i, node in enumerate(node_list)}

                # données simples des nœuds
                nodes_data = []
                ox, oy = self.offset
                for node in node_list:
                    nodes_data.append({
                        'cls':  type(node),
                        'props': dict(node.properties),
                        # position *relative* au point d'ancrage (ici (0,0) de l'éditeur)
                        'pos': (node.x - ox, node.y - oy)
                    })

                # connexions internes
                conns_data = []
                for out_p, in_p in self.connections:
                    n0, n1 = out_p.node, in_p.node
                    if n0 in idx_map and n1 in idx_map:
                        conns_data.append({
                            'src_idx':   idx_map[n0],
                            'src_pin':   out_p.name,
                            'dst_idx':   idx_map[n1],
                            'dst_pin':   in_p.name
                        })

                # stocker dans le niveau
                self.LevelEditor.clipboard = {
                    'nodes':  nodes_data,
                    'conns':  conns_data
                }
                return


            # Coller (Ctrl+V)
            # Coller (Ctrl+V), centré sur le curseur
            if e.type == KEYDOWN and e.key == K_v and (e.mod & KMOD_CTRL):
                cb = getattr(self.LevelEditor, 'clipboard', None)
                if not cb or not cb.get('nodes'):
                    return

                mx, my = pygame.mouse.get_pos()
                ox, oy = self.offset

                # 1) Calcul du centre de la sélection d’après les positions relatives
                xs = [px for data in cb['nodes'] for px, _ in [data['pos']]]
                ys = [py for data in cb['nodes'] for _, py in [data['pos']]]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2

                new_nodes = []
                # 2) Recréer chaque nœud en décalant par rapport au centre
                for data in cb['nodes']:
                    cls    = data['cls']
                    props  = dict(data['props'])
                    px, py = data['pos']
                    # on retire le centre pour récentrer
                    adj_x = px - center_x
                    adj_y = py - center_y
                    node  = cls((mx + ox + adj_x, my + oy + adj_y), self, properties=props)
                    self.add_node(node)
                    new_nodes.append(node)

                # 3) Refaire les connexions internes
                for c in cb['conns']:
                    src_node = new_nodes[c['src_idx']]
                    dst_node = new_nodes[c['dst_idx']]

                    out_pin = next((p for p in src_node.outputs if p.name == c['src_pin']), None)
                    in_pin  = next((p for p in dst_node.inputs  if p.name == c['dst_pin']), None)
                    if out_pin and in_pin:
                        out_pin.connect(in_pin)
                        self.connections.append((out_pin, in_pin))

                # 4) Sélectionner les nouveaux nœuds
                self.selected = new_nodes
                return


            if e.type == KEYDOWN and e.key == K_h:
                if self.selected:
                    node = self.selected[0]
                    query = getattr(node, 'title', node.__class__.__name__)
                    self.LevelEditor.doc.help(query)
                return

            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if hasattr(self, 'close_btn_rect') and self.close_btn_rect.collidepoint((mx, my)):
                    self.running = False
                    return
            if e.type == MOUSEBUTTONDOWN and e.button == 1 and self.sidebar_visible:
                tri_area = pygame.Rect(self.sidebar_width - 10, self.screen.get_height()//2 - 20, 20, 40)
                if tri_area.collidepoint((mx, my)):
                    self.sidebar_visible = False
                    return
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if not self.sidebar_visible and self.toggle_rect.collidepoint((mx, my)):
                    self.sidebar_visible = True
                    return

            if e.type == MOUSEWHEEL and pygame.mouse.get_pos()[0] < self.sidebar_width:
                # on déplace de 20 pixels par cran
                self.sidebar_scroll = max(0, self.sidebar_scroll - e.y * 20)
                return

            btn = self.get_mouse_button(e)
            if e.type == MOUSEBUTTONDOWN and btn == 2:
                self.panning = True
                self.pan_start = (mx, my)
                return
            elif e.type == MOUSEBUTTONUP and btn == 2:
                self.panning = False
                return
            elif e.type == MOUSEMOTION and self.panning:
                dx, dy = mx - self.pan_start[0], my - self.pan_start[1]
                self.offset[0] -= dx
                self.offset[1] -= dy
                self.pan_start = (mx, my)
                return

            if e.type == MOUSEBUTTONDOWN and e.button == 1 and self.sidebar_visible and mx < self.sidebar_width:
                for entry in self.sidebar_items:
                    if entry[0] != "item":
                        continue
                    _, rect, factory, label = entry
                    rect_scrolled = rect.move(0, -self.sidebar_scroll)
                    if rect_scrolled.collidepoint((mx, my)):
                        self.dragging_factory = factory
                        return

                    
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                for n in self.nodes:
                    for pin in n.inputs + n.outputs:
                        if (mx - pin.pos[0])**2 + (my - pin.pos[1])**2 < Pin.RADIUS**2:
                            self.start_connection(pin)


            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                # on ne veut pas démarrer de cadre si :
                # - on est sur un pin, 
                # - on drague un seul noeud (cf. plus bas),
                # - le menu est ouvert
                if not self.show_menu and not self.connecting:
                    # calculer si on clique sur un noeud
                    mx, my = e.pos
                    ox, oy = self.offset
                    over_node = any(
                        pygame.Rect(n.x-ox, n.y-oy, Node.WIDTH, n.height).collidepoint((mx,my))
                        for n in self.nodes
                    )
                    if not over_node:
                        self.selecting = True
                        self.selection_start = (mx, my)
                        self.selection_rect = pygame.Rect(mx, my, 0, 0)
                        self.selected.clear()
                        # on continue vers les autres conditions (ne pas return)

            if e.type == MOUSEMOTION and self.selecting:
                mx, my = e.pos
                x0, y0 = self.selection_start
                self.selection_rect.x = min(x0, mx)
                self.selection_rect.y = min(y0, my)
                self.selection_rect.width  = abs(mx - x0)
                self.selection_rect.height = abs(my - y0)
                return  # on stoppe là pour ne pas interférer


            if e.type == MOUSEBUTTONUP and e.button == 1 and self.selecting:
                # on sélectionne tous les nodes dans le cadre
                ox, oy = self.offset
                for n in self.nodes:
                    nr = pygame.Rect(n.x-ox, n.y-oy, Node.WIDTH, n.height)
                    if self.selection_rect.colliderect(nr):
                        self.selected.append(n)
                self.selecting = False
                return

            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                # si on clique dans un noeud déjà sélectionné ET qu'on a plusieurs
                mx, my = e.pos
                ox, oy = self.offset
                for n in self.selected:
                    nr = pygame.Rect(n.x-ox, n.y-oy, Node.WIDTH, n.height)
                    if nr.collidepoint((mx,my)) and len(self.selected) > 1:
                        # on passe en mode drag de sélection
                        self.dragging_selection = True
                        # calculer les offsets de chaque node
                        self.drag_offset = {
                            node: (node.x - (mx+ox), node.y - (my+oy))
                            for node in self.selected
                        }
                        return

            if e.type == MOUSEMOTION and self.dragging_selection:
                mx, my = e.pos
                ox, oy = self.offset
                for node, (dx, dy) in self.drag_offset.items():
                    node.x = mx + ox + dx
                    node.y = my + oy + dy
                return

            if e.type == MOUSEBUTTONUP and e.button == 1 and self.dragging_selection:
                self.dragging_selection = False
                return


            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                self.selected.clear()
                for node in reversed(self.nodes):
                    ox, oy = self.offset
                    node_rect = pygame.Rect(node.x-ox, node.y-oy, Node.WIDTH, node.height)
                    if node_rect.collidepoint(e.pos):
                        self.selected.append(node)
                        break
            if e.type == KEYDOWN and e.key == K_DELETE:
                for node in list(self.selected):
                    self.delete_node(node)

            if e.type == MOUSEBUTTONDOWN and e.button == 3:
                mx, my = e.pos
                ox, oy = self.offset

                # 1) est-ce sur un nœud ? → petit menu Supprimer
                for node in reversed(self.nodes):
                    node_rect = pygame.Rect(node.x-ox, node.y-oy, Node.WIDTH, node.height)
                    if node_rect.collidepoint((mx, my)):
                        self.show_menu = True
                        self.delete_target = node
                        # on définit un seul item "Supprimer" sans barre de recherche
                        self.menu_pos = (mx, my)
                        self.menu_items = [ 
                            ( pygame.Rect(mx, my, 120, 24),
                            lambda n=node: self.delete_node(n),
                            "Supprimer" ) 
                        ]
                        return

                # 2) sinon → menu classique de création
                self.delete_target = None
                self.show_menu = True
                self.search_field.active = True
                self.menu_pos = (mx, my)
                self.search_field.rect.topleft = (mx+10, my+10)
                self.search_field.text = ""
                self.menu_scroll = 0
                self._build_menu()
                return
            if e.type == KEYDOWN and e.key == K_RETURN and self.start_node:
                self.run_logic({})
                return
            if e.type==MOUSEBUTTONDOWN and e.button==3:
                self.show_menu = not self.show_menu
                self.menu_pos = e.pos
                if self.show_menu:
                    self.search_field.rect.topleft = (e.pos[0]+10, e.pos[1]+10)
                    self.search_field.text = ""
                    self.menu_scroll = 0
                    self.search_field.active = True
                    self._build_menu()
                return  
            if e.type == MOUSEBUTTONUP and e.button == 1 and self.dragging_factory:
                # n’ajoute que si on lâche hors du sidebar
                if mx > self.sidebar_width:
                    # centre le nœud sur le curseur
                    x = mx + self.offset[0] - Node.WIDTH  // 2
                    y = my + self.offset[1] - Node.HEIGHT // 2
                    node = self.dragging_factory((x, y))
                    self.add_node(node)
                self.dragging_factory = None
                return
            elif e.type == MOUSEBUTTONUP and e.button == 1 and self.connecting:
                mx, my = pygame.mouse.get_pos()

                for n in self.nodes:
                    for pin in n.inputs + n.outputs:
                        if (mx - pin.pos[0])**2 + (my - pin.pos[1])**2 < Pin.RADIUS**2:
                            self.finish_connection(pin)
                            return
                self.show_menu = True
                self.menu_pos = (mx, my)
                self.search_field.rect.topleft = (mx+10, my+10)
                self.search_field.text = ""
                self.search_field.active = True
                self.menu_scroll = 0
                self._build_menu()
            if self.show_menu:
                self.search_field.handle_event(e)
                if e.type==MOUSEWHEEL:
                    new_scroll = self.menu_scroll - e.y * 20
                    self.menu_scroll = max(0, min(new_scroll, self.max_scroll))
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if self.show_menu and self.delete_target:
                    rect, action, label = self.menu_items[0]
                    if rect.collidepoint(e.pos):
                        action()               # supprime le node
                        self.show_menu = False
                        self.delete_target = None
                        return
                if self.show_menu and self.search_field.rect.collidepoint(e.pos):
                    return
                if not self.show_menu:
                    return
                for entry in self.menu_items:
                    if entry[0] != "item":
                        continue
                    _, rect, factory, label = entry
                    draw_r = rect.move(0, -self.menu_scroll)
                    if draw_r.collidepoint(e.pos):
                        node = factory()
                        self.add_node(node)
                        # Raccroche automatique de la connexion
                        if self.connecting and node.inputs:
                            self.finish_connection(node.inputs[0])
                        self.connecting = False
                        self.show_menu = False
                        break
                else:
                    if self.show_menu:
                        self.connecting=False
                        self.show_menu=False


            return





    def draw(self):
        self.screen.fill((25, 25, 35))
        w, h = self.screen.get_size()
        step = 32
        for x in range(-self.offset[0] % step, w, step):
            pygame.draw.line(self.screen, (50,50,70), (x, 0), (x, h))
        for y in range(-self.offset[1] % step, h, step):
            pygame.draw.line(self.screen, (50,50,70), (0, y), (w, y))


        for out_p, in_p in self.connections:
            self._draw_bezier(out_p.pos, in_p.pos, (200,200,200))
        if self.connecting and not self.show_menu:
            self._draw_bezier(self.connecting.pos, pygame.mouse.get_pos(), (120,120,120))
        for n in self.nodes:
            n.draw(self.screen, n in self.selected)
        if self.error_node:
            font = FontManager().get(size=20)
            text_surf = font.render(self.error_message, True, (220, 50, 50))
            # fond semi-transparent
            bg = pygame.Surface((self.screen.get_width(), text_surf.get_height()+8),
                                flags=pygame.SRCALPHA)
            bg.fill((30, 0, 0, 180))
            self.screen.blit(bg, (0, self.screen.get_height() - bg.get_height()))
            self.screen.blit(text_surf,
                             (10, self.screen.get_height() - text_surf.get_height() - 4))

        if self.show_menu:
            if self.delete_target:
                rect, action, label = self.menu_items[0]
                pygame.draw.rect(self.screen, (40,40,40), rect, border_radius=4)
                pygame.draw.rect(self.screen, (120,120,120), rect, 1, border_radius=4)
                font = FontManager().get(size=18)
                self.screen.blit(font.render(label, True, (220,220,220)), (rect.x+8, rect.y+4))
            else:
                mw = 220 
                menu_rect = pygame.Rect(*self.menu_pos, mw, self.menu_height)
                pygame.draw.rect(self.screen, (30,30,30), menu_rect)
                pygame.draw.rect(self.screen, (80,80,80), menu_rect, 2)

                # items
                clip = self.screen.get_clip()
                scroll_area = pygame.Rect(self.menu_pos[0]+10,
                                        self.menu_pos[1]+10,
                                        200, self.menu_height-20)
                self.screen.set_clip(scroll_area)

                offset_y = self.menu_scroll
                for entry in self.menu_items:
                    if entry[0] == "header":
                        _, text_surf, (tx, ty) = entry
                        draw_pos = (tx, ty - offset_y)
                        self.screen.blit(text_surf, draw_pos)
                    else:
                        _, rect, factory, label = entry
                        draw_r = rect.move(0, -offset_y)
                        pygame.draw.rect(self.screen, (50,50,50), draw_r, border_radius=4)
                        txt = FontManager().get(size=18).render(label, True, (220,220,220))
                        self.screen.blit(txt, (draw_r.x+8, draw_r.y+4))
                self.screen.set_clip(clip)
                # barre de recherche
                self.search_field.draw(self.screen)

        if self.sidebar_visible:
            sidebar_rect = pygame.Rect(0, 0, self.sidebar_width, h)
            pygame.draw.rect(self.screen, (30,30,40), sidebar_rect)
            clip = self.screen.get_clip()
            self.screen.set_clip(sidebar_rect)
            for entry in self.sidebar_items:
                kind = entry[0]
                if kind == "header":
                    _, surf, (x, y) = entry
                    self.screen.blit(surf, (x, y - self.sidebar_scroll))
                else:
                    _, rect, _, label = entry
                    rect_scrolled = rect.move(0, -self.sidebar_scroll)
                    # background + hover
                    hover = rect_scrolled.collidepoint(pygame.mouse.get_pos())
                    bg_color = (60,60,80) if hover else (40,40,60)
                    pygame.draw.rect(self.screen, bg_color, rect_scrolled, border_radius=3)
                    txt = FontManager().get(size=16).render(label, True, (220,220,220))
                    self.screen.blit(txt, (rect_scrolled.x+6, rect_scrolled.y+2))
            self.screen.set_clip(None)
            tri = [
                (self.sidebar_width - 2, h//2 - 10),
                (self.sidebar_width - 2, h//2 + 10),
                (self.sidebar_width + 8, h//2),
            ]
            pygame.draw.polygon(self.screen, (60, 60, 80), tri)
        else:
            self.toggle_rect = pygame.Rect(0, h//2 - 32, 16, 64)
            pygame.draw.rect(self.screen, (30,30,40), self.toggle_rect)
            # flèche vers la droite
            tri = [
                (4,  h//2 - 12),
                (4,  h//2 + 12),
                (12, h//2),
            ]
            pygame.draw.polygon(self.screen, (60, 60, 80), tri)            

        # 2) Bouton Fermer
        bx = w - self.close_btn_size - self.close_btn_padding
        by = self.close_btn_padding
        self.close_btn_rect = pygame.Rect(bx, by, self.close_btn_size, self.close_btn_size)

        # Cercle de fond
        center = (bx + self.close_btn_size//2, by + self.close_btn_size//2)
        radius = self.close_btn_size // 2
        try:
            pygame.draw.aacircle(self.screen, (200, 71, 88), center, radius)
        except:
            pygame.draw.circle(self.screen, (200, 71, 88), center, radius)


        if self.dragging_factory:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        self.LevelEditor.nm.draw(self.screen)
        if self.selecting:
            pygame.draw.rect(self.screen, (100,200,250), self.selection_rect, 2)

        pygame.display.flip()

    def _draw_bezier(self, p0, p3, color):
        midx = (p0[0] + p3[0]) // 2
        pts = [
            (
                (1-t)**3 * p0[0] + 3*(1-t)**2 * t * midx + 3*(1-t) * t**2 * midx + t**3 * p3[0],
                (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p0[1] + 3*(1-t) * t**2 * p3[1] + t**3 * p3[1]
            )
            for t in [i/20 for i in range(21)]
        ]
        pygame.draw.aalines(self.screen, color, False, pts)

    def run(self):
        self.running = True
        while self.running:
            for e in pygame.event.get():
                if e.type == QUIT:
                    self.running = False
                else:
                    self.handle_event(e)
            dt=self.clock.tick(60)/1000
            self.LevelEditor.nm.update(dt)
            self.draw()
            
        # pygame.quit()


# if __name__ == "__main__":
#     editor = BlueprintEditor()

#     start = OnStart((50, 50), editor)
#     editor.add_node(start)
#     editor.set_start(start)
#     exit = OnEnter((50, 300), editor)
#     editor.add_node(exit)
#     overlap = OnExit((50, 550), editor)
#     editor.add_node(overlap)
#     # printer = PrintString((400, 50), editor)
#     # editor.add_node(printer)
#     # printer2 = PrintString((400, 300), editor)
#     # editor.add_node(printer2)
#     # start.outputs[0].connect(printer.inputs[0])
#     # editor.connections.append((start.outputs[0], printer.inputs[0]))
#     # printer.outputs[0].connect(printer2.inputs[0])
#     # editor.connections.append((printer.outputs[0], printer2.inputs[0]))
#     editor.run()