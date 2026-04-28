# main.py

import pygame
import sys

from config import SCREEN_WIDTH, SCREEN_HEIGHT, TRACK_DIR
from track import load_all_tracks
from genome import random_genome
from ga import next_generation
from simulator import simulate_population_visual
from util import save_best_genome, load_best_genome


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Evolutionary AI Racer")
    clock = pygame.time.Clock()

    tracks = load_all_tracks(TRACK_DIR)
    current_track_idx = 0
    current_track = tracks[current_track_idx]

    best_overall_genome = load_best_genome(current_track.name)
    best_overall_fitness = float("-inf")

    population = [random_genome() for _ in range(80)]
    generation = 1
    best_history = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_TAB:
                    current_track_idx = (current_track_idx + 1) % len(tracks)
                    current_track = tracks[current_track_idx]
                    print(f"Switched to track: {current_track.name}")

                    population = [random_genome() for _ in range(80)]
                    generation = 1
                    best_history = []
                    best_overall_genome = load_best_genome(current_track.name)
                    best_overall_fitness = float("-inf")

        scored = simulate_population_visual(
            screen, clock, current_track, population, generation, best_history
        )
        best_fitness, best_genome = scored[0]
        best_history.append(best_fitness)

        if best_fitness > best_overall_fitness:
            best_overall_fitness = best_fitness
            best_overall_genome = best_genome[:]
            save_best_genome(current_track.name, best_overall_genome)

        print(f"Gen {generation:4d}  fitness: {best_fitness:.1f}")

        population = next_generation(scored)
        generation += 1


if __name__ == "__main__":
    main()
