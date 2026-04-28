import json
import math
import os
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BACKGROUND_COLOR, DRIVEABLE_COLOR,
    WALL_COLOR, ROAD_EDGE_COLOR, CHECKPOINT_COLOR, START_COLOR
)

# UI layout constants
TOP_BAR_HEIGHT    = 60
BOTTOM_BAR_HEIGHT = 45

# Track inset
TRACK_MARGIN    = 70
WALL_THICKNESS  = 22

_DOT_SPACING = 28
_DOT_COLOR   = (18, 20, 38)   # subtle grid dots in the off-road void


class Track:
    def __init__(self, name, start_pos, start_angle, walls, checkpoints):
        self.name        = name
        self.start_pos   = start_pos
        self.start_angle = start_angle
        self.walls       = walls
        self.checkpoints = checkpoints

    def draw(self, surface, active_checkpoint=None):
        game_y      = TOP_BAR_HEIGHT
        game_height = SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT

        # ── OFF-TRACK VOID ──────────────────────────────────────
        pygame.draw.rect(surface, BACKGROUND_COLOR,
                         pygame.Rect(0, game_y, SCREEN_WIDTH, game_height))

        # Subtle dot grid — only visible in the off-road area since
        # the road rect is drawn on top.
        for gy in range(game_y, game_y + game_height, _DOT_SPACING):
            for gx in range(0, SCREEN_WIDTH, _DOT_SPACING):
                pygame.draw.circle(surface, _DOT_COLOR, (gx, gy), 1)

        # ── ROAD SURFACE ────────────────────────────────────────
        road_rect = pygame.Rect(
            TRACK_MARGIN, game_y + TRACK_MARGIN,
            SCREEN_WIDTH - 2 * TRACK_MARGIN,
            game_height - 2 * TRACK_MARGIN
        )
        pygame.draw.rect(surface, DRIVEABLE_COLOR, road_rect)

        # Subtle road border
        pygame.draw.rect(surface, (55, 58, 90), road_rect, 1)

        # ── WALLS ───────────────────────────────────────────────
        for w in self.walls:
            pygame.draw.rect(surface, WALL_COLOR, w)

        # ── CHECKPOINTS ─────────────────────────────────────────
        t     = pygame.time.get_ticks() / 1000.0
        pulse = 0.5 + 0.5 * math.sin(t * 4.0)   # 0→1 at ~2 Hz
        font  = pygame.font.SysFont("Helvetica", 12, bold=True)

        for i, (cx, cy) in enumerate(self.checkpoints):
            is_active = (active_checkpoint == i)
            is_done   = (active_checkpoint is not None and i < active_checkpoint)

            if is_active:
                # Animated outer glow (radius pulses)
                gr = int(18 + 6 * pulse)
                for r, a in [(gr, int(30 * pulse)), (gr - 6, int(60 * pulse)),
                             (gr - 11, int(100 * pulse))]:
                    gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (0, 240, 180, a), (r, r), r)
                    surface.blit(gs, (cx - r, cy - r))
                # Bright ring + inner dot
                ring_color = (
                    0,
                    int(200 + 40 * pulse),
                    int(160 + 50 * pulse)
                )
                pygame.draw.circle(surface, ring_color, (cx, cy), 12, 2)
                pygame.draw.circle(surface, ring_color, (cx, cy), 3)
                label_color = ring_color

            elif is_done:
                pygame.draw.circle(surface, (45, 65, 55), (cx, cy), 9, 1)
                label_color = (50, 80, 65)

            else:
                pygame.draw.circle(surface, CHECKPOINT_COLOR, (cx, cy), 9, 2)
                label_color = CHECKPOINT_COLOR

            lbl = font.render(str(i + 1), True, label_color)
            surface.blit(lbl, lbl.get_rect(centerx=cx, bottom=cy - 14))

        # ── START MARKER ────────────────────────────────────────
        pygame.draw.circle(surface, START_COLOR, self.start_pos, 5)
        pygame.draw.circle(surface, (160, 255, 200), self.start_pos, 5, 1)


# -------------------------------------------------------------
#                      DEFAULT TRACK
# -------------------------------------------------------------
def default_track():
    walls = []

    play_top    = TOP_BAR_HEIGHT
    play_bottom = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT
    play_height = play_bottom - play_top

    left   = TRACK_MARGIN
    top    = play_top + TRACK_MARGIN
    width  = SCREEN_WIDTH - 2 * TRACK_MARGIN
    height = play_height - 2 * TRACK_MARGIN

    def wall(x, y, w, h):
        walls.append(pygame.Rect(x, y, w, h))

    wall(left, top,                          width,          WALL_THICKNESS)
    wall(left, top + height - WALL_THICKNESS, width,         WALL_THICKNESS)
    wall(left, top,                          WALL_THICKNESS, height)
    wall(left + width - WALL_THICKNESS, top, WALL_THICKNESS, height)

    offset = WALL_THICKNESS + 25
    checkpoints = [
        (left + width  // 2,       top + offset),
        (left + width  - offset,   top + height // 2),
        (left + width  // 2,       top + height - offset),
        (left + offset,            top + height // 2),
    ]

    return Track(
        "rectangular_track",
        (left + 80, top + height // 2),
        0.0,
        walls,
        checkpoints
    )


def load_all_tracks(track_dir):
    if not os.path.isdir(track_dir):
        return [default_track()]

    files  = [f for f in os.listdir(track_dir) if f.endswith(".json")]
    tracks = []

    for fname in sorted(files):
        path = os.path.join(track_dir, fname)
        try:
            with open(path, "r") as f:
                data = json.load(f)

            name        = data.get("name", os.path.splitext(fname)[0])
            sx, sy      = data["start"]
            start       = (sx, sy + TOP_BAR_HEIGHT)
            start_angle = float(data.get("start_angle", 0.0))

            walls = [
                pygame.Rect(int(r[0]), int(r[1]) + TOP_BAR_HEIGHT, int(r[2]), int(r[3]))
                for r in data["walls"]
            ]
            checkpoints = [(cp[0], cp[1] + TOP_BAR_HEIGHT) for cp in data["checkpoints"]]

            tracks.append(Track(name, start, start_angle, walls, checkpoints))

        except Exception as e:
            print(f"Error loading track {path}: {e}")

    return tracks or [default_track()]
