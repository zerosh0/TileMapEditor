import math


# Gravité simple (vers le bas)
def gravity(p, strength=0.1):
    p.vy += strength


# Attracteur (attire vers un point donné)
def attract(p, target_x, target_y, strength=0.2):
    dx = target_x - p.x
    dy = target_y - p.y
    dist = math.hypot(dx, dy) + 0.0001

    p.vx += (dx / dist) * strength
    p.vy += (dy / dist) * strength


# Répulseur (repousse depuis un point donné)
def repel(p, target_x, target_y, strength=1.0, radius=120):
    dx = p.x - target_x
    dy = p.y - target_y
    dist = math.hypot(dx, dy) + 0.0001

    if dist < radius:
        force = (radius - dist) / radius * strength
        p.vx += dx / dist * force
        p.vy += dy / dist * force


# Vent horizontal
def wind(p, strength=0.05):
    p.vx += strength


# Tourbillon (vortex)
def vortex(p, cx, cy, strength=0.5):
    dx = p.x - cx
    dy = p.y - cy
    p.vx += -dy * 0.01 * strength
    p.vy += dx * 0.01 * strength


# Frottement global (réduit la vitesse)
def global_friction(p, factor=0.98):
    p.vx *= factor
    p.vy *= factor
