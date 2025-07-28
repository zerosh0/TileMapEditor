import pygame
from editor.game_engine.core.level import Level


class CollisionManager:
    def __init__(self, level: Level,entity):
        self.level = level
        self.entity=entity
        self.groundThreshold=1
        self.wallThreshold=1
        self.frontHitBoxThreshold=50

    def check(self):
        for rect in self.level.get_scaled_collision_rects():
            if self.entity.rect.colliderect(rect):
                return rect
        return None
    
    def checkWithByName(self,name):
        for rect in self.level.get_scaled_collision_rects():
            if rect.name==name and self.entity.rect.colliderect(rect):
                return True
        return False

    def OnGround(self):
        for Collisionrect in self.level.get_scaled_collision_rects():
            rect = Collisionrect.rect
            lowered_rect = self.entity.rect.copy()
            lowered_rect.bottom += self.groundThreshold
            if Collisionrect.type=="collision" and lowered_rect.colliderect(rect) and self.entity.rect.top<rect.top:
                    return True
        return False
    
    def OnWall(self):
        for Collisionrect in self.level.get_scaled_collision_rects():
            rect = Collisionrect.rect
            # Vérification pour une collision sur le côté gauche
            leftRect= self.entity.rect.copy()
            leftRect.x-=self.wallThreshold
            if Collisionrect.type=="collision" and leftRect.colliderect(rect) and self.entity.rect.right > rect.left:
                return True
            # Vérification pour une collision sur le côté droit
            rightRect= self.entity.rect.copy()
            rightRect.x+=self.wallThreshold
            if Collisionrect.type=="collision" and rightRect.colliderect(rect) and self.entity.rect.left < rect.right:
                return True
        return False


    def FrontCollide(self,rects,direction,threshold=None):
        threshold=self.frontHitBoxThreshold if threshold is None else threshold
        FrontHitBox=self.entity.rect.copy()
        FrontHitBox.y-=7
        if direction=="right":
            FrontHitBox.x+=threshold
        elif direction=="left":
            FrontHitBox.x-=threshold
        else:
            raise Exception(f"direction non reconnue pour {self.entity}")
        for rect in rects:
            if FrontHitBox.colliderect(rect):
                return rect,FrontHitBox
        return None,FrontHitBox
    

    def ProjectileCollide(self,direction,height,y,range,EntityRect):
        direction = self.entity.rect.left-range if direction=="left" else self.entity.rect.right
        ProjectileRect=pygame.Rect(direction,self.entity.rect.top-y,range,height)
        return ProjectileRect.colliderect(EntityRect),ProjectileRect
        

    def getSurfaceType(self):
        for Collisionrect in self.level.get_scaled_collision_rects():
            rect = Collisionrect.rect
            lowered_rect = self.entity.rect.copy()
            lowered_rect.bottom += self.groundThreshold
            if lowered_rect.colliderect(rect) and self.entity.rect.top<rect.top:
                    return Collisionrect.type

    def update(self):
        self.Process()
        self.execute()

    def execute(self):
        for Collisionrect in self.level.scaled_collision_rects:
            rect = Collisionrect.rect
            if Collisionrect.graph is not None:
                if self.entity.rect.colliderect(rect):
                    if Collisionrect.collide==False:
                        Collisionrect.collide=True
                        enter=Collisionrect.graph.events.get("on_enter")
                        if enter:
                            Collisionrect.graph.run_logic_from_event(enter)
                    overlap=Collisionrect.graph.events.get("on_overlap")
                    if overlap:
                        Collisionrect.graph.run_logic_from_event(overlap)  
                elif Collisionrect.collide==True:
                    Collisionrect.collide=False
                    exit=Collisionrect.graph.events.get("on_exit")
                    if exit:
                            Collisionrect.graph.run_logic_from_event(exit)


    def Process(self):
        """Corrige la position de l'entité en cas de collision avec un objet"""
        for Collisionrect in self.level.get_scaled_collision_rects():
            rect = Collisionrect.rect
            if Collisionrect.type=="collision" and self.entity.rect.colliderect(rect):  # Vérifie si l'entité entre en collision
                delta_left = abs(self.entity.rect.left - rect.right)
                delta_right = abs(rect.left - self.entity.rect.right)
                delta_top = abs(self.entity.rect.top - rect.bottom)
                delta_bottom = abs(rect.top - self.entity.rect.bottom)
                min_delta = min(delta_left, delta_right, delta_top, delta_bottom)

                # Correction de la position selon la collision la plus proche
                if min_delta == delta_bottom:
                    self.entity.rect.bottom = rect.top  # Collision avec le bas
                elif min_delta == delta_top:
                    self.entity.rect.top = rect.bottom  # Collision avec le haut
                elif min_delta == delta_right:
                    self.entity.rect.right = rect.left  # Collision avec la droite
                elif min_delta == delta_left:
                    self.entity.rect.left = rect.right  # Collision avec la gauche



