# simulator.py

import math
import pygame
from car import Car
from config import DT


def simulate_genome(genome, track):
    """
    Run a single genome on a track (no drawing).
    Returns (fitness, final_car_state).
    """
    car = Car(track.start_pos[0], track.start_pos[1], track.start_angle)
    steps_alive = 0

    for (steer, throttle) in genome:
        if not car.alive:
            break

        car.update(steer, throttle, track, DT)
        steps_alive += 1

        # allow quitting during heavy sims
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

    cp_idx = car.checkpoint_index

    if cp_idx >= len(track.checkpoints):
        target_x, target_y = track.checkpoints[-1]
    else:
        target_x, target_y = track.checkpoints[cp_idx]

    dist = math.hypot(car.x - target_x, car.y - target_y)

    # Fitness: more checkpoints, closer to next one, fewer wasted steps
    fitness = cp_idx * 1000.0 - dist - 0.1 * (len(genome) - steps_alive)
    return fitness, car
