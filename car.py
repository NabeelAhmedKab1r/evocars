# car.py

import math
import pygame
from config import (
    DT, MAX_SPEED, ACCEL, FRICTION, TURN_RATE,
    CAR_WIDTH, CAR_LENGTH, SCREEN_WIDTH, SCREEN_HEIGHT, CAR_COLOR,
    RAY_ANGLES, MAX_RAY_DIST
)


class Car:
    def __init__(self, x, y, angle):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)  # radians
        self.speed = 0.0
        self.alive = True
        self.checkpoint_index = 0

    def update(self, steer, throttle, track, dt=DT):
        if not self.alive:
            return

        self.speed += throttle * ACCEL * dt

        if self.speed > 0:
            self.speed -= FRICTION
            if self.speed < 0:
                self.speed = 0
        elif self.speed < 0:
            self.speed += FRICTION
            if self.speed > 0:
                self.speed = 0

        self.speed = max(-0.5 * MAX_SPEED, min(MAX_SPEED, self.speed))
        self.angle += steer * TURN_RATE * dt

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        car_rect = pygame.Rect(0, 0, CAR_WIDTH, CAR_LENGTH)
        car_rect.center = (self.x, self.y)

        for w in track.walls:
            if car_rect.colliderect(w):
                self.alive = False
                return

        if (self.x < 0 or self.x > SCREEN_WIDTH or
                self.y < 0 or self.y > SCREEN_HEIGHT):
            self.alive = False
            return

        if self.checkpoint_index < len(track.checkpoints):
            cx, cy = track.checkpoints[self.checkpoint_index]
            if (self.x - cx) ** 2 + (self.y - cy) ** 2 < (25 ** 2):
                self.checkpoint_index += 1

    # ------------------------------------------------------------------
    #  Raycasting
    # ------------------------------------------------------------------

    def get_raycasts(self, track):
        """Return normalised ray distances [0, 1] for each RAY_ANGLES entry."""
        return [
            self._cast_ray(self.angle + math.radians(deg), track.walls) / MAX_RAY_DIST
            for deg in RAY_ANGLES
        ]

    def _cast_ray(self, angle, walls):
        """AABB slab intersection — returns distance to nearest wall."""
        ox, oy = self.x, self.y
        dx = math.cos(angle)
        dy = math.sin(angle)
        min_dist = MAX_RAY_DIST

        for rect in walls:
            # Slab test on x axis
            if dx != 0:
                tx1 = (rect.left - ox) / dx
                tx2 = (rect.right - ox) / dx
                txn, txx = min(tx1, tx2), max(tx1, tx2)
            else:
                txn, txx = -math.inf, math.inf

            # Slab test on y axis
            if dy != 0:
                ty1 = (rect.top - oy) / dy
                ty2 = (rect.bottom - oy) / dy
                tyn, tyx = min(ty1, ty2), max(ty1, ty2)
            else:
                tyn, tyx = -math.inf, math.inf

            tmin = max(txn, tyn)
            tmax = min(txx, tyx)

            if tmax >= max(tmin, 0.0):
                dist = max(tmin, 0.0)
                if dist < min_dist:
                    min_dist = dist

        return min_dist

    def draw_rays(self, surface, track):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for deg in RAY_ANGLES:
            angle = self.angle + math.radians(deg)
            dist  = self._cast_ray(angle, track.walls)
            end_x = self.x + math.cos(angle) * dist
            end_y = self.y + math.sin(angle) * dist
            hit   = dist < MAX_RAY_DIST - 1

            line_color = (255, 130, 50, 35) if hit else (60, 190, 255, 18)
            pygame.draw.line(overlay, line_color,
                             (int(self.x), int(self.y)),
                             (int(end_x), int(end_y)), 1)
            if hit:
                pygame.draw.circle(overlay, (255, 150, 70, 160),
                                   (int(end_x), int(end_y)), 2)
        surface.blit(overlay, (0, 0))

    def draw(self, surface, color=CAR_COLOR):
        ang  = self.angle
        size = 11
        ix, iy = int(self.x), int(self.y)

        p1 = (self.x + math.cos(ang) * size,
              self.y + math.sin(ang) * size)
        p2 = (self.x + math.cos(ang + 2.5) * size * 0.65,
              self.y + math.sin(ang + 2.5) * size * 0.65)
        p3 = (self.x + math.cos(ang - 2.5) * size * 0.65,
              self.y + math.sin(ang - 2.5) * size * 0.65)

        # Layered neon glow (large → small, transparent → opaque)
        glow = pygame.Surface((64, 64), pygame.SRCALPHA)
        for r, a in [(30, 15), (22, 30), (15, 55), (9, 100)]:
            pygame.draw.circle(glow, (*color, a), (32, 32), r)
        surface.blit(glow, (ix - 32, iy - 32))

        # Car body
        pygame.draw.polygon(surface, color, [p1, p2, p3])
        # Bright highlight at the nose
        pygame.draw.circle(surface, (220, 255, 255), (int(p1[0]), int(p1[1])), 2)
