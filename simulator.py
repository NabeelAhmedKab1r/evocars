# simulator.py

import math
import pygame
import pygame.gfxdraw
from car import Car
from config import (
    DT, REPLAY_FPS, MAX_SPEED, SIM_STEPS,
    NN_INPUTS, NN_HIDDEN, NN_OUTPUTS,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)

# =========================
# UI CONSTANTS
# =========================
TOP_BAR_HEIGHT    = 60
BOTTOM_BAR_HEIGHT = 45

TOP_BAR_BG    = (30, 34, 60)
BOTTOM_BAR_BG = (30, 34, 60)
ACCENT_LINE   = (75, 80, 125)

BEST_CAR_COLOR = (0, 150, 220)    # electric blue
TRAIL_COLOR    = (0, 120, 200)

TEXT_LIGHT  = (235, 238, 255)
TEXT_MUTED  = (170, 175, 210)
TEXT_ACCENT = (50, 240, 155)      # fitness
TEXT_GEN    = (255, 210, 55)      # generation

MAX_TRAIL_LENGTH = 260


# ============================================================
#  NEURAL NETWORK FORWARD PASS
# ============================================================
def nn_forward(genome, inputs):
    """Two-layer tanh net: W1(n_in×n_h), b1(n_h), W2(n_h×n_out), b2(n_out)."""
    n_in, n_h, n_out = NN_INPUTS, NN_HIDDEN, NN_OUTPUTS

    idx = 0
    w1 = genome[idx: idx + n_in * n_h];  idx += n_in * n_h
    b1 = genome[idx: idx + n_h];         idx += n_h
    w2 = genome[idx: idx + n_h * n_out]; idx += n_h * n_out
    b2 = genome[idx: idx + n_out]

    hidden = [
        math.tanh(b1[j] + sum(inputs[i] * w1[i * n_h + j] for i in range(n_in)))
        for j in range(n_h)
    ]
    return [
        math.tanh(b2[j] + sum(hidden[i] * w2[i * n_out + j] for i in range(n_h)))
        for j in range(n_out)
    ]


# ============================================================
#  FULL POPULATION — LIVE SIMULATION + EVALUATION
# ============================================================
GHOST_COLOR      = (30, 100, 190)  # blue, visible on light track
GHOST_COLOR_FAST = (40, 140, 230)  # brighter when moving well
SIM_SPEED_MULT   = 3.0            # run sim at 3× real time (~33 sec/generation)


def _dist_to_next_cp(car, track):
    if car.checkpoint_index >= len(track.checkpoints):
        return 0.0
    tx, ty = track.checkpoints[car.checkpoint_index]
    return math.hypot(car.x - tx, car.y - ty)


def _car_fitness(car, steps_alive, track):
    cp_idx = car.checkpoint_index
    tx, ty = (track.checkpoints[-1] if cp_idx >= len(track.checkpoints)
               else track.checkpoints[cp_idx])
    return cp_idx * 1000.0 - math.hypot(car.x - tx, car.y - ty) + steps_alive * 0.05


def _draw_ghost_car(surface, car):
    color = GHOST_COLOR_FAST if car.speed > 3.0 else GHOST_COLOR
    x, y = int(car.x), int(car.y)
    pygame.gfxdraw.filled_circle(surface, x, y, 3, color)
    pygame.gfxdraw.aacircle(surface, x, y, 3, color)
    # Subtle outline so ghost cars read against dark asphalt
    outline = (color[0], min(255, color[1] + 60), min(255, color[2] + 60))
    pygame.gfxdraw.aacircle(surface, x, y, 4, (*outline, 80))


def simulate_population_visual(screen, clock, track, population, generation, best_history):
    """Evaluate the whole population with live rendering. Returns scored list."""
    n         = len(population)
    cars      = [Car(track.start_pos[0], track.start_pos[1], track.start_angle)
                 for _ in range(n)]
    steps_alive = [0] * n
    trail       = []
    trail_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    font_lg = pygame.font.SysFont("Helvetica", 20, bold=True)
    font_sm = pygame.font.SysFont("Helvetica", 13)
    font_xs = pygame.font.SysFont("Helvetica", 11)

    step      = 0
    time_acc  = 0.0
    skipped   = False
    sim_speed = SIM_SPEED_MULT

    while step < SIM_STEPS:
        dt_real   = clock.tick(REPLAY_FPS) / 1000.0
        time_acc += dt_real * sim_speed

        # ── EVENTS ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit
                if event.key == pygame.K_TAB:
                    pygame.event.post(event)
                    skipped = True
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    sim_speed = min(10.0, round(sim_speed + 0.5, 1))
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    sim_speed = max(0.5, round(sim_speed - 0.5, 1))
                else:
                    skipped = True

        if skipped:
            while step < SIM_STEPS:
                for i, car in enumerate(cars):
                    if car.alive:
                        rays = car.get_raycasts(track)
                        steer, throttle = nn_forward(population[i], rays + [car.speed / MAX_SPEED])
                        car.update(steer, throttle, track, DT)
                        steps_alive[i] += 1
                step += 1
            break

        # ── STEP SIM (time-based, capped to avoid spiral) ───────
        steps_this_frame = 0
        while time_acc >= DT and step < SIM_STEPS and steps_this_frame < 8:
            for i, car in enumerate(cars):
                if car.alive:
                    rays = car.get_raycasts(track)
                    steer, throttle = nn_forward(population[i], rays + [car.speed / MAX_SPEED])
                    car.update(steer, throttle, track, DT)
                    steps_alive[i] += 1
            step += 1
            time_acc -= DT
            steps_this_frame += 1

        # ── FIND BEST LIVING CAR ────────────────────────────────
        alive_indices = [i for i, c in enumerate(cars) if c.alive]
        alive_count   = len(alive_indices)

        best_idx = max(range(n), key=lambda i: (
            cars[i].checkpoint_index, -_dist_to_next_cp(cars[i], track)
        ))
        best_car = cars[best_idx]

        if best_car.alive:
            trail.append((best_car.x, best_car.y))
            if len(trail) > MAX_TRAIL_LENGTH:
                trail.pop(0)

        live_fitness = _car_fitness(best_car, steps_alive[best_idx], track)

        # ── DRAW ────────────────────────────────────────────────
        screen.fill((195, 200, 215))

        # Top bar
        pygame.draw.rect(screen, TOP_BAR_BG,
                         pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(screen, ACCENT_LINE,
                         (0, TOP_BAR_HEIGHT - 1), (SCREEN_WIDTH, TOP_BAR_HEIGHT - 1))

        # Three equal thirds
        third = SCREEN_WIDTH // 3
        div1, div2 = third, third * 2

        # Left third: generation (left-aligned)
        lbl_gen = font_xs.render("GEN", True, TEXT_MUTED)
        val_gen = font_lg.render(str(generation), True, TEXT_GEN)
        screen.blit(lbl_gen, (22, 11))
        screen.blit(val_gen, (22, 22))

        # Dividers
        pygame.draw.line(screen, ACCENT_LINE, (div1, 12), (div1, TOP_BAR_HEIGHT - 13))
        pygame.draw.line(screen, ACCENT_LINE, (div2, 12), (div2, TOP_BAR_HEIGHT - 13))

        # Middle third: best fitness (centred)
        mid     = SCREEN_WIDTH // 2
        lbl_fit = font_xs.render("BEST FITNESS", True, TEXT_MUTED)
        val_fit = font_lg.render(f"{live_fitness:.0f}", True, TEXT_ACCENT)
        screen.blit(lbl_fit, lbl_fit.get_rect(centerx=mid, top=10))
        screen.blit(val_fit, val_fit.get_rect(centerx=mid, top=24))

        # Right third: alive count (right-aligned)
        lbl_alive = font_xs.render("ALIVE", True, TEXT_MUTED)
        val_alive = font_sm.render(f"{alive_count} / {n}", True, TEXT_LIGHT)
        screen.blit(lbl_alive, lbl_alive.get_rect(right=SCREEN_WIDTH - 22, top=11))
        screen.blit(val_alive, val_alive.get_rect(right=SCREEN_WIDTH - 22, top=26))

        _draw_progress_bar(screen, best_car, track)

        # Track
        track.draw(screen, active_checkpoint=best_car.checkpoint_index)

        # Ghost cars
        for i in alive_indices:
            if i != best_idx:
                _draw_ghost_car(screen, cars[i])

        # Best car trail
        if len(trail) >= 2:
            trail_surf.fill((0, 0, 0, 0))
            nt = len(trail)
            for j in range(1, nt):
                frac  = j / nt
                alpha = int(210 * frac)
                w     = 1 + int(2 * frac)
                pygame.draw.line(
                    trail_surf, (*TRAIL_COLOR, alpha),
                    (int(trail[j - 1][0]), int(trail[j - 1][1])),
                    (int(trail[j][0]),     int(trail[j][1])), w
                )
            # Smooth circle caps at each trail point
            for j in range(nt):
                frac  = (j + 1) / nt
                alpha = int(210 * frac)
                r     = max(1, int(1.5 * frac))
                tx, ty = int(trail[j][0]), int(trail[j][1])
                pygame.gfxdraw.filled_circle(trail_surf, tx, ty, r, (*TRAIL_COLOR, alpha))
            screen.blit(trail_surf, (0, 0))

        # Best car
        if best_car.alive:
            best_car.draw_rays(screen, track)
        best_car.draw(screen, BEST_CAR_COLOR)

        # Chart (history from previous generations)
        _draw_chart(screen, best_history, font_xs)

        # Bottom bar
        pygame.draw.rect(screen, BOTTOM_BAR_BG,
                         pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT,
                                     SCREEN_WIDTH, BOTTOM_BAR_HEIGHT))
        pygame.draw.line(screen, ACCENT_LINE,
                         (0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT),
                         (SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT))
        _draw_key_hints(screen, font_xs, sim_speed)

        pygame.display.flip()

        if alive_count == 0:
            pygame.time.delay(400)
            break

    # ── SCORE ALL CARS ──────────────────────────────────────────
    scored = sorted(
        [(_car_fitness(cars[i], steps_alive[i], track), population[i]) for i in range(n)],
        key=lambda x: x[0], reverse=True
    )
    return scored


# ============================================================
#  CHECKPOINT PROGRESS BAR
# ============================================================
def _draw_progress_bar(surface, car, track):
    total = len(track.checkpoints)
    if total == 0:
        return
    progress = car.checkpoint_index / total
    bar_w    = int(progress * SCREEN_WIDTH)
    # Track background rail
    pygame.draw.rect(surface, (60, 65, 95),
                     pygame.Rect(0, TOP_BAR_HEIGHT - 4, SCREEN_WIDTH, 4))
    if bar_w > 0:
        pygame.draw.rect(surface, (0, 210, 120),
                         pygame.Rect(0, TOP_BAR_HEIGHT - 4, bar_w, 4))
        # Bright leading edge
        pygame.draw.rect(surface, (140, 255, 200),
                         pygame.Rect(max(0, bar_w - 2), TOP_BAR_HEIGHT - 4, 2, 4))


# ============================================================
#  FITNESS HISTORY CHART
# ============================================================
def _draw_chart(surface, history, font):
    from config import CHART_WIDTH, CHART_HEIGHT

    pad = 10
    w, h = CHART_WIDTH, CHART_HEIGHT
    x0   = SCREEN_WIDTH  - w  - 12
    y0   = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT - h - 10

    # Panel background (always drawn)
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    bg.fill((215, 220, 235, 220))
    surface.blit(bg, (x0, y0))
    pygame.draw.rect(surface, (150, 155, 185), pygame.Rect(x0, y0, w, h), 1)

    title = font.render("FITNESS", True, (90, 95, 135))
    surface.blit(title, (x0 + w // 2 - title.get_width() // 2, y0 + 2))

    if len(history) < 2:
        msg = font.render("waiting...", True, (140, 145, 175))
        surface.blit(msg, msg.get_rect(centerx=x0 + w // 2, centery=y0 + h // 2))
        return

    lo   = min(history)
    hi   = max(history)
    span = hi - lo if hi != lo else 1
    inner_h = h - 2 * pad - 14   # space below the title row

    def to_pt(i, val):
        px = x0 + pad + int(i / (len(history) - 1) * (w - 2 * pad))
        py = y0 + h - pad - int((val - lo) / span * inner_h)
        return (px, py)

    points = [to_pt(i, v) for i, v in enumerate(history)]

    # Area fill under the line (gradient via polygon + alpha surf)
    fill_pts = ([(x0 + pad, y0 + h - pad)]
                + points
                + [(points[-1][0], y0 + h - pad)])
    local_pts = [(p[0] - x0, p[1] - y0) for p in fill_pts]
    fill_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(fill_surf, (0, 160, 90, 50), local_pts)
    surface.blit(fill_surf, (x0, y0))

    # Line
    pygame.draw.lines(surface, (20, 180, 90), False, points, 2)
    # Endpoint dot
    pygame.draw.circle(surface, (20, 180, 90), points[-1], 3)

    # Labels
    hi_lbl = font.render(f"{hi:.0f}", True, (20, 130, 60))
    lo_lbl = font.render(f"{lo:.0f}", True, (110, 85, 85))
    surface.blit(hi_lbl, (x0 + 3, y0 + 14))
    surface.blit(lo_lbl, (x0 + 3, y0 + h - lo_lbl.get_height() - 3))


# ============================================================
#  KEY HINTS
# ============================================================
def _draw_key_hints(surface, font, sim_speed=SIM_SPEED_MULT):
    hints   = [("TAB", "next track"), ("ESC", "quit"), ("ANY KEY", "skip gen"),
               ("+  /  -", f"speed  {sim_speed:.1f}×")]
    gap     = 22
    rendered = [(font.render(k, True, (220, 224, 245)),
                 font.render(d, True, (145, 150, 190))) for k, d in hints]

    total_w = sum(ks.get_width() + 12 + ds.get_width() for ks, ds in rendered)
    total_w += gap * (len(hints) - 1)
    x  = SCREEN_WIDTH // 2 - total_w // 2
    cy = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT // 2

    for ks, ds in rendered:
        # Key cap badge
        kr    = ks.get_rect(centery=cy, left=x)
        badge = pygame.Rect(kr.left - 5, kr.top - 3, kr.width + 10, kr.height + 6)
        pygame.draw.rect(surface, (32, 36, 65), badge, border_radius=3)
        pygame.draw.rect(surface, (95, 100, 150), badge, 1, border_radius=3)
        surface.blit(ks, kr)
        x += badge.width + 5
        # Description
        dr = ds.get_rect(centery=cy, left=x)
        surface.blit(ds, dr)
        x += ds.get_width() + gap
