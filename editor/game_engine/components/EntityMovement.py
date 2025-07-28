class EntityMovement:
    def __init__(self, entity, clock):
        self.entity = entity
        self.clock = clock
        self.velocity_x = 0  # Vitesse horizontale
        self.acceleration = 1  # Accélération de base
        self.max_speed = entity.speed * 2  # Vitesse maximale
        self.default_friction = 0.5  # Friction par défaut
        self.friction = self.default_friction  # Friction actuelle

        self.is_dashing = False
        self.dash_speed = 15
        self.dash_duration = 170  # Durée du dash en ms
        self.dash_timer = 0
        self.dash_cooldown = 510  # Cooldown en ms
        self.dash_cooldown_timer = 0
        self.external_forces = []


    def add_force(self, force_x,force_y, duration_ms=None):
        self.entity.physics.add_vertical_force(force_y,duration_ms)
        self.external_forces.append({
            'force_x': force_x,
            'duration': duration_ms
        })

    def clear_forces(self):
        self.entity.physics.clear_forces()
        self.external_forces.clear()
        self.velocity_x = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0

    def _apply_external_forces(self, dt):
        total_force = 0
        forces_to_keep = []
        for f in self.external_forces:
            total_force += f['force_x']
            if f['duration'] is not None:
                f['duration'] -= dt
                if f['duration'] > 0:
                    forces_to_keep.append(f)
            else:
                forces_to_keep.append(f)
        self.external_forces = forces_to_keep
        self.velocity_x += total_force * (dt / 17)

    def move_right(self):
        """Déplacement vers la droite"""
        dt_factor = self.clock.get_time() / 17  # Facteur basé sur 17 ms par frame
        self.velocity_x += self.acceleration * dt_factor
        self.velocity_x = min(self.velocity_x, self.max_speed)

    def move_left(self):
        dt_factor = self.clock.get_time() / 17
        self.velocity_x -= self.acceleration * dt_factor
        self.velocity_x = max(self.velocity_x, -self.max_speed)

    def dash(self):
        if not self.is_dashing and self.dash_cooldown_timer <= 0 and not self.entity.collisions.OnGround():
            self.is_dashing = True
            self.dash_timer = self.dash_duration  # Timer en ms
            self.dash_cooldown_timer = self.dash_cooldown  # Timer en ms
            if self.entity.direction == "right":
                self.velocity_x = self.dash_speed
            else:
                self.velocity_x = -self.dash_speed

    def applyFriction(self):
        surface_type = self.entity.collisions.getSurfaceType()

        # Adapter la friction selon la surface
        if surface_type == "ice":
            self.friction = 0.1
        elif surface_type == "sand":
            self.friction = 0.9
        else:
            self.friction = self.default_friction

        dt_factor = self.clock.get_time() / 17
        # Appliquer la friction (uniquement si on n'est pas en dash)
        if not self.is_dashing:
            if self.velocity_x > 0:
                self.velocity_x -= self.friction * dt_factor
                if self.velocity_x < 0:
                    self.velocity_x = 0
            elif self.velocity_x < 0:
                self.velocity_x += self.friction * dt_factor
                if self.velocity_x > 0:
                    self.velocity_x = 0

    def update(self):
        dt = self.clock.get_time()
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        self._apply_external_forces(dt)
        self.applyFriction()
        self.entity.rect.x += self.velocity_x * (dt / 17)
