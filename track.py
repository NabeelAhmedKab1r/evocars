import json
import os
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BACKGROUND_COLOR, DRIVEABLE_COLOR,
    WALL_COLOR, CHECKPOINT_COLOR, START_COLOR
)

# UI layout constants
TOP_BAR_HEIGHT = 60
BOTTOM_BAR_HEIGHT = 45

# Track inset
TRACK_MARGIN = 70       # distance from app border to track edges
WALL_THICKNESS = 22     # thickness of track walls


class Track:
    def __init__(self, name, start_pos, start_angle, walls, checkpoints):
        self.name = name
        self.start_pos = start_pos
        self.start_angle = start_angle
        self.walls = walls
        self.checkpoints = checkpoints

    def draw(self, surface):
        game_y = TOP_BAR_HEIGHT
        game_height = SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT

        # --- Gameplay background area ---
        pygame.draw.rect(
            surface,
            BACKGROUND_COLOR,
            pygame.Rect(0, game_y, SCREEN_WIDTH, game_height)
        )

        # --- Inner driveable rectangle ---
        pygame.draw.rect(
            surface,
            DRIVEABLE_COLOR,
            pygame.Rect(
                TRACK_MARGIN,
                game_y + TRACK_MARGIN,
                SCREEN_WIDTH - 2 * TRACK_MARGIN,
                game_height - 2 * TRACK_MARGIN
            )
        )

        # --- Draw walls ---
        for w in self.walls:
            pygame.draw.rect(surface, WALL_COLOR, w)

        # --- Checkpoints ---
        font = pygame.font.SysFont("Helvetica", 18, bold=True)
        for i, (cx, cy) in enumerate(self.checkpoints):
            pygame.draw.circle(surface, CHECKPOINT_COLOR, (cx, cy), 8)
            label = font.render(str(i + 1), True, (0, 0, 0))
            rect = label.get_rect(center=(cx, cy - 20))
            surface.blit(label, rect)

        # --- Start position marker ---
        pygame.draw.circle(surface, START_COLOR, self.start_pos, 7)


# -------------------------------------------------------------
#                      DEFAULT TRACK (RECTANGLE)
# -------------------------------------------------------------
def default_track():
    walls = []

    # Compute the area where the track exists
    play_top = TOP_BAR_HEIGHT
    play_bottom = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT
    play_height = play_bottom - play_top

    # Track’s inner boundaries
    left = TRACK_MARGIN
    top = play_top + TRACK_MARGIN
    width = SCREEN_WIDTH - 2 * TRACK_MARGIN
    height = play_height - 2 * TRACK_MARGIN

    # -------- WALLS --------
    def wall(x, y, w, h):
        walls.append(pygame.Rect(x, y, w, h))

    # Top wall
    wall(left, top, width, WALL_THICKNESS)

    # Bottom wall
    wall(left, top + height - WALL_THICKNESS, width, WALL_THICKNESS)

    # Left wall
    wall(left, top, WALL_THICKNESS, height)

    # Right wall
    wall(left + width - WALL_THICKNESS, top, WALL_THICKNESS, height)

    # ---------------- CHECKPOINTS (INSIDE TRACK) ----------------
    checkpoints = []

    offset = WALL_THICKNESS + 25  # safe distance inside wall

    # Top checkpoint
    checkpoints.append((
        left + width // 2,
        top + offset
    ))

    # Right checkpoint
    checkpoints.append((
        left + width - offset,
        top + height // 2
    ))

    # Bottom checkpoint
    checkpoints.append((
        left + width // 2,
        top + height - offset
    ))

    # Left checkpoint
    checkpoints.append((
        left + offset,
        top + height // 2
    ))

    # ---------------- START POSITION ----------------
    start_pos = (left + 80, top + height // 2)
    start_angle = 0.0

    return Track(
        "rectangular_track",
        start_pos,
        start_angle,
        walls,
        checkpoints
    )


# -------------------------------------------------------------
#                     LOADER FOR JSON TRACKS
# -------------------------------------------------------------
def load_all_tracks(track_dir):
    if not os.path.isdir(track_dir):
        return [default_track()]

    files = [f for f in os.listdir(track_dir) if f.endswith(".json")]
    tracks = []

    for fname in sorted(files):
        path = os.path.join(track_dir, fname)
        try:
            with open(path, "r") as f:
                data = json.load(f)

            name = data.get("name", os.path.splitext(fname)[0])

            sx, sy = data["start"]
            start = (sx, sy + TOP_BAR_HEIGHT)
            start_angle = float(data.get("start_angle", 0.0))

            walls = [
                pygame.Rect(
                    int(r[0]),
                    int(r[1]) + TOP_BAR_HEIGHT,
                    int(r[2]),
                    int(r[3])
                )
                for r in data["walls"]
            ]

            checkpoints = [
                (cp[0], cp[1] + TOP_BAR_HEIGHT)
                for cp in data["checkpoints"]
            ]

            tracks.append(
                Track(name, start, start_angle, walls, checkpoints)
            )

        except Exception as e:
            print(f"Error loading track {path}: {e}")

    return tracks or [default_track()]
