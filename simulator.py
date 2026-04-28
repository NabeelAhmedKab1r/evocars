# simulator.py

import math
import pygame
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

TOP_BAR_BG    = (9, 10, 20)
BOTTOM_BAR_BG = (9, 10, 20)
ACCENT_LINE   = (45, 48, 75)

BEST_CAR_COLOR = (0, 200, 255)    # electric cyan
TRAIL_COLOR    = (0, 160, 210)

TEXT_LIGHT  = (215, 220, 235)
TEXT_MUTED  = (90, 95, 130)
TEXT_ACCENT = (60, 240, 160)      # fitness
TEXT_GEN    = (255, 200, 60)      # generation

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
#  FITNESS EVALUATION  (headless)
# ============================================================
def simulate_genome(genome, track):
    car = Car(track.start_pos[0], track.start_pos[1], track.start_angle)
    steps_alive = 0

    for _ in range(SIM_STEPS):
        if not car.alive:
            break
        rays       = car.get_raycasts(track)
        speed_norm = car.speed / MAX_SPEED
        steer, throttle = nn_forward(genome, rays + [speed_norm])
        car.update(steer, throttle, track, DT)
        steps_alive += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

    cp_idx = car.checkpoint_index
    tx, ty = (track.checkpoints[-1] if cp_idx >= len(track.checkpoints)
               else track.checkpoints[cp_idx])
    dist    = math.hypot(car.x - tx, car.y - ty)
    fitness = cp_idx * 1000.0 - dist + steps_alive * 0.05
    return fitness, car


# ============================================================
#  FULL POPULATION — LIVE SIMULATION + EVALUATION
# ============================================================
GHOST_COLOR      = (0, 55, 80)    # dim cyan for non-best alive cars
GHOST_COLOR_FAST = (0, 90, 120)   # slightly brighter when moving well
STEPS_PER_FRAME  = 5              # sim steps rendered per display frame


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
    ang  = car.angle
    size = 7
    p1 = (car.x + math.cos(ang) * size,             car.y + math.sin(ang) * size)
    p2 = (car.x + math.cos(ang + 2.5) * size * 0.65, car.y + math.sin(ang + 2.5) * size * 0.65)
    p3 = (car.x + math.cos(ang - 2.5) * size * 0.65, car.y + math.sin(ang - 2.5) * size * 0.65)
    color = GHOST_COLOR_FAST if car.speed > 3.0 else GHOST_COLOR
    pygame.draw.polygon(surface, color, [p1, p2, p3])


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

    step    = 0
    skipped = False

    while step < SIM_STEPS:
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
                else:
                    skipped = True

        if skipped:
            # Finish headlessly so fitness is still accurate
            while step < SIM_STEPS:
                for i, car in enumerate(cars):
                    if car.alive:
                        rays = car.get_raycasts(track)
                        steer, throttle = nn_forward(population[i], rays + [car.speed / MAX_SPEED])
                        car.update(steer, throttle, track, DT)
                        steps_alive[i] += 1
                step += 1
            break

        # ── STEP SIM ────────────────────────────────────────────
        for _ in range(STEPS_PER_FRAME):
            if step >= SIM_STEPS:
                break
            for i, car in enumerate(cars):
                if car.alive:
                    rays = car.get_raycasts(track)
                    steer, throttle = nn_forward(population[i], rays + [car.speed / MAX_SPEED])
                    car.update(steer, throttle, track, DT)
                    steps_alive[i] += 1
            step += 1

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
        screen.fill((7, 8, 18))

        # Top bar
        pygame.draw.rect(screen, TOP_BAR_BG,
                         pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(screen, ACCENT_LINE,
                         (0, TOP_BAR_HEIGHT - 1), (SCREEN_WIDTH, TOP_BAR_HEIGHT - 1))

        lbl_gen = font_xs.render("GEN", True, TEXT_MUTED)
        val_gen = font_lg.render(str(generation), True, TEXT_GEN)
        screen.blit(lbl_gen, (22, 13))
        screen.blit(val_gen, (22 + lbl_gen.get_width() + 5, 9))

        mid     = SCREEN_WIDTH // 2
        lbl_fit = font_xs.render("BEST FITNESS", True, TEXT_MUTED)
        val_fit = font_lg.render(f"{live_fitness:.0f}", True, TEXT_ACCENT)
        screen.blit(lbl_fit, lbl_fit.get_rect(centerx=mid, top=10))
        screen.blit(val_fit, val_fit.get_rect(centerx=mid, top=26))

        lbl_alive = font_xs.render("ALIVE", True, TEXT_MUTED)
        val_alive = font_sm.render(f"{alive_count} / {n}", True, TEXT_LIGHT)
        screen.blit(lbl_alive, lbl_alive.get_rect(right=SCREEN_WIDTH - 20, top=13))
        screen.blit(val_alive, val_alive.get_rect(right=SCREEN_WIDTH - 20, top=30))

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
        _draw_key_hints(screen, font_xs)

        pygame.display.flip()
        clock.tick(REPLAY_FPS)

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
#  BEST GENOME REPLAY
# ============================================================
def replay_best(
    screen, clock, track,
    best_genome, generation, best_fitness,
    best_history, auto_continue=True
):
    car = Car(track.start_pos[0], track.start_pos[1], track.start_angle)

    font_lg  = pygame.font.SysFont("Helvetica", 20, bold=True)
    font_sm  = pygame.font.SysFont("Helvetica", 13)
    font_xs  = pygame.font.SysFont("Helvetica", 11)

    # Pre-build trail surface once (reused, cleared each frame)
    trail_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    running    = True
    step_index = 0
    time_acc   = 0.0
    trail      = []

    while running:
        dt_real   = clock.tick(REPLAY_FPS) / 1000.0
        time_acc += dt_real

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
                    running = False
                else:
                    running = False

        # ── STEP ────────────────────────────────────────────────
        while time_acc >= DT and step_index < SIM_STEPS and car.alive:
            rays       = car.get_raycasts(track)
            speed_norm = car.speed / MAX_SPEED
            steer, throttle = nn_forward(best_genome, rays + [speed_norm])
            car.update(steer, throttle, track, DT)
            step_index += 1
            time_acc   -= DT
            trail.append((car.x, car.y))
            if len(trail) > MAX_TRAIL_LENGTH:
                trail.pop(0)

        # ── DRAW: background fill ────────────────────────────────
        screen.fill((7, 8, 18))

        # ── TOP BAR ─────────────────────────────────────────────
        pygame.draw.rect(screen, TOP_BAR_BG,
                         pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(screen, ACCENT_LINE,
                         (0, TOP_BAR_HEIGHT - 1), (SCREEN_WIDTH, TOP_BAR_HEIGHT - 1))

        # Left: GEN label + big number
        lbl_gen = font_xs.render("GEN", True, TEXT_MUTED)
        val_gen = font_lg.render(str(generation), True, TEXT_GEN)
        screen.blit(lbl_gen, (22, 13))
        screen.blit(val_gen, (22 + lbl_gen.get_width() + 5, 9))

        # Centre: BEST FITNESS
        lbl_fit = font_xs.render("BEST FITNESS", True, TEXT_MUTED)
        val_fit = font_lg.render(f"{best_fitness:.0f}", True, TEXT_ACCENT)
        mid = SCREEN_WIDTH // 2
        screen.blit(lbl_fit, lbl_fit.get_rect(centerx=mid, top=10))
        screen.blit(val_fit, val_fit.get_rect(centerx=mid, top=26))

        # Right: TRACK
        trk_display = track.name.replace("_", " ").title()
        lbl_trk = font_xs.render("TRACK", True, TEXT_MUTED)
        val_trk = font_sm.render(trk_display, True, TEXT_LIGHT)
        screen.blit(lbl_trk, lbl_trk.get_rect(right=SCREEN_WIDTH - 20, top=13))
        screen.blit(val_trk, val_trk.get_rect(right=SCREEN_WIDTH - 20, top=30))

        # Thin checkpoint progress bar along the bottom of the top bar
        _draw_progress_bar(screen, car, track)

        # ── TRACK ───────────────────────────────────────────────
        track.draw(screen, active_checkpoint=car.checkpoint_index)

        # ── GRADIENT TRAIL ──────────────────────────────────────
        if len(trail) >= 2:
            trail_surf.fill((0, 0, 0, 0))
            n = len(trail)
            for j in range(1, n):
                frac  = j / n
                alpha = int(210 * frac)
                width = 1 + int(2 * frac)
                pygame.draw.line(
                    trail_surf,
                    (*TRAIL_COLOR, alpha),
                    (int(trail[j - 1][0]), int(trail[j - 1][1])),
                    (int(trail[j][0]),     int(trail[j][1])),
                    width
                )
            screen.blit(trail_surf, (0, 0))

        # ── RAYS + CAR ──────────────────────────────────────────
        if car.alive:
            car.draw_rays(screen, track)
        car.draw(screen, BEST_CAR_COLOR)

        # ── CHART ───────────────────────────────────────────────
        _draw_chart(screen, best_history, font_xs)

        # ── BOTTOM BAR ──────────────────────────────────────────
        pygame.draw.rect(
            screen, BOTTOM_BAR_BG,
            pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT,
                        SCREEN_WIDTH, BOTTOM_BAR_HEIGHT)
        )
        pygame.draw.line(screen, ACCENT_LINE,
                         (0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT),
                         (SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT))
        _draw_key_hints(screen, font_xs)

        pygame.display.flip()

        # ── END REPLAY ──────────────────────────────────────────
        if step_index >= SIM_STEPS or not car.alive:
            pygame.time.delay(300)
            if auto_continue:
                running = False


# ============================================================
#  CHECKPOINT PROGRESS BAR
# ============================================================
def _draw_progress_bar(surface, car, track):
    total = len(track.checkpoints)
    if total == 0:
        return
    progress = car.checkpoint_index / total
    bar_w    = int(progress * SCREEN_WIDTH)
    if bar_w > 0:
        pygame.draw.rect(surface, (0, 200, 120),
                         pygame.Rect(0, TOP_BAR_HEIGHT - 3, bar_w, 3))


# ============================================================
#  FITNESS HISTORY CHART
# ============================================================
def _draw_chart(surface, history, font):
    from config import CHART_WIDTH, CHART_HEIGHT

    if len(history) < 2:
        return

    pad = 10
    w, h = CHART_WIDTH, CHART_HEIGHT
    x0   = SCREEN_WIDTH  - w  - 12
    y0   = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT - h - 10

    # Panel background
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    bg.fill((6, 8, 18, 210))
    surface.blit(bg, (x0, y0))
    pygame.draw.rect(surface, (40, 44, 72), pygame.Rect(x0, y0, w, h), 1)

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
    pygame.draw.polygon(fill_surf, (0, 180, 100, 35), local_pts)
    surface.blit(fill_surf, (x0, y0))

    # Line
    pygame.draw.lines(surface, (50, 210, 110), False, points, 2)
    # Endpoint dot
    pygame.draw.circle(surface, (50, 210, 110), points[-1], 3)

    # Labels
    title  = font.render("FITNESS", True, (70, 75, 110))
    hi_lbl = font.render(f"{hi:.0f}", True, (70, 140, 80))
    lo_lbl = font.render(f"{lo:.0f}", True, (70, 75, 100))
    surface.blit(title,  (x0 + w // 2 - title.get_width() // 2, y0 + 2))
    surface.blit(hi_lbl, (x0 + 3, y0 + 14))
    surface.blit(lo_lbl, (x0 + 3, y0 + h - lo_lbl.get_height() - 3))


# ============================================================
#  KEY HINTS
# ============================================================
def _draw_key_hints(surface, font):
    hints   = [("TAB", "next track"), ("ESC", "quit"), ("ANY KEY", "skip")]
    gap     = 22
    rendered = [(font.render(k, True, (190, 195, 220)),
                 font.render(d, True, (75, 78, 115))) for k, d in hints]

    total_w = sum(ks.get_width() + 12 + ds.get_width() for ks, ds in rendered)
    total_w += gap * (len(hints) - 1)
    x  = SCREEN_WIDTH // 2 - total_w // 2
    cy = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT // 2

    for ks, ds in rendered:
        # Key cap badge
        kr    = ks.get_rect(centery=cy, left=x)
        badge = pygame.Rect(kr.left - 5, kr.top - 3, kr.width + 10, kr.height + 6)
        pygame.draw.rect(surface, (28, 30, 52), badge, border_radius=3)
        pygame.draw.rect(surface, (60, 65, 100), badge, 1, border_radius=3)
        surface.blit(ks, kr)
        x += badge.width + 5
        # Description
        dr = ds.get_rect(centery=cy, left=x)
        surface.blit(ds, dr)
        x += ds.get_width() + gap
