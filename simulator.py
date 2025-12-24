# simulator.py

import math
import pygame
from car import Car
from config import DT, REPLAY_FPS, CAR_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT

# =========================
# UI CONSTANTS
# =========================
TOP_BAR_HEIGHT = 60
BOTTOM_BAR_HEIGHT = 45

TOP_BAR_BG = (30, 30, 30)
BOTTOM_BAR_BG = (235, 235, 235)

BEST_CAR_COLOR = (0, 180, 0)
TEXT_LIGHT = (240, 240, 240)
TEXT_MUTED = (200, 200, 200)
TEXT_ACCENT = (180, 255, 180)


# ============================================================
#                 FITNESS EVALUATION (NO UI)
# ============================================================
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

        # Allow quitting during long simulations
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

    # Fitness: checkpoints > distance > wasted moves
    fitness = cp_idx * 1000.0 - dist - 0.1 * (len(genome) - steps_alive)
    return fitness, car


# ============================================================
#                 BEST GENOME REPLAY (UI)
# ============================================================
def replay_best(
    screen,
    clock,
    track,
    best_genome,
    generation,
    best_fitness,
    genome_len,
    best_history,
    auto_continue=True
):
    car = Car(track.start_pos[0], track.start_pos[1], track.start_angle)

    font_top = pygame.font.SysFont("Helvetica", 20, bold=True)
    font_instr = pygame.font.SysFont("Helvetica", 16)

    running = True
    step_index = 0
    time_acc = 0.0

    while running:
        dt_real = clock.tick(REPLAY_FPS) / 1000.0
        time_acc += dt_real

        # ---------------- EVENTS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit

                # TAB switches track (forwarded to main loop)
                if event.key == pygame.K_TAB:
                    pygame.event.post(event)
                    running = False
                else:
                    running = False

        # ---------------- STEP GENOME ----------------
        while time_acc >= DT and step_index < len(best_genome) and car.alive:
            steer, throttle = best_genome[step_index]
            car.update(steer, throttle, track, DT)
            step_index += 1
            time_acc -= DT

        # ---------------- DRAW ----------------
        screen.fill((245, 245, 245))

        # ===== TOP BAR =====
        pygame.draw.rect(
            screen,
            TOP_BAR_BG,
            pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT)
        )

        gen_text = font_top.render(
            f"Generation {generation}", True, TEXT_LIGHT
        )
        fit_text = font_top.render(
            f"Best fitness: {best_fitness:.1f}", True, TEXT_ACCENT
        )
        move_text = font_top.render(
            f"Moves: {genome_len}", True, TEXT_MUTED
        )

        screen.blit(gen_text, (20, 18))
        screen.blit(
            fit_text,
            (SCREEN_WIDTH // 2 - fit_text.get_width() // 2, 18)
        )
        screen.blit(
            move_text,
            (SCREEN_WIDTH - move_text.get_width() - 20, 18)
        )

        # ===== TRACK + BEST AGENT =====
        track.draw(screen)
        car.draw(screen, BEST_CAR_COLOR)

        # ===== BOTTOM BAR =====
        pygame.draw.rect(
            screen,
            BOTTOM_BAR_BG,
            pygame.Rect(
                0,
                SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT,
                SCREEN_WIDTH,
                BOTTOM_BAR_HEIGHT
            )
        )

        controls = "TAB = next track   •   ESC = quit   •   Any key = skip replay"
        surf = font_instr.render(controls, True, (60, 60, 60))
        surf_rect = surf.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT // 2
            )
        )
        screen.blit(surf, surf_rect)

        pygame.display.flip()

        # ---------------- END REPLAY ----------------
        if step_index >= len(best_genome) or not car.alive:
            pygame.time.delay(250)
            if auto_continue:
                running = False
