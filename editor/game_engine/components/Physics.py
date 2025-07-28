
class PhysicsObject:
    def __init__(self, entity, clock, gravity=0.6, jump_strength=-15, coyote_time=10, jump_buffer=10):
        self.entity = entity
        self.clock = clock
        self.gravity = gravity
        self.jump_strength = jump_strength
        self.y_velocity = 0
        self.is_jumping = False
        self.current_jump_animation = ""
        self.jump_start_y = None

        # Coyote Time & Buffer Input
        self.coyote_time = coyote_time
        self.coyote_timer = 0
        self.jump_buffer = jump_buffer
        self.buffer_timer = 0

        # Wall Slide & Wall Jump
        self.is_wall_sliding = False
        self.wall_slide_speed = 4
        self.wall_jump_strength = -8
        self.external_forces = []

        self.fall_buffer = 20
        self.fall_timer = 0

    def clear_forces(self):
        self.external_forces.clear()
        self.y_velocity = 0
        self.buffer_timer = 0
        self.coyote_timer = 0
        self.is_jumping = False

    def add_vertical_force(self, force_y, duration_ms=None):
        self.external_forces.append({
            'force_y': force_y,
            'duration': duration_ms
        })

    def _apply_external_forces(self, dt):
        total_fy = 0
        remaining = []
        for f in self.external_forces:
            total_fy += f['force_y']
            if f['duration'] is not None:
                f['duration'] -= dt
                if f['duration'] > 0:
                    remaining.append(f)
            else:
                remaining.append(f)
        self.external_forces = remaining
        factor = min(dt / 17, 2.0)
        self.y_velocity += total_fy * factor

    def jump(self, animation_name):
        if self.entity.collisions.OnGround() and not self.is_jumping:
            self.current_jump_animation = animation_name
            self.buffer_timer = self.jump_buffer

    def update(self):
        if self.entity.fly_mode:
            return

        dt_ms = self.clock.get_time()
        dt_factor = min(dt_ms / 17, 2.0)
        remaining = []
        total_force_y = 0
        for f in self.external_forces:
            total_force_y += f['force_y']
            if f['duration'] is None or f['duration'] > dt_ms:
                # réduit la durée restante si applicable
                if f['duration'] is not None:
                    f['duration'] -= dt_ms
                remaining.append(f)
        self.external_forces = remaining
        a_total = self.gravity + total_force_y
        self.y_velocity += a_total * dt_factor

        if self.is_wall_sliding:
            self.y_velocity = min(self.y_velocity, self.wall_slide_speed)


        if (
            self.is_jumping
            and self.jump_start_y is not None
            and self.entity.rect.y > self.jump_start_y
            and not self.entity.collisions.OnGround()
            and hasattr(self.entity, "animation")
            and self.entity.animation.current_animation == "idle"
        ):
            self.is_jumping = False
            self.fall_timer = 0

        self.entity.rect.y += self.y_velocity * dt_factor
        if self.entity.collisions.OnGround():
            self.y_velocity = 0
            self.coyote_timer = self.coyote_time
            self.is_jumping = False
        else:
            self.coyote_timer = max(self.coyote_timer - 1, 0)

        if self.buffer_timer > 0:
            self.buffer_timer -= 1
        if (self.buffer_timer > 0
            and (self.coyote_timer > 0 or self.is_wall_sliding)
            and not self.is_jumping):
            self.performJump()
            self.buffer_timer = 0
        

        is_falling = (
            not self.entity.collisions.OnGround()
            and not self.is_jumping
            and self.y_velocity > 0
        )

        if is_falling:
            self.fall_timer += 1
            if self.fall_timer >= self.fall_buffer:
                if hasattr(self.entity, "animation"):
                    self.entity.animation.setAnimation("fall_slow")
        else:
            self.fall_timer = 0


    def performJump(self):
        """Exécute le saut et réinitialise l'animation pour qu'elle démarre au bon moment."""
        self.jump_start_y = self.entity.rect.y
        if self.entity.collisions.OnWall() and not self.entity.collisions.OnGround():
            self.wallJump()
        else:
            self.y_velocity = self.jump_strength
            self.is_jumping = True
            if hasattr(self.entity, "animation"):
                self.entity.animation.forceSetAnimation(self.current_jump_animation)


    def wallJump(self):
        """Permet un saut contre le mur."""
        direction = 1 if self.entity.direction == "right" else -1
        if self.is_wall_sliding:
            self.y_velocity = self.wall_jump_strength
            self.entity.movement.velocity_x = direction * self.entity.movement.dash_speed
            self.is_jumping = True
