# main.py

import pygame
import sys

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BASE_GENOME_LEN, GENOME_INC, GENS_PER_INC,
    AUTO_REPLAY, TRACK_DIR
)
from track import load_all_tracks
from genome import random_genome
from ga import evaluate_population, next_generation
from replay_screen import replay_best
from util import save_best_genome, load_best_genome


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Evolutionary AI Racer")
    clock = pygame.time.Clock()

    # ----- Load tracks -----
    tracks = load_all_tracks(TRACK_DIR)
    current_track_idx = 0
    current_track = tracks[current_track_idx]

    # Try load previously saved best
    best_overall_genome = load_best_genome(current_track.name)
    best_overall_fitness = float("-inf")

    genome_len = BASE_GENOME_LEN
    population = [random_genome(genome_len) for _ in range(80)]
    generation = 1
    best_history = []

    while True:
        # ----- Handle events -----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # Switch track with TAB
                if event.key == pygame.K_TAB:
                    current_track_idx = (current_track_idx + 1) % len(tracks)
                    current_track = tracks[current_track_idx]
                    print(f"Switched to track: {current_track.name}")

                    # Reset all evolution stats for the new track
                    genome_len = BASE_GENOME_LEN
                    population = [random_genome(genome_len) for _ in range(80)]
                    generation = 1
                    best_history = []
                    best_overall_genome = load_best_genome(current_track.name)
                    best_overall_fitness = float("-inf")

        # ----- Evaluate population -----
        scored = evaluate_population(population, current_track)
        best_fitness, best_genome = scored[0]

        best_history.append(best_fitness)

        # Track-specific best saving
        if best_fitness > best_overall_fitness:
            best_overall_fitness = best_fitness
            best_overall_genome = best_genome[:]
            save_best_genome(current_track.name, best_overall_genome)

        # ----- Replay best -----
        if AUTO_REPLAY:
            replay_best(
                screen, clock, current_track,
                best_genome, generation, best_fitness,
                genome_len, best_history, auto_continue=True
            )

        # ----- Increase genome length -----
        if generation % GENS_PER_INC == 0:
            genome_len += GENOME_INC
            print(f"Genome length increased to {genome_len}")

        # ----- Next generation -----
        population = next_generation(scored, genome_len)
        generation += 1


if __name__ == "__main__":
    main()
