# car.py

import math
import pygame
from config import (
    DT, MAX_SPEED, ACCEL, FRICTION, TURN_RATE,
    CAR_WIDTH, CAR_LENGTH, SCREEN_WIDTH, SCREEN_HEIGHT, CAR_COLOR
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

        # Speed update
        self.speed += throttle * ACCEL * dt

        # Friction
        if self.speed > 0:
            self.speed -= FRICTION
            if self.speed < 0:
                self.speed = 0
        elif self.speed < 0:
            self.speed += FRICTION
            if self.speed > 0:
                self.speed = 0

        # Clamp
        self.speed = max(-0.5 * MAX_SPEED, min(MAX_SPEED, self.speed))

        # Steering
        self.angle += steer * TURN_RATE * dt

        # Move
        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed
        self.x += dx
        self.y += dy

        # Collision rect
        car_rect = pygame.Rect(0, 0, CAR_WIDTH, CAR_LENGTH)
        car_rect.center = (self.x, self.y)

        # Walls
        for w in track.walls:
            if car_rect.colliderect(w):
                self.alive = False
                return

        # Screen bounds
        if (self.x < 0 or self.x > SCREEN_WIDTH or
                self.y < 0 or self.y > SCREEN_HEIGHT):
            self.alive = False
            return

        # Checkpoints
        if self.checkpoint_index < len(track.checkpoints):
            cx, cy = track.checkpoints[self.checkpoint_index]
            if (self.x - cx) ** 2 + (self.y - cy) ** 2 < (25 ** 2):
                self.checkpoint_index += 1

    def draw(self, surface, color=CAR_COLOR):
        # Draw small triangle pointing in direction of angle
        ang = self.angle
        size = 10
        x, y = self.x, self.y

        p1 = (x + math.cos(ang) * size,
              y + math.sin(ang) * size)
        p2 = (x + math.cos(ang + 2.5) * size * 0.7,
              y + math.sin(ang + 2.5) * size * 0.7)
        p3 = (x + math.cos(ang - 2.5) * size * 0.7,
              y + math.sin(ang - 2.5) * size * 0.7)

        pygame.draw.polygon(surface, color, [p1, p2, p3])
