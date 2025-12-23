import pygame
from car import Car
from config import (
    DT, REPLAY_FPS,
    CAR_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT
)

TOP_BAR_HEIGHT = 60
BOTTOM_BAR_HEIGHT = 45
TOP_BAR_BG = (240, 240, 240)
BOTTOM_BAR_BG = (240, 240, 240)


def replay_best(screen, clock, track, best_genome,
                generation, best_fitness, genome_len,
                best_history, auto_continue=True):

    car = Car(track.start_pos[0], track.start_pos[1], track.start_angle)

    font_top = pygame.font.SysFont("Helvetica", 26)
    font_instr = pygame.font.SysFont("Helvetica", 19)

    running = True
    step_index = 0
    time_acc = 0.0

    while running:
        dt_real = clock.tick(REPLAY_FPS) / 1000.0
        time_acc += dt_real

        # -------- HANDLE EVENTS (special TAB fix) --------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit

                # --- SPECIAL FIX ---
                # TAB should switch tracks, not just skip replay.
                if event.key == pygame.K_TAB:
                    pygame.event.post(event)   # send TAB back to main loop
                    running = False            # exit replay
                else:
                    running = False            # any other key skips replay

        # -------- STEP GENOME --------
        while time_acc >= DT and step_index < len(best_genome) and car.alive:
            steer, throttle = best_genome[step_index]
            car.update(steer, throttle, track, DT)
            step_index += 1
            time_acc -= DT

        # -------- DRAW EVERYTHING --------
        screen.fill((255, 255, 255))

        # ---------- TOP BAR ----------
        pygame.draw.rect(screen, TOP_BAR_BG,
                         pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))

        left = font_top.render(f"Generation: {generation}", True, (0, 0, 0))
        right = font_top.render(f"Number of moves: {genome_len}", True, (0, 0, 0))

        screen.blit(left, (20, 15))
        screen.blit(right, (SCREEN_WIDTH - right.get_width() - 20, 15))

        # ---------- TRACK ----------
        track.draw(screen)
        car.draw(screen, CAR_COLOR)

        # ---------- BOTTOM BAR ----------
        pygame.draw.rect(
            screen,
            BOTTOM_BAR_BG,
            pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT,
                        SCREEN_WIDTH, BOTTOM_BAR_HEIGHT)
        )

        controls = "TAB = next track     •     ESC = quit     •     Any key = skip replay"
        surf = font_instr.render(controls, True, (50, 50, 50))
        surf_rect = surf.get_rect(center=(SCREEN_WIDTH // 2,
                                          SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT // 2))
        screen.blit(surf, surf_rect)

        pygame.display.flip()

        # ---------- END REPLAY ----------
        if (step_index >= len(best_genome)) or (not car.alive):
            pygame.time.delay(300)
            if auto_continue:
                running = False
